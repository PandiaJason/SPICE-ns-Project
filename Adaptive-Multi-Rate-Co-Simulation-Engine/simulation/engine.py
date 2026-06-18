"""
engine.py  –  Adaptive Multi-Rate Co-Simulation Engine
=======================================================
Components:
  ContinuousEngine   – ODE solver (scipy solve_ivp) for orbital mechanics
  DiscreteEngine     – Discrete-event network simulator (native Python)
  CoSimOrchestrator  – Couples both engines under three execution strategies:
                         1. FixedStep  – uniform dt = 1 s
                         2. EventDriven – step only on network events
                         3. Adaptive  – predictive look-ahead step sizing
"""

import time, math
import numpy as np
from scipy.integrate import solve_ivp

C_LIGHT = 299_792_458.0   # m/s


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Continuous Engine
# ─────────────────────────────────────────────────────────────────────────────
class ContinuousEngine:
    """Two-body ODE propagator.  State = [x, y, vx, vy]."""

    def __init__(self, mu: float, rtol: float = 1e-9, atol: float = 1e-9):
        self.mu   = mu
        self.rtol = rtol
        self.atol = atol

    def _eom(self, t, s):
        x, y, vx, vy = s
        r3 = (x*x + y*y) ** 1.5
        ax = -self.mu * x / r3
        ay = -self.mu * y / r3
        return [vx, vy, ax, ay]

    def propagate(self, state0: np.ndarray, t0: float, t1: float) -> np.ndarray:
        """Integrate from t0 to t1, return final state [x,y,vx,vy]."""
        if abs(t1 - t0) < 1e-12:
            return state0.copy()
        sol = solve_ivp(self._eom, [t0, t1], state0,
                        method="DOP853", rtol=self.rtol, atol=self.atol,
                        dense_output=False)
        return sol.y[:, -1]

    def propagate_grid(self, state0: np.ndarray, t_grid: np.ndarray) -> np.ndarray:
        """Integrate over a fixed time grid; return (4 x N) state matrix."""
        sol = solve_ivp(self._eom, [t_grid[0], t_grid[-1]], state0,
                        method="DOP853", rtol=self.rtol, atol=self.atol,
                        t_eval=t_grid, dense_output=False)
        return sol.y                    # shape (4, N)


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Discrete-Event Network Engine
# ─────────────────────────────────────────────────────────────────────────────
class Packet:
    __slots__ = ("size_bytes", "t_created", "t_sent", "t_received", "dropped")

    def __init__(self, size_bytes: int, t_created: float):
        self.size_bytes = size_bytes
        self.t_created  = t_created
        self.t_sent     = None
        self.t_received = None
        self.dropped    = False


