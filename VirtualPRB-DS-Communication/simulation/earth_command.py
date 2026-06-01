#!/usr/bin/env python3
"""
=============================================================================
  PREDICTIVE TEMPORAL BRIDGE (PTB) — EARTH COMMAND CENTER TERMINAL
  Mission: Ares-3 Mars Orbital Insertion  |  One-Way Light Delay: m seconds
  Run alongside mars_cabin.py (start both simultaneously via launch.sh)
=============================================================================
  Layout (curses):
    Panel A  – Raw telemetry received from Mars (data sent at t-m)
    Panel B  – Earth AI Forward Projection to t+m
    Panel C  – Earth Command being transmitted to Mars
    Panel D  – Trajectory plot (ASCII): actual telemetry vs. AI prediction
=============================================================================
"""

import curses
import time
import math
import json
import os
import sys
import random
from datetime import datetime, timezone
from collections import deque

# ─── Shared-state file (both scripts read/write) ───────────────────────────
SHARED_DIR = os.path.join(os.path.dirname(__file__), "shared_state")
EARTH_TX_FILE  = os.path.join(SHARED_DIR, "earth_to_mars.json")
MARS_TX_FILE   = os.path.join(SHARED_DIR, "mars_to_earth.json")

os.makedirs(SHARED_DIR, exist_ok=True)

# ─── Mission constants ──────────────────────────────────────────────────────
LIGHT_DELAY_INITIAL = 60.0          # seconds one-way at mission start (sim)
LIGHT_DELAY_GROW    = 2.0           # seconds added per sim-minute (grows over time)
LIGHT_DELAY_MAX     = 480.0         # cap at 8 minutes (realistic mid-approach)
SIM_SPEED           = 1.0           # wall-clock seconds per sim-second
ANOMALY_TRIGGER_T   = 90            # sim-seconds when anomaly fires

# ─── Telemetry helpers ──────────────────────────────────────────────────────
def compute_delay(t_sim: float) -> float:
    raw = LIGHT_DELAY_INITIAL + (t_sim / 60.0) * LIGHT_DELAY_GROW
    return min(raw, LIGHT_DELAY_MAX)

def nominal_telemetry(t: float) -> dict:
    """Nominal spacecraft state at mission-clock t (seconds)."""
    return {
        "t": t,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "range_km":        55_000_000 - t * 450.0,
        "velocity_ms":     20_500.0  - t * 0.12,
        "attitude_deg":    -3.14 * math.sin(t / 400.0),
        "gimbal_port_C":   78.0 + 0.04 * t + 3.0 * math.sin(t / 30.0),
        "gimbal_stbd_C":   76.0 + 0.02 * t + 1.5 * math.cos(t / 45.0),
        "thrust_pct":      98.5 - 0.01 * t,
        "traj_deviation_pct": 0.0,
        "hull_pressure_psi":  14.7,
        "power_kw":        42.3,
        "anomaly":         False,
        "anomaly_type":    None,
    }

def inject_anomaly(base: dict, t: float) -> dict:
    """After ANOMALY_TRIGGER_T: gimbal seal degrades → thrust asymmetry."""
    dt = t - ANOMALY_TRIGGER_T
    base["gimbal_port_C"]      += 12.0 * (1 - math.exp(-dt / 20.0))
    base["thrust_pct"]         -= 3.2  * (1 - math.exp(-dt / 25.0))
    base["traj_deviation_pct"] += 0.04 * (1 - math.exp(-dt / 30.0))
    base["anomaly"]             = True
    base["anomaly_type"]        = "PORT_GIMBAL_SEAL_DEGRADATION"
    return base

def get_mars_telemetry(t_sim: float) -> dict:
    """Try to read the shared file; fall back to synthetic data."""
    try:
        with open(MARS_TX_FILE) as f:
            data = json.load(f)
        return data
    except Exception:
        tel = nominal_telemetry(t_sim)
        if t_sim >= ANOMALY_TRIGGER_T:
            tel = inject_anomaly(tel, t_sim)
        return tel

def earth_ai_predict(recv_tel: dict, m: float) -> dict:
    """Project received state (t_recv) forward by 2m to get t+m."""
    t_base    = recv_tel.get("t", 0)
    t_predict = t_base + 2 * m
    predicted = nominal_telemetry(t_predict)

    # If anomaly was flagged in received data, extrapolate degradation
    if recv_tel.get("anomaly"):
        dt = t_predict - ANOMALY_TRIGGER_T
        predicted["gimbal_port_C"]      += 10.0 * (1 - math.exp(-dt / 20.0))
        predicted["thrust_pct"]         -= 3.0  * (1 - math.exp(-dt / 25.0))
        predicted["traj_deviation_pct"] += 0.035 * (1 - math.exp(-dt / 30.0))
        predicted["anomaly"] = True
        predicted["anomaly_type"] = recv_tel.get("anomaly_type")

    predicted["t"] = t_predict
    return predicted

