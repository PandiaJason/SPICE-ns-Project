#!/usr/bin/env python3
"""
=============================================================================
  PREDICTIVE TEMPORAL BRIDGE (PTB) — MARS CABIN TERMINAL
  Mission: Ares-3 Mars Orbital Insertion
  Run alongside earth_command.py (start both via launch.sh)
=============================================================================
  Layout (curses):
    Panel A  – Earth AI prediction arriving now (Earth said: t+m)
    Panel B  – Cabin AI local sensors (true t)
    Panel C  – Cabin AI proposed action (reconciled decision)
    Panel D  – Dual trajectory: Earth prediction vs. Cabin AI live track
=============================================================================
"""

import curses
import time
import math
import json
import os
import sys
from datetime import datetime, timezone
from collections import deque

# ─── Shared-state paths (same as Earth script) ─────────────────────────────
SHARED_DIR     = os.path.join(os.path.dirname(__file__), "shared_state")
EARTH_TX_FILE  = os.path.join(SHARED_DIR, "earth_to_mars.json")
MARS_TX_FILE   = os.path.join(SHARED_DIR, "mars_to_earth.json")
os.makedirs(SHARED_DIR, exist_ok=True)

# ─── Constants (must mirror earth_command.py) ──────────────────────────────
LIGHT_DELAY_INITIAL = 60.0
LIGHT_DELAY_GROW    = 2.0
LIGHT_DELAY_MAX     = 480.0
SIM_SPEED           = 1.0
ANOMALY_TRIGGER_T   = 90
CORRECTION_APPLIED_T = 999.0   # set when commander executes fix

# ─── Telemetry functions (same physics as Earth side) ─────────────────────
def compute_delay(t_sim: float) -> float:
    return min(LIGHT_DELAY_INITIAL + (t_sim / 60.0) * LIGHT_DELAY_GROW, LIGHT_DELAY_MAX)

def nominal_telemetry(t: float) -> dict:
    return {
        "t": t,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "range_km":            55_000_000 - t * 450.0,
        "velocity_ms":         20_500.0   - t * 0.12,
        "attitude_deg":        -3.14 * math.sin(t / 400.0),
        "gimbal_port_C":       78.0 + 0.04 * t + 3.0 * math.sin(t / 30.0),
        "gimbal_stbd_C":       76.0 + 0.02 * t + 1.5 * math.cos(t / 45.0),
        "thrust_pct":          98.5 - 0.01 * t,
        "traj_deviation_pct":  0.0,
        "hull_pressure_psi":   14.7,
        "power_kw":            42.3,
        "anomaly":             False,
        "anomaly_type":        None,
    }

def inject_anomaly(base: dict, t: float, correction_applied: bool) -> dict:
    dt = t - ANOMALY_TRIGGER_T
    # After correction, anomaly decays
    if correction_applied:
        dt2 = t - CORRECTION_APPLIED_T
        decay = math.exp(-dt2 / 15.0)
    else:
        decay = 1.0

    base["gimbal_port_C"]      += 12.0 * (1 - math.exp(-dt / 20.0)) * decay
    base["thrust_pct"]         -= 3.2  * (1 - math.exp(-dt / 25.0)) * decay
    base["traj_deviation_pct"] += 0.04 * (1 - math.exp(-dt / 30.0)) * decay
    base["anomaly"]             = (decay > 0.05)
    base["anomaly_type"]        = "PORT_GIMBAL_SEAL_DEGRADATION" if decay > 0.05 else None
    return base

def get_cabin_telemetry(t_sim: float, correction_applied: bool) -> dict:
    """True sensor readings at current Mars time t_sim."""
    tel = nominal_telemetry(t_sim)
    if t_sim >= ANOMALY_TRIGGER_T:
        tel = inject_anomaly(tel, t_sim, correction_applied)
    return tel

def read_earth_command() -> dict | None:
    """Non-blocking read of the Earth command packet."""
    try:
        with open(EARTH_TX_FILE) as f:
            return json.load(f)
    except Exception:
        return None

