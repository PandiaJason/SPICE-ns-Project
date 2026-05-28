#!/usr/bin/env python3
"""
ML-CGR Simulation Runner
========================

Executes comparative simulations of standard CGR vs. proposed ML-CGR algorithm
for deep-space DTN relay networks with ML-driven link quality estimation and
proactive bundle fragmentation. Runs multiple Monte Carlo iterations and
saves all results for offline analysis.

Usage:
    python run_simulation.py [--runs N] [--seed S] [--output DIR]

Output:
    results/simulation_results.json  - Complete results for analysis
    results/contact_plan.json        - Contact plan with LQI values
    results/contact_plan.ionrc       - ION-DTN compatible contact plan
    results/detailed_timeseries.json - First-run time series data
"""

import argparse
import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import (
    SIM_DURATION, RANDOM_SEED, NUM_MONTE_CARLO_RUNS,
    RESULTS_DIR, NODE_NAMES
)
from simulation.contact_plan import ContactPlanGenerator
from simulation.simulator import DTNSimulator, TrafficGenerator
from simulation.spice_data import SyntheticSPICE


def run_single_comparison(contacts, bundles, seed):
    """Run a single CGR vs ML-CGR comparison with given contacts and bundles."""

    # --- Run standard CGR ---
    cgr_sim = DTNSimulator(router_type="CGR", seed=seed)
    cgr_sim.setup(contacts, bundles)
    cgr_results = cgr_sim.run()

    # --- Run ML-CGR ---
    mlcgr_sim = DTNSimulator(router_type="ML-CGR", seed=seed)
    mlcgr_sim.setup(contacts, bundles)
    mlcgr_results = mlcgr_sim.run()

    return cgr_results, mlcgr_results


def run_monte_carlo(num_runs, base_seed, output_dir):
    """
    Run Monte Carlo simulations with varying random seeds.

    Each run uses a different seed for traffic generation while
    keeping the contact plan consistent (orbital mechanics are deterministic).
    """
    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "=" * 72)
    print("  ML-CGR vs CGR Comparative Simulation")
    print("  Mars Deep-Space Relay Network — ML Link Quality + Fragmentation")
    print("=" * 72)
    print(f"\n  Monte Carlo runs: {num_runs}")
    print(f"  Base seed: {base_seed}")
    print(f"  Simulation duration: {SIM_DURATION}s ({SIM_DURATION/3600:.1f} hours)")

    # Generate contact plan
    print("\n--- Generating Contact Plan from Orbital Data ---")
    cpg = ContactPlanGenerator(seed=base_seed)
    contacts = cpg.generate_full_contact_plan()

    # Export contact plans
    cpg.export_json(os.path.join(output_dir, "contact_plan.json"))
    cpg.export_ion_dtn_format(os.path.join(output_dir, "contact_plan.ionrc"))

    # Export SPICE ephemeris data
    spice = SyntheticSPICE(seed=base_seed)
    spice_data = {
        "smallsat_ephemeris": spice.generate_ephemeris_table('smallsat', dt=300),
        "mro_ephemeris": spice.generate_ephemeris_table('mro', dt=300),
        "smallsat_eclipse_windows": spice.compute_eclipse_windows('smallsat'),
        "orbital_parameters": {
            "smallsat_period_s": float(spice.smallsat_period),
            "mro_period_s": float(spice.mro_period),
            "smallsat_altitude_km": spice.smallsat_a - 3389.5,
            "mro_altitude_km": spice.mro_a - 3389.5,
            "smallsat_inclination_deg": spice.smallsat_inc,
            "mro_inclination_deg": spice.mro_inc,
            "rover_lat_deg": spice.rover_lat,
            "rover_lon_deg": spice.rover_lon,
        }
    }
    with open(os.path.join(output_dir, "spice_ephemeris.json"), 'w') as f:
        json.dump(spice_data, f, indent=2, default=str)
    print(f"[SPICE] Ephemeris data saved to {output_dir}/spice_ephemeris.json")

    # Run Monte Carlo simulations
    all_cgr_results = []
    all_mlcgr_results = []

    EXCLUDE_KEYS = [
        'metrics_timeseries', 'smallsat_energy_log',
        'smallsat_buffer_log', 'mro_energy_log', 'mro_buffer_log',
        'routing_decisions', 'lqi_predictions', 'fragmentation_events',
    ]

    for run_idx in range(num_runs):
        run_seed = base_seed + run_idx * 17
        print(f"\n{'='*72}")
        print(f"  Monte Carlo Run {run_idx + 1}/{num_runs} (seed={run_seed})")
        print(f"{'='*72}")

        tg = TrafficGenerator(seed=run_seed)
        bundles = tg.generate_traffic()
        print(f"  Generated {len(bundles)} bundles")

        start_time = time.time()
        cgr_res, mlcgr_res = run_single_comparison(contacts, bundles, run_seed)
        elapsed = time.time() - start_time
        print(f"  Run completed in {elapsed:.1f}s")

        cgr_summary = {k: v for k, v in cgr_res.items() if k not in EXCLUDE_KEYS}
        mlcgr_summary = {k: v for k, v in mlcgr_res.items() if k not in EXCLUDE_KEYS}
        cgr_summary['run_seed'] = run_seed
        mlcgr_summary['run_seed'] = run_seed
        all_cgr_results.append(cgr_summary)
        all_mlcgr_results.append(mlcgr_summary)

        # Save detailed timeseries for the first run only
        if run_idx == 0:
            detailed = {
                "cgr": cgr_res,
                "mlcgr": mlcgr_res,
            }
            with open(os.path.join(output_dir, "detailed_timeseries.json"), 'w') as f:
                json.dump(detailed, f, indent=2, default=str)
            print(f"  [First run] Detailed timeseries saved.")

    # Compile aggregate statistics
    aggregate = compile_aggregate_stats(all_cgr_results, all_mlcgr_results)

    final_output = {
        "simulation_config": {
            "duration_s": SIM_DURATION,
            "num_runs": num_runs,
            "base_seed": base_seed,
            "time_step_s": 10,
            "algorithms": ["CGR", "ML-CGR"],
        },
        "aggregate_statistics": aggregate,
        "per_run_cgr": all_cgr_results,
        "per_run_mlcgr": all_mlcgr_results,
    }

    output_path = os.path.join(output_dir, "simulation_results.json")
    with open(output_path, 'w') as f:
        json.dump(final_output, f, indent=2, default=str)

    print(f"\n{'='*72}")
    print(f"  All results saved to {output_path}")
    print(f"{'='*72}")

    print_aggregate_comparison(aggregate)
    return final_output


