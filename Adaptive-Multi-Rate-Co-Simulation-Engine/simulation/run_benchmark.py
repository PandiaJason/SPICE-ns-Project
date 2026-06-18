"""
run_benchmark.py  –  Execute all simulations, collect metrics, save CSV.
Fixed-step baseline uses dt=60s (mission-planning resolution).
Usage:  python3 simulation/run_benchmark.py
"""

import json, os, sys
import numpy as np
import pandas as pd

ROOT     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
OUT_DIR  = os.path.join(ROOT, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

sys.path.insert(0, ROOT)
from engine import CoSimOrchestrator

PROFILES = [
    ("mars_occultation_profile.json",   "Mars"),
    ("elliptical_doppler_profile.json", "Elliptical"),
    ("cislunar_nrho_profile.json",      "Cislunar"),
]

def load(name):
    with open(os.path.join(DATA_DIR, name)) as f:
        return json.load(f)

def build_ref(profile):
    gt = profile["ground_truth"]
    return (np.array(gt["t_s"]), np.array(gt["x_m"]), np.array(gt["y_m"]))


def run_all():
    rows        = []
    all_results = {}
    all_profs   = {}

    for fname, label in PROFILES:
        print(f"\n{'='*55}\n  Profile: {label}\n{'='*55}")
        prof = load(fname)
        all_profs[label]   = prof
        ref_t, ref_x, ref_y = build_ref(prof)
        orch = CoSimOrchestrator(prof, ref_t, ref_x, ref_y)

        results = {}
        for strat, runner in [("Fixed",       orch.run_fixed),
                               ("EventDriven", orch.run_event),
                               ("Adaptive",    orch.run_adaptive)]:
            print(f"  Running {strat} … ", end="", flush=True)
            res = runner()
            results[strat] = res
            print(f"done  ({res.wall_time_s:.3f}s | {res.steps} steps)")
        all_results[label] = results

        t_fixed = results["Fixed"].wall_time_s
        for strat, res in results.items():
            res.speedup = t_fixed / max(res.wall_time_s, 1e-9)
            rows.append({
                "Profile":       label,
                "Engine":        strat,
                "WallTime_s":    round(res.wall_time_s, 4),
                "Steps":         res.steps,
                "Speedup":       round(res.speedup, 3),
                "PosError_m":    round(res.pos_error_m, 2),
                "EventError_ms": round(res.event_error_ms, 4),
            })

    df_main = pd.DataFrame(rows)
    df_main.to_csv(os.path.join(OUT_DIR, "simulation_metrics.csv"), index=False)
    print(f"\n✓ Metrics → {OUT_DIR}/simulation_metrics.csv")

    # ── Persist dt + buffer sequences from already-collected runs ─────────────
    dt_df = pd.DataFrame(all_results["Mars"]["Adaptive"].dt_sequence,
                         columns=["t_s", "dt_s"])
    dt_df.to_csv(os.path.join(OUT_DIR, "adaptive_dt_sequence_mars.csv"), index=False)

    buf_df = pd.DataFrame(all_results["Cislunar"]["Adaptive"].buf_sequence,
                          columns=["t_s", "buf_bytes"])
    buf_df.to_csv(os.path.join(OUT_DIR, "buffer_sequence_cislunar.csv"), index=False)

    # ── Pareto: reuse main run (no re-simulation) ─────────────────────────────
    pareto = []
    for label in ["Mars", "Elliptical", "Cislunar"]:
        for strat, res in all_results[label].items():
            pareto.append({"Profile": label, "Engine": strat,
                           "Steps": res.steps, "PosError_m": res.pos_error_m})
    pd.DataFrame(pareto).to_csv(os.path.join(OUT_DIR, "pareto_data.csv"), index=False)
    print("✓ Pareto data saved.")

    # ── Per-step error sequences for validation figures ───────────────────────
    for label in ["Mars", "Elliptical", "Cislunar"]:
        for strat, res in all_results[label].items():
            if res.pos_err_seq:
                df_err = pd.DataFrame(res.pos_err_seq, columns=["t_s", "pos_err_m"])
                df_err["cum_err_m"] = [r[1] for r in res.cum_err_seq]
                safe = strat.lower()
                prof_safe = label.lower()
                df_err.to_csv(
                    os.path.join(OUT_DIR, f"error_seq_{prof_safe}_{safe}.csv"),
                    index=False
                )
    print("✓ Per-step error sequences saved.")

    # ── Scalability: adaptive only, 3 → 30 nodes ─────────────────────────────
    print("\n  Scalability stress test (Cislunar NRHO, adaptive engine) …")
    prof_c      = all_profs["Cislunar"]
    ref_t, ref_x, ref_y = build_ref(prof_c)
    node_counts = prof_c["simulation"]["node_counts"]
    scale_rows  = []
    for n in node_counts:
        orch_c = CoSimOrchestrator(prof_c, ref_t, ref_x, ref_y)
        res    = orch_c.run_adaptive(n_nodes=n)
        scale_rows.append({"Nodes": n,
                            "WallTime_s": round(res.wall_time_s, 4),
                            "Steps":      res.steps})
        print(f"    nodes={n:2d}  wall={res.wall_time_s:.3f}s  steps={res.steps}")

    df_scale = pd.DataFrame(scale_rows)
    df_scale.to_csv(os.path.join(OUT_DIR, "scalability_metrics.csv"), index=False)
    print(f"✓ Scalability → {OUT_DIR}/scalability_metrics.csv")

    return df_main, df_scale


if __name__ == "__main__":
    run_all()