# ─── Reconciliation engine ─────────────────────────────────────────────────
def reconcile(cabin_tel: dict, earth_pkg: dict | None) -> dict:
    """Cabin AI compares Earth prediction vs. actual sensor truth."""
    if earth_pkg is None:
        return {
            "status": "NO_EARTH_SIGNAL",
            "earth_cmd_type": None,
            "deltas": {},
            "cabin_recommendation": "Awaiting Earth signal. Local auto-control active.",
            "safe_to_execute": False,
        }

    pred  = earth_pkg.get("predicted", {})
    cmd   = earth_pkg.get("command",   {})

    # Compute deltas
    deltas = {}
    for key in ("gimbal_port_C", "thrust_pct", "traj_deviation_pct", "velocity_ms"):
        if key in pred and key in cabin_tel:
            deltas[key] = cabin_tel[key] - pred[key]

    max_delta_pct = max(abs(v) for v in deltas.values()) if deltas else 0.0
    safe = max_delta_pct < 0.5   # threshold: <0.5 unit delta is safe to follow

    # Build Cabin AI recommendation
    if cmd.get("type") == "CORRECTION":
        if safe:
            rec = f"Earth correction VALIDATED. Delta={max_delta_pct:.3f}. Ready to execute."
        else:
            rec = f"⚠ DELTA HIGH ({max_delta_pct:.3f}). Earth model diverged! Override recommended."
    else:
        rec = "Systems nominal. Earth concurs."

    return {
        "status": "RECONCILED" if safe else "DELTA_HIGH",
        "earth_cmd_type": cmd.get("type"),
        "deltas": deltas,
        "cabin_recommendation": rec,
        "safe_to_execute": safe,
        "earth_command": cmd,
    }

# ─── Panel renderers ───────────────────────────────────────────────────────
def render_panel_a(win, earth_pkg: dict | None, t_sim: float):
    """Panel A – Earth AI message arriving now."""
    win.erase(); win.box()
    win.addstr(0, 2, " PANEL A: EARTH PREDICTION (arriving now) ", curses.color_pair(6) | curses.A_BOLD)
    if earth_pkg is None:
        win.addstr(2, 2, "No signal from Earth yet.", curses.color_pair(4))
        return
    pred = earth_pkg.get("predicted", {})
    m    = earth_pkg.get("m", 0)
    rows = [
        ("Earth packet issued",     f"{earth_pkg.get('t_issued',0):>9.1f} s"),
        ("Prediction horizon",      f"t+2m = +{2*m:.0f}s"),
        ("Port Gimbal (predicted)", f"{pred.get('gimbal_port_C',0):>9.1f} °C"),
        ("Thrust (predicted)",      f"{pred.get('thrust_pct',0):>9.2f} %"),
        ("Traj Dev (predicted)",    f"{pred.get('traj_deviation_pct',0):>+9.4f} %"),
        ("Anomaly in prediction",   "YES ⚠" if pred.get("anomaly") else "NO ✓"),
    ]
    cmd = earth_pkg.get("command", {})
    for i, (label, val) in enumerate(rows, start=2):
        col = curses.color_pair(1) if "⚠" in val else curses.color_pair(6)
        try:
            win.addstr(i, 2, f"{label:<28} {val}", col)
        except curses.error:
            pass
    if cmd.get("type") == "CORRECTION":
        try:
            win.addstr(len(rows)+3, 2, "EARTH COMMAND:", curses.color_pair(1)|curses.A_BOLD)
            for j, det in enumerate(cmd.get("details",[]), start=len(rows)+4):
                win.addstr(j, 4, f"• {det}", curses.color_pair(5))
        except curses.error:
            pass

def render_panel_b(win, cabin_tel: dict, t_sim: float):
    """Panel B – Cabin AI live sensor data (true t)."""
    win.erase(); win.box()
    win.addstr(0, 2, " PANEL B: CABIN AI — LOCAL SENSORS (true t) ", curses.color_pair(2) | curses.A_BOLD)
    rows = [
        ("Mission clock (now)",     f"{t_sim:>9.1f} s"),
        ("Range from Earth",        f"{cabin_tel.get('range_km',0)/1e6:>9.3f} M km"),
        ("Velocity",                f"{cabin_tel.get('velocity_ms',0):>9.1f} m/s"),
        ("Attitude",                f"{cabin_tel.get('attitude_deg',0):>+9.3f}°"),
        ("Port Gimbal Temp",        f"{cabin_tel.get('gimbal_port_C',0):>9.1f} °C"),
        ("Stbd Gimbal Temp",        f"{cabin_tel.get('gimbal_stbd_C',0):>9.1f} °C"),
        ("Thrust",                  f"{cabin_tel.get('thrust_pct',0):>9.2f} %"),
        ("Traj Deviation",          f"{cabin_tel.get('traj_deviation_pct',0):>+9.4f} %"),
        ("Hull Pressure",           f"{cabin_tel.get('hull_pressure_psi',0):>9.2f} PSI"),
        ("Power",                   f"{cabin_tel.get('power_kw',0):>9.2f} kW"),
    ]
    for i, (label, val) in enumerate(rows, start=2):
        hot = ("Gimbal" in label and cabin_tel.get("gimbal_port_C", 0) > 85)
        col = curses.color_pair(1) if (cabin_tel.get("anomaly") and hot) else curses.color_pair(3)
        try:
            win.addstr(i, 2, f"{label:<28} {val}", col)
        except curses.error:
            pass
    if cabin_tel.get("anomaly"):
        try:
            win.addstr(len(rows)+3, 2, f"⚠ LOCAL ANOMALY: {cabin_tel.get('anomaly_type')}", curses.color_pair(1)|curses.A_BOLD|curses.A_BLINK)
        except curses.error:
            pass