def compile_aggregate_stats(cgr_results, mlcgr_results):
    """Compile aggregate statistics across all Monte Carlo runs."""

    def stats(values):
        arr = np.array(values, dtype=float)
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "median": float(np.median(arr)),
        }

    aggregate = {"cgr": {}, "mlcgr": {}}

    for algo, results in [("cgr", cgr_results), ("mlcgr", mlcgr_results)]:
        aggregate[algo] = {
            "delivery_ratio": stats([r["delivery_ratio"] for r in results]),
            "avg_latency_s": stats([r["avg_latency_s"] for r in results]),
            "p95_latency_s": stats([r["p95_latency_s"] for r in results]),
            "dropped": stats([r["dropped"] for r in results]),
            "smallsat_min_soc": stats([r["smallsat_min_soc"] for r in results]),
            "smallsat_avg_soc": stats([r["smallsat_avg_soc"] for r in results]),
            "smallsat_below_20pct": stats([r["smallsat_below_20pct_fraction"] for r in results]),
            "data_delivered_mb": stats([r["total_data_delivered_mb"] for r in results]),
            "n_fragmentation_events": stats([r.get("n_fragmentation_events", 0) for r in results]),
            "n_fragments_total": stats([r.get("n_fragments_total", 0) for r in results]),
            "avg_predicted_lqi": stats([r.get("avg_predicted_lqi", 1.0) for r in results]),
        }

        for p in [1, 2, 3]:
            key = f"priority_{p}_delivery_ratio"
            vals = [r["priority_stats"].get(str(p), r["priority_stats"].get(p, {})).get("delivery_ratio", 0)
                    for r in results]
            aggregate[algo][key] = stats(vals)

    return aggregate


def print_aggregate_comparison(aggregate):
    """Print formatted aggregate comparison table."""
    print(f"\n{'='*78}")
    print(f"  AGGREGATE COMPARISON (Standard CGR vs. Proposed ML-CGR)")
    print(f"{'='*78}")
    print(f"{'Metric':<35} {'CGR':>18} {'ML-CGR':>18}")
    print(f"{'─'*72}")

    metrics = [
        ("Delivery Ratio (%)", "delivery_ratio", 100),
        ("Avg Latency (s)", "avg_latency_s", 1),
        ("P95 Latency (s)", "p95_latency_s", 1),
        ("Bundles Dropped", "dropped", 1),
        ("SmallSat Min SoC (%)", "smallsat_min_soc", 100),
        ("SmallSat Avg SoC (%)", "smallsat_avg_soc", 100),
        ("SmallSat <20% Time (%)", "smallsat_below_20pct", 100),
        ("Data Delivered (MB)", "data_delivered_mb", 1),
        ("Fragmentation Events", "n_fragmentation_events", 1),
        ("Total Fragments", "n_fragments_total", 1),
        ("Avg Predicted LQI", "avg_predicted_lqi", 1),
    ]

    for label, key, scale in metrics:
        cgr_val = aggregate["cgr"][key]["mean"] * scale
        mlcgr_val = aggregate["mlcgr"][key]["mean"] * scale
        cgr_std = aggregate["cgr"][key]["std"] * scale
        mlcgr_std = aggregate["mlcgr"][key]["std"] * scale
        print(f"  {label:<33} {cgr_val:>6.2f}±{cgr_std:<6.2f} "
              f"{mlcgr_val:>6.2f}±{mlcgr_std:<6.2f}")

    print(f"{'='*78}")


def main():
    parser = argparse.ArgumentParser(
        description="ML-CGR vs CGR Simulation for Deep-Space DTN"
    )
    parser.add_argument("--runs", type=int, default=NUM_MONTE_CARLO_RUNS,
                        help="Number of Monte Carlo runs")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED,
                        help="Base random seed")
    parser.add_argument("--output", type=str, default=RESULTS_DIR,
                        help="Output directory for results")
    args = parser.parse_args()

    run_monte_carlo(args.runs, args.seed, args.output)


if __name__ == "__main__":
    main()