def generate_command(predicted: dict, m: float) -> dict:
    """Earth Flight Director generates a correction command."""
    cmd: dict = {"type": "NOMINAL", "description": "No action required.", "details": []}
    if predicted.get("anomaly"):
        tdev = predicted.get("traj_deviation_pct", 0)
        gtemp = predicted.get("gimbal_port_C", 0)
        cmd = {
            "type": "CORRECTION",
            "intercept_t": predicted["t"],
            "description": "Anomaly predicted at t+2m. Execute correction on receipt.",
            "details": [
                f"THROTTLE: Reduce main engine to 92%",
                f"RCS: +0.4s starboard pulses every 10s",
                f"GIMBAL: Cool port side; expected temp {gtemp:.1f}°C",
                f"TRAJECTORY: Compensate +{tdev:.3f}% deviation",
            ],
        }
    return cmd

# ─── ASCII trajectory plot ──────────────────────────────────────────────────
def draw_trajectory_panel(win, traj_history, pred_history, h, w):
    win.erase()
    win.box()
    win.addstr(0, 2, " TRAJECTORY (◆ actual | ○ AI prediction) ", curses.color_pair(5) | curses.A_BOLD)

    plot_h = h - 4
    plot_w = w - 6
    if plot_h < 4 or plot_w < 8:
        return

    # Normalize deviation to y-axis (0 = nominal centre)
    all_devs = [d for _, d in traj_history] + [d for _, d in pred_history]
    max_dev  = max(0.05, max(abs(v) for v in all_devs)) if all_devs else 0.05
    mid_y    = 2 + plot_h // 2

    def dev_to_y(dev):
        return mid_y - int((dev / max_dev) * (plot_h // 2))

    # Centre line
    for x in range(4, w - 2):
        try:
            win.addch(mid_y, x, ord('─'), curses.color_pair(4))
        except curses.error:
            pass

    # Plot actual
    for i, (t_val, dev) in enumerate(traj_history):
        x = 4 + int(i * (plot_w / max(1, len(traj_history) - 1)))
        y = dev_to_y(dev)
        if 2 <= y < h - 2 and 4 <= x < w - 2:
            try:
                win.addch(y, x, ord('◆'), curses.color_pair(3) | curses.A_BOLD)
            except curses.error:
                pass

    # Plot prediction
    for i, (t_val, dev) in enumerate(pred_history):
        x = 4 + int(i * (plot_w / max(1, len(pred_history) - 1)))
        y = dev_to_y(dev)
        if 2 <= y < h - 2 and 4 <= x < w - 2:
            try:
                win.addch(y, x, ord('○'), curses.color_pair(6) | curses.A_BOLD)
            except curses.error:
                pass

    legend_y = h - 2
    win.addstr(legend_y, 4, f" max_dev={max_dev:.4f}%  points={len(traj_history)} ", curses.color_pair(4))

# ─── Panel renderers ────────────────────────────────────────────────────────
def render_panel_a(win, tel: dict, m: float, t_sim: float):
    """Panel A – Raw telemetry received (sent at t-m)."""
    win.erase(); win.box()
    win.addstr(0, 2, " PANEL A: MARS RAW TELEMETRY (sent at t−m) ", curses.color_pair(2) | curses.A_BOLD)
    t_sent = tel.get("t", 0)
    rows = [
        ("Mission clock (data sent)", f"{t_sent:>9.1f} s"),
        ("Current sim clock",         f"{t_sim:>9.1f} s"),
        ("One-way light delay (m)",   f"{m:>9.1f} s  ({m/60:.2f} min)"),
        ("Range from Earth",          f"{tel.get('range_km',0)/1e6:>9.3f} M km"),
        ("Velocity",                  f"{tel.get('velocity_ms',0):>9.1f} m/s"),
        ("Attitude",                  f"{tel.get('attitude_deg',0):>+9.3f}°"),
        ("Port Gimbal Temp",          f"{tel.get('gimbal_port_C',0):>9.1f} °C"),
        ("Stbd Gimbal Temp",          f"{tel.get('gimbal_stbd_C',0):>9.1f} °C"),
        ("Thrust",                    f"{tel.get('thrust_pct',0):>9.2f} %"),
        ("Traj Deviation",            f"{tel.get('traj_deviation_pct',0):>+9.4f} %"),
        ("Hull Pressure",             f"{tel.get('hull_pressure_psi',0):>9.2f} PSI"),
        ("Power",                     f"{tel.get('power_kw',0):>9.2f} kW"),
    ]
    for i, (label, val) in enumerate(rows, start=2):
        anom_col = curses.color_pair(1) if tel.get("anomaly") and "Gimbal" in label else curses.color_pair(3)
        try:
            win.addstr(i, 2, f"{label:<28} {val}", anom_col)
        except curses.error:
            pass
    if tel.get("anomaly"):
        try:
            win.addstr(len(rows) + 3, 2, f"⚠ ANOMALY: {tel.get('anomaly_type')}", curses.color_pair(1) | curses.A_BOLD | curses.A_BLINK)
        except curses.error:
            pass

def render_panel_b(win, predicted: dict, m: float):
    """Panel B – Earth AI prediction at t+m."""
    win.erase(); win.box()
    win.addstr(0, 2, " PANEL B: EARTH AI PREDICTION → t+2m ", curses.color_pair(6) | curses.A_BOLD)
    t_pred = predicted.get("t", 0)
    rows = [
        ("Predicted mission clock", f"{t_pred:>9.1f} s"),
        ("Projection horizon",      f"t + 2m = +{2*m:.0f} s"),
        ("Range (projected)",       f"{predicted.get('range_km',0)/1e6:>9.3f} M km"),
        ("Velocity (projected)",    f"{predicted.get('velocity_ms',0):>9.1f} m/s"),
        ("Attitude (projected)",    f"{predicted.get('attitude_deg',0):>+9.3f}°"),
        ("Port Gimbal (projected)", f"{predicted.get('gimbal_port_C',0):>9.1f} °C"),
        ("Thrust (projected)",      f"{predicted.get('thrust_pct',0):>9.2f} %"),
        ("Traj Dev (projected)",    f"{predicted.get('traj_deviation_pct',0):>+9.4f} %"),
        ("Anomaly predicted?",      "YES ⚠" if predicted.get("anomaly") else "NO ✓"),
    ]
    for i, (label, val) in enumerate(rows, start=2):
        col = curses.color_pair(1) if ("Anomaly" in label and predicted.get("anomaly")) else curses.color_pair(6)
        try:
            win.addstr(i, 2, f"{label:<28} {val}", col)
        except curses.error:
            pass

def render_panel_c(win, cmd: dict, m: float):
    """Panel C – Earth command being transmitted."""
    win.erase(); win.box()
    col = curses.color_pair(1) if cmd["type"] == "CORRECTION" else curses.color_pair(3)
    win.addstr(0, 2, " PANEL C: EARTH COMMAND → TRANSMITTING ", col | curses.A_BOLD)
    try:
        win.addstr(2, 2, f"Command type : {cmd['type']}", col | curses.A_BOLD)
        win.addstr(3, 2, f"Description  : {cmd['description']}", curses.color_pair(3))
        if "intercept_t" in cmd:
            win.addstr(4, 2, f"Intercept at : t = {cmd['intercept_t']:.1f} s (Mars time)", curses.color_pair(5))
        win.addstr(5, 2, f"Signal delay : {m:.1f} s one-way", curses.color_pair(4))
        for j, det in enumerate(cmd.get("details", []), start=7):
            win.addstr(j, 4, f"• {det}", curses.color_pair(3))
    except curses.error:
        pass

# ─── Main curses loop ───────────────────────────────────────────────────────
def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED,     -1)   # alert
    curses.init_pair(2, curses.COLOR_CYAN,    -1)   # panel A
    curses.init_pair(3, curses.COLOR_GREEN,   -1)   # nominal
    curses.init_pair(4, curses.COLOR_WHITE,   -1)   # info
    curses.init_pair(5, curses.COLOR_YELLOW,  -1)   # highlight
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)   # AI prediction

    traj_actual = deque(maxlen=60)
    traj_pred   = deque(maxlen=60)

    t_sim   = 0.0
    tick_dt = 0.5           # update every 0.5 wall-clock seconds

    while True:
        sh, sw = stdscr.getmaxyx()

        # ── Layout math ────────────────────────────────────────────────────
        half_w   = sw // 2
        top_h    = sh * 4 // 10
        mid_h    = sh * 3 // 10
        traj_h   = sh - top_h - mid_h - 3   # bottom strip

        # ── Compute current delay ─────────────────────────────────────────
        m = compute_delay(t_sim)

        # ── Get (simulated) Mars telemetry that arrived at Earth ──────────
        recv_tel = get_mars_telemetry(t_sim - m if t_sim > m else 0)

        # ── Earth AI projects forward ─────────────────────────────────────
        predicted = earth_ai_predict(recv_tel, m)
        cmd       = generate_command(predicted, m)

        # ── Write Earth command to shared file (Mars will read it) ────────
        try:
            with open(EARTH_TX_FILE, "w") as f:
                payload = {"t_issued": t_sim, "m": m, "command": cmd, "predicted": predicted}
                json.dump(payload, f)
        except Exception:
            pass

        # ── Record trajectory history ─────────────────────────────────────
        traj_actual.append((t_sim, recv_tel.get("traj_deviation_pct", 0)))
        traj_pred.append((t_sim, predicted.get("traj_deviation_pct", 0)))

        # ── Draw windows ─────────────────────────────────────────────────
        try:
            # Header
            stdscr.erase()
            header = f" 🌍 EARTH COMMAND CENTER — PTB SIMULATION  |  sim_t={t_sim:.1f}s  |  delay={m:.0f}s ({m/60:.1f}min)  |  {datetime.now().strftime('%H:%M:%S')} "
            stdscr.attron(curses.color_pair(5) | curses.A_BOLD | curses.A_REVERSE)
            stdscr.addstr(0, 0, header.center(sw)[:sw])
            stdscr.attroff(curses.color_pair(5) | curses.A_BOLD | curses.A_REVERSE)

            # Three top panels
            panel_w = sw // 3
            win_a = curses.newwin(top_h, panel_w,           1, 0)
            win_b = curses.newwin(top_h, panel_w,           1, panel_w)
            win_c = curses.newwin(top_h, sw - 2 * panel_w,  1, 2 * panel_w)

            render_panel_a(win_a, recv_tel, m, t_sim)
            render_panel_b(win_b, predicted, m)
            render_panel_c(win_c, cmd, m)

            win_a.noutrefresh(); win_b.noutrefresh(); win_c.noutrefresh()

            # Transcript log strip
            log_y = 1 + top_h
            win_log = curses.newwin(mid_h, sw, log_y, 0)
            win_log.box()
            win_log.addstr(0, 2, " FLIGHT DIRECTOR TRANSCRIPT ", curses.color_pair(5) | curses.A_BOLD)
            log_lines = build_transcript(t_sim, m, recv_tel, predicted, cmd)
            for li, line in enumerate(log_lines[-(mid_h - 2):], start=1):
                col = curses.color_pair(1) if "⚠" in line else curses.color_pair(3)
                try:
                    win_log.addstr(li, 2, line[:sw-4], col)
                except curses.error:
                    pass
            win_log.noutrefresh()

            # Trajectory panel
            traj_y = log_y + mid_h
            if traj_h > 4:
                win_traj = curses.newwin(traj_h, sw, traj_y, 0)
                draw_trajectory_panel(win_traj, list(traj_actual), list(traj_pred), traj_h, sw)
                win_traj.noutrefresh()

            curses.doupdate()
        except curses.error:
            pass

        # ── Input handling ────────────────────────────────────────────────
        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break

        t_sim += tick_dt
        time.sleep(tick_dt * SIM_SPEED)

