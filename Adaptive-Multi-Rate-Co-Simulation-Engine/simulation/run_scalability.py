"""
run_scalability.py  –  Scalability stress test for Cislunar NRHO (Adaptive Engine).
Benchmarks node counts: [10, 50, 100, 200, 300, 400, 500].
Updates outputs/scalability_metrics.csv and regenerates Figure 1 (fig1_perf_panel.pdf).
"""

import json, os, sys, time
import numpy as np
import pandas as pd

ROOT     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
OUT_DIR  = os.path.join(ROOT, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

sys.path.insert(0, ROOT)
from engine import CoSimOrchestrator
from generate_figures import fig_perf_panel

def main():
    print(f"\n{'='*60}\n  Scalability Stress Test: 10 to 500 Spacecraft Nodes\n{'='*60}")
    profile_path = os.path.join(DATA_DIR, "cislunar_nrho_profile.json")
    with open(profile_path) as f:
        prof = json.load(f)

    gt = prof["ground_truth"]
    ref_t = np.array(gt["t_s"])
    ref_x = np.array(gt["x_m"])
    ref_y = np.array(gt["y_m"])

    node_counts = [10, 50, 100, 200, 300, 400, 500]
    scale_rows  = []

    for n in node_counts:
        print(f"  Simulating {n:3d} nodes … ", end="", flush=True)
        orch = CoSimOrchestrator(prof, ref_t, ref_x, ref_y)
        t0 = time.perf_counter()
        res = orch.run_adaptive(n_nodes=n)
        wall = time.perf_counter() - t0
        scale_rows.append({
            "Nodes": n,
            "WallTime_s": round(wall, 4),
            "Steps": res.steps
        })
        print(f"done  (wall={wall:.4f}s | steps={res.steps})")

    df_scale = pd.DataFrame(scale_rows)
    csv_path = os.path.join(OUT_DIR, "scalability_metrics.csv")
    df_scale.to_csv(csv_path, index=False)
    print(f"\n✓ Saved scalability metrics → {csv_path}")

    print("\nRegenerating Figure 1 (Performance Panel)...")
    fig_perf_panel()
    print("✓ Figure 1 regenerated successfully!")

if __name__ == "__main__":
    main()