def render_panel_c(win, recon: dict, correction_done: bool):
    """Panel C – Cabin AI reconciled decision + Commander interface."""
    win.erase(); win.box()
    status_col = curses.color_pair(3) if recon["status"] in ("RECONCILED","NO_EARTH_SIGNAL") else curses.color_pair(1)
    win.addstr(0, 2, " PANEL C: CABIN AI RECONCILIATION & COMMAND ", status_col | curses.A_BOLD)
    try:
        win.addstr(2, 2, f"Status       : {recon['status']}", status_col | curses.A_BOLD)
        win.addstr(3, 2, f"Earth cmd    : {recon.get('earth_cmd_type','—')}", curses.color_pair(4))
        win.addstr(5, 2, "Δ Deltas (Cabin truth − Earth prediction):", curses.color_pair(5))
        for i, (key, val) in enumerate(recon.get("deltas", {}).items(), start=6):
            col = curses.color_pair(1) if abs(val) > 0.3 else curses.color_pair(3)
            win.addstr(i, 4, f"  {key:<26} Δ={val:>+8.4f}", col)
        rec_y = 6 + len(recon.get("deltas", {})) + 1
        win.addstr(rec_y, 2, "Cabin AI:", curses.color_pair(5) | curses.A_BOLD)
        win.addstr(rec_y+1, 4, recon["cabin_recommendation"], curses.color_pair(3))
        if recon.get("safe_to_execute") and not correction_done:
            win.addstr(rec_y+3, 2, "[ Press SPACE ] Commander executes correction", curses.color_pair(5) | curses.A_REVERSE | curses.A_BOLD)
        elif correction_done:
            win.addstr(rec_y+3, 2, "✓ CORRECTION EXECUTED — Monitoring recovery...", curses.color_pair(3) | curses.A_BOLD)
    except curses.error:
        pass