class DiscreteEngine:
    """
    Lightweight packet-level network simulator.
    Tracks queue depth, bit-rate, propagation delay, custody transfers.
    """

    def __init__(self, cfg: dict):
        self.bitrate        = cfg.get("bitrate_nominal", 2_000_000)     # bps
        self.bitrate_min    = cfg.get("bitrate_min", 1_000)
        self.bitrate_max    = cfg.get("bitrate_max", self.bitrate)
        self.mtu            = cfg.get("mtu_bytes", 1024)
        self.buf_cap        = cfg.get("buffer_bytes", 50_000_000)
        self.protocol       = cfg.get("protocol", "CCSDS/SLE")
        self.prop_delay     = 0.0                                        # s (updated externally)
        self._queue         : list[Packet] = []
        self._buf_used      = 0                                          # bytes
        self.events         : list[dict]   = []                         # log
        self.custody_count  = 0
        self.drops          = 0
        self.pkts_sent      = 0

    # ── Internal helpers ──────────────────────────────────────────────────────
    def _enqueue(self, pkt: Packet, now: float):
        if self._buf_used + pkt.size_bytes > self.buf_cap:
            pkt.dropped = True
            self.drops += 1
            self.events.append({"t": now, "type": "drop",
                                 "buf_used": self._buf_used})
        else:
            self._queue.append(pkt)
            self._buf_used += pkt.size_bytes

    def _flush(self, now: float, link_up: bool):
        """Transmit as many packets as the current bitrate allows in this slot."""
        if not link_up or not self._queue:
            return
        bytes_budget = self.bitrate * 1.0 / 8   # bytes per second (normalised)
        sent = []
        for pkt in self._queue:
            if bytes_budget <= 0:
                break
            tx_time = pkt.size_bytes * 8 / self.bitrate
            pkt.t_sent     = now
            pkt.t_received = now + tx_time + self.prop_delay
            bytes_budget  -= pkt.size_bytes
            self._buf_used -= pkt.size_bytes
            self.pkts_sent += 1
            sent.append(pkt)
        for p in sent:
            self._queue.remove(p)

    # ── Public API ────────────────────────────────────────────────────────────
    def inject_traffic(self, n_pkts: int, now: float):
        for _ in range(n_pkts):
            self._enqueue(Packet(self.mtu, now), now)

    def step(self, now: float, link_up: bool, snr_dB: float = 30.0,
             dist_m: float = 1.0e9):
        """Advance network state by one time slice."""
        self.prop_delay = dist_m / C_LIGHT
        # Adapt bitrate from SNR (Shannon log approximation)
        if snr_dB > -200:                         # valid SNR
            snr_lin = 10 ** (snr_dB / 10.0)
            new_br  = min(self.bitrate_max,
                          max(self.bitrate_min,
                              self.bitrate_max * math.log2(1 + snr_lin) / 40.0))
            if abs(new_br - self.bitrate) / max(self.bitrate, 1) > 0.05:
                self.events.append({"t": now, "type": "bitrate_change",
                                    "old_bps": self.bitrate, "new_bps": new_br})
                self.bitrate = new_br
        self._flush(now, link_up)
        # Custody transfer bookkeeping (DTN)
        if "DTN" in self.protocol and not link_up and self._buf_used > 1e6:
            self.custody_count += 1
            self.events.append({"t": now, "type": "custody",
                                 "buf_used": self._buf_used})

    def buf_bytes(self) -> float:
        return self._buf_used

    def reset(self):
        self._queue.clear(); self._buf_used = 0
        self.events.clear(); self.drops = 0
        self.pkts_sent = 0; self.custody_count = 0


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Co-Simulation Orchestrator
# ─────────────────────────────────────────────────────────────────────────────
class SimResult:
    """Container for metrics from a single run."""
    def __init__(self):
        self.wall_time_s   = 0.0
        self.steps         = 0
        self.pos_error_m   = 0.0     # cumulative |Δr| vs. reference
        self.event_error_ms= 0.0     # timestamp error at critical events
        self.dt_sequence   = []      # [(t, dt), ...]
        self.buf_sequence  = []      # [(t, buf_bytes), ...]
        self.speedup       = 1.0     # vs. fixed-step baseline
        self.pos_err_seq   = []      # [(t, pos_err_m), ...]  – per-step errors
        self.cum_err_seq   = []      # [(t, cum_err_m), ...]  – running cumulative