# ─── Live transcript builder ────────────────────────────────────────────────
_transcript_log: list[str] = []
_last_t = -999.0

def build_transcript(t_sim, m, tel, predicted, cmd):
    global _last_t
    lines = _transcript_log

    if t_sim - _last_t >= 5.0:
        _last_t = t_sim
        ts = f"[t={t_sim:06.1f}s]"
        if not tel.get("anomaly"):
            lines.append(f"{ts} Earth AI: All systems nominal. Projection to t+{2*m:.0f}s complete.")
        else:
            lines.append(f"{ts} ⚠ Earth AI: ANOMALY detected — {tel.get('anomaly_type')}!")
            lines.append(f"{ts}    Port Gimbal projected {predicted.get('gimbal_port_C',0):.1f}°C at t+{2*m:.0f}s.")
            lines.append(f"{ts}    Thrust asymmetry: {100-predicted.get('thrust_pct',100):.2f}% deficiency predicted.")
            lines.append(f"{ts}    Traj deviation projected: {predicted.get('traj_deviation_pct',0):+.4f}%")
            if cmd["type"] == "CORRECTION":
                lines.append(f"{ts} FLIGHT: Correction command compiled. Transmitting now.")
                lines.append(f"{ts}    → {cmd['details'][0]}")
                lines.append(f"{ts}    → {cmd['details'][1]}")
                lines.append(f"{ts}    Will intercept Mars at t={cmd.get('intercept_t',0):.1f}s")

    return lines[-30:]   # keep last 30 lines


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\n[Earth Terminal] Simulation ended.")