def draw_trajectory_dual(win, cabin_hist, earth_hist, h, w, correction_t):
    win.erase(); win.box()
    win.addstr(0, 2, " TRAJECTORY: ◆ Cabin (truth) | ○ Earth prediction | ✕ Correction", curses.color_pair(5)|curses.A_BOLD)
    plot_h = h - 4
    plot_w = w - 6
    if plot_h < 4 or plot_w < 8:
        return
    all_devs = [d for _, d in cabin_hist] + [d for _, d in earth_hist]
    max_dev  = max(0.05, max(abs(v) for v in all_devs)) if all_devs else 0.05
    mid_y    = 2 + plot_h // 2

    def to_y(dev):
        return mid_y - int((dev / max_dev) * (plot_h // 2))

    for x in range(4, w - 2):
        try:
            win.addch(mid_y, x, ord('─'), curses.color_pair(4))
        except curses.error:
            pass

    for i, (tv, dev) in enumerate(cabin_hist):
        x = 4 + int(i * (plot_w / max(1, len(cabin_hist)-1)))
        y = to_y(dev)
        if 2 <= y < h-2 and 4 <= x < w-2:
            try:
                win.addch(y, x, ord('◆'), curses.color_pair(3)|curses.A_BOLD)
            except curses.error:
                pass

    for i, (tv, dev) in enumerate(earth_hist):
        x = 4 + int(i * (plot_w / max(1, len(earth_hist)-1)))
        y = to_y(dev)
        if 2 <= y < h-2 and 4 <= x < w-2:
            try:
                win.addch(y, x, ord('o'), curses.color_pair(6)|curses.A_BOLD)
            except curses.error:
                pass

    win.addstr(h-2, 4, f" max_dev={max_dev:.4f}%  correction={'APPLIED' if correction_t<9999 else 'NONE'} ", curses.color_pair(4))

# ─── Cabin transcript ───────────────────────────────────────────────────────
_cabin_log: list[str] = []
_last_cabin_t = -999.0

def build_cabin_transcript(t_sim, cabin_tel, recon, correction_done):
    global _last_cabin_t
    lines = _cabin_log
    if t_sim - _last_cabin_t >= 5.0:
        _last_cabin_t = t_sim
        ts = f"[t={t_sim:06.1f}s]"
        if not cabin_tel.get("anomaly"):
            lines.append(f"{ts} Cabin AI: All systems nominal. Insertion profile on track.")
        else:
            lines.append(f"{ts} Cabin AI: ⚠ LOCAL ANOMALY — {cabin_tel.get('anomaly_type')}")
            lines.append(f"{ts}   Port Gimbal: {cabin_tel.get('gimbal_port_C',0):.1f}°C  Thrust: {cabin_tel.get('thrust_pct',0):.2f}%")
            if recon["status"] == "RECONCILED" and recon.get("earth_cmd_type") == "CORRECTION":
                lines.append(f"{ts} Capt. Chen: Earth prediction matches local truth. Execute fix?")
            elif recon["status"] == "DELTA_HIGH":
                lines.append(f"{ts} Cabin AI: DELTA HIGH — Earth model diverged. Local override!")
        if correction_done:
            lines.append(f"{ts} ✓ Commander: CORRECTION EXECUTED. RCS firing. Monitoring recovery.")
    return lines[-30:]

# ─── Main loop ─────────────────────────────────────────────────────────────
def main(stdscr):
    global CORRECTION_APPLIED_T

    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED,     -1)
    curses.init_pair(2, curses.COLOR_CYAN,    -1)
    curses.init_pair(3, curses.COLOR_GREEN,   -1)
    curses.init_pair(4, curses.COLOR_WHITE,   -1)
    curses.init_pair(5, curses.COLOR_YELLOW,  -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)

    cabin_hist  = deque(maxlen=60)
    earth_hist  = deque(maxlen=60)
    correction_done = False

    t_sim   = 0.0
    tick_dt = 0.5

    while True:
        sh, sw = stdscr.getmaxyx()
        m = compute_delay(t_sim)

        # Live cabin sensors
        cabin_tel = get_cabin_telemetry(t_sim, correction_done)

        # Earth command (arrived m seconds ago — simulate by reading shared file)
        earth_pkg = read_earth_command()

        # Cabin AI reconciliation
        recon = reconcile(cabin_tel, earth_pkg)

        # Publish Mars telemetry to shared file for Earth to read
        try:
            with open(MARS_TX_FILE, "w") as f:
                json.dump(cabin_tel, f)
        except Exception:
            pass

        # Track history
        cabin_hist.append((t_sim, cabin_tel.get("traj_deviation_pct", 0)))
        if earth_pkg:
            pred = earth_pkg.get("predicted", {})
            earth_hist.append((t_sim, pred.get("traj_deviation_pct", 0)))

        # ── Draw ─────────────────────────────────────────────────────────
        try:
            stdscr.erase()
            panel_w = sw // 3
            top_h   = sh * 4 // 10
            mid_h   = sh * 3 // 10
            traj_h  = sh - top_h - mid_h - 3

            header = f" 🚀 MARS CABIN (ARES-3) — PTB TERMINAL  |  sim_t={t_sim:.1f}s  |  delay={m:.0f}s ({m/60:.1f}min)  |  {datetime.now().strftime('%H:%M:%S')} "
            stdscr.attron(curses.color_pair(2) | curses.A_BOLD | curses.A_REVERSE)
            stdscr.addstr(0, 0, header.center(sw)[:sw])
            stdscr.attroff(curses.color_pair(2) | curses.A_BOLD | curses.A_REVERSE)

            win_a = curses.newwin(top_h, panel_w,           1, 0)
            win_b = curses.newwin(top_h, panel_w,           1, panel_w)
            win_c = curses.newwin(top_h, sw - 2 * panel_w,  1, 2 * panel_w)

            render_panel_a(win_a, earth_pkg, t_sim)
            render_panel_b(win_b, cabin_tel, t_sim)
            render_panel_c(win_c, recon, correction_done)

            win_a.noutrefresh(); win_b.noutrefresh(); win_c.noutrefresh()

            log_y = 1 + top_h
            win_log = curses.newwin(mid_h, sw, log_y, 0)
            win_log.box()
            win_log.addstr(0, 2, " COMMANDER CHEN — MISSION TRANSCRIPT ", curses.color_pair(5)|curses.A_BOLD)
            lines = build_cabin_transcript(t_sim, cabin_tel, recon, correction_done)
            for li, line in enumerate(lines[-(mid_h-2):], start=1):
                col = curses.color_pair(1) if "⚠" in line or "ANOMALY" in line else curses.color_pair(3)
                try:
                    win_log.addstr(li, 2, line[:sw-4], col)
                except curses.error:
                    pass
            win_log.noutrefresh()

            if traj_h > 4:
                win_traj = curses.newwin(traj_h, sw, log_y + mid_h, 0)
                draw_trajectory_dual(win_traj, list(cabin_hist), list(earth_hist), traj_h, sw, CORRECTION_APPLIED_T)
                win_traj.noutrefresh()

            curses.doupdate()
        except curses.error:
            pass

        # ── Input ─────────────────────────────────────────────────────────
        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break
        if key == ord(' ') and recon.get("safe_to_execute") and not correction_done:
            correction_done    = True
            CORRECTION_APPLIED_T = t_sim
            _cabin_log.append(f"[t={t_sim:06.1f}s] ✓ Commander Chen: EXECUTING Earth correction command NOW.")

        t_sim += tick_dt
        time.sleep(tick_dt * SIM_SPEED)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\n[Mars Cabin Terminal] Simulation ended.")