class CoSimOrchestrator:
    """
    Couples ContinuousEngine and DiscreteEngine under three strategies.
    All strategies share the same reference truth arrays for error computation.
    """

    # ── dt look-ahead constants ───────────────────────────────────────────────
    DT_MIN   = 1.0        # 1 s   – active handover / ingress-egress boundary
    DT_NOM   = 30.0       # 30 s  – nominal active link
    DT_COAST = 600.0      # 10 min – quiet cruise
    DT_BLACKOUT = 3600.0  # 1 h   – total blackout (physics still coasts)

    # Traffic injection: 1 packet per dt step
    PKT_RATE = 1

    def __init__(self, profile: dict, ref_t: np.ndarray, ref_x: np.ndarray,
                 ref_y: np.ndarray):
        mu  = profile["constants"].get("mu_mars",
              profile["constants"].get("mu_earth",
              profile["constants"].get("mu_moon", 3.986e14)))
        self.cont = ContinuousEngine(mu)
        self.net  = DiscreteEngine(profile["network"])
        gt        = profile["ground_truth"]
        self.gt_t = np.array(gt["t_s"])
        self.gt_x = np.array(gt["x_m"])
        self.gt_y = np.array(gt["y_m"])
        self.gt_los = np.array(gt.get("los", gt.get("contact", np.ones(len(gt["t_s"])))))
        self.gt_snr = np.array(gt.get("snr_dB", 30*np.ones(len(gt["t_s"]))))
        self.t_end  = profile["simulation"]["t_span_s"]
        self.ref_t  = ref_t
        self.ref_x  = ref_x
        self.ref_y  = ref_y
        # Critical events (occultation ingress/egress or custody)
        evlist = gt.get("events", gt.get("custody", []))
        self.crit_times = np.array([ev["time_s"] for ev in evlist]) if evlist else np.array([])

    # ── Interpolation helpers ─────────────────────────────────────────────────
    def _interp_los(self, t: float) -> int:
        return int(np.interp(t, self.gt_t, self.gt_los))

    def _interp_snr(self, t: float) -> float:
        return float(np.interp(t, self.gt_t, self.gt_snr))

    def _ref_pos(self, t: float):
        rx = float(np.interp(t, self.ref_t, self.ref_x))
        ry = float(np.interp(t, self.ref_t, self.ref_y))
        return rx, ry

    def _adaptive_dt(self, t: float, state: np.ndarray) -> float:
        """Predictive look-ahead step selector.
        Contracts dt near critical events; expands during cruise or blackout.
        The key novelty: proximity window only triggers when t IS NEAR an event,
        not globally whenever future events exist.
        """
        if self.crit_times.size > 0:
            dists      = np.abs(self.crit_times - t)
            dt_nearest = float(np.min(dists))   # seconds to nearest event
            if dt_nearest < 60.0:
                return self.DT_MIN              # 1 ms – active ingress/egress
            if dt_nearest < 600.0:
                return min(self.DT_NOM, dt_nearest / 10.0)  # graduated ramp

        los = self._interp_los(t)
        snr = self._interp_snr(t)

        if los == 0:
            return self.DT_BLACKOUT             # 1 h coast during blackout
        if snr < 5.0:
            return self.DT_NOM                  # degraded link — 1 s steps
        t_fut   = min(t + 120.0, self.t_end - 1.0)
        snr_fut = float(np.interp(t_fut, self.gt_t, self.gt_snr))
        if abs(snr_fut - snr) > 5.0:
            return self.DT_NOM                  # rapid SNR gradient
        return self.DT_COAST                    # stable cruise — 10 min steps

    # ── Run strategies ────────────────────────────────────────────────────────
    def _run(self, strategy: str, n_nodes: int = 1) -> SimResult:
        res  = SimResult()
        self.net.reset()
        state = np.array([self.gt_x[0], self.gt_y[0],
                          0.0, np.sqrt(
                              (float(np.interp(0, self.gt_t,
                                     np.sqrt(self.gt_x**2+self.gt_y**2))))**(-1)
                              )])
        # Better initial velocity from vis-viva (approximate)
        r0 = math.sqrt(state[0]**2 + state[1]**2)
        v0 = math.sqrt(self.cont.mu / r0)
        state[3] = v0   # tangential velocity along y for circular approx

        t    = 0.0
        cum_pos_err = 0.0
        cum_evt_err = 0.0
        dt_seq      = []
        buf_seq     = []
        pos_err_seq = []
        cum_err_seq = []
        steps       = 0

        # Discrete-event baseline: collect network events from truth for stepping
        net_event_times = self.gt_t[np.diff(self.gt_los, prepend=self.gt_los[0]) != 0]

        t0_wall = time.perf_counter()

        while t < self.t_end:
            # ── Determine dt ──────────────────────────────────────────────
            if strategy == "fixed":  # 60 s uniform cadence
                dt = 60.0
            elif strategy == "event":
                future = net_event_times[net_event_times > t]
                dt = float(future[0] - t) if future.size else min(300.0, self.t_end-t)
                dt = max(dt, 0.001)
            else:  # adaptive
                dt = self._adaptive_dt(t, state)

            dt = min(dt, self.t_end - t)
            if dt <= 0:
                break

            # ── Propagate physics ─────────────────────────────────────────
            state = self.cont.propagate(state, t, t + dt)
            sim_r = math.sqrt(state[0]**2 + state[1]**2)

            # ── Network step (scaled by n_nodes) ──────────────────────────
            los = self._interp_los(t + dt)
            snr = self._interp_snr(t + dt)
            dist = sim_r  # simplified: range to ground
            self.net.inject_traffic(self.PKT_RATE * n_nodes, t + dt)
            self.net.step(t + dt, bool(los), snr, dist)

            # ── Metrics ───────────────────────────────────────────────────
            rx, ry = self._ref_pos(t + dt)
            pos_err = math.sqrt((state[0]-rx)**2 + (state[1]-ry)**2)
            cum_pos_err += pos_err

            dt_seq.append((t, dt))
            buf_seq.append((t + dt, self.net.buf_bytes()))
            pos_err_seq.append((t + dt, pos_err))
            cum_err_seq.append((t + dt, cum_pos_err))
            t += dt
            steps += 1

        # Event timestamp error
        for ev_net in self.net.events:
            if ev_net["type"] in ("drop","bitrate_change","custody") \
                    and self.crit_times.size > 0:
                nearest = float(np.min(np.abs(self.crit_times - ev_net["t"])))
                cum_evt_err += nearest * 1000   # s → ms

        res.wall_time_s    = time.perf_counter() - t0_wall
        res.steps          = steps
        res.pos_error_m    = cum_pos_err
        res.event_error_ms = cum_evt_err / max(1, len(self.net.events))
        res.dt_sequence    = dt_seq
        res.buf_sequence   = buf_seq
        res.pos_err_seq    = pos_err_seq
        res.cum_err_seq    = cum_err_seq
        return res

    def run_fixed(self, n_nodes=1):    return self._run("fixed",   n_nodes)
    def run_event(self, n_nodes=1):    return self._run("event",   n_nodes)
    def run_adaptive(self, n_nodes=1): return self._run("adaptive", n_nodes)
