#!/usr/bin/env python3
"""
ECGR Simulation Runner
======================

Executes comparative simulations of standard CGR vs. proposed ECGR algorithm
for deep-space DTN relay networks. Runs multiple Monte Carlo iterations and
saves all results for offline analysis.

Usage:
    python run_simulation.py [--runs N] [--seed S] [--output DIR]

Output:
    results/simulation_results.json  - Complete results for analysis
    results/contact_plan.json        - Contact plan used
    results/contact_plan.ionrc       - ION-DTN compatible contact plan
"""

import argparse
import json
import os
import sys
import time
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import (
    SIM_DURATION, RANDOM_SEED, NUM_MONTE_CARLO_RUNS,
    RESULTS_DIR, NODE_NAMES
)
from simulation.contact_plan import ContactPlanGenerator
from simulation.simulator import DTNSimulator, TrafficGenerator
from simulation.spice_data import SyntheticSPICE


def run_single_comparison(contacts, bundles, seed):
    """Run a single CGR vs ECGR vs P-ECGR comparison with given contacts and bundles."""

    # --- Run standard CGR ---
    cgr_sim = DTNSimulator(router_type="CGR", seed=seed)
    cgr_sim.setup(contacts, bundles)
    cgr_results = cgr_sim.run()

    # --- Run ECGR ---
    ecgr_sim = DTNSimulator(router_type="ECGR", seed=seed)
    ecgr_sim.setup(contacts, bundles)
    ecgr_results = ecgr_sim.run()

    # --- Run P-ECGR ---
    pecgr_sim = DTNSimulator(router_type="P-ECGR", seed=seed)
    pecgr_sim.setup(contacts, bundles)
    pecgr_results = pecgr_sim.run()

    return cgr_results, ecgr_results, pecgr_results


def run_monte_carlo(num_runs, base_seed, output_dir):
    """
    Run Monte Carlo simulations with varying random seeds.

    Each run uses a different seed for traffic generation while
    keeping the contact plan consistent (orbital mechanics are deterministic).
    """
    os.makedirs(output_dir, exist_ok=True)

    # Generate contact plan (same for all runs - orbits are deterministic)
    print("\n" + "=" * 70)
    print("  ECGR vs CGR Comparative Simulation")
    print("  Mars Deep-Space Relay Network")
    print("=" * 70)
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
    all_ecgr_results = []
    all_pecgr_results = []

    for run_idx in range(num_runs):
        run_seed = base_seed + run_idx * 17  # Deterministic seed variation
        print(f"\n{'='*70}")
        print(f"  Monte Carlo Run {run_idx + 1}/{num_runs} (seed={run_seed})")
        print(f"{'='*70}")

        # Generate traffic for this run
        tg = TrafficGenerator(seed=run_seed)
        bundles = tg.generate_traffic()
        print(f"  Generated {len(bundles)} bundles")

        # Run comparison
        start_time = time.time()
        cgr_res, ecgr_res, pecgr_res = run_single_comparison(contacts, bundles, run_seed)
        elapsed = time.time() - start_time
        print(f"  Run completed in {elapsed:.1f}s")

        # Store results (without large timeseries for aggregate stats)
        cgr_summary = {k: v for k, v in cgr_res.items()
                       if k not in ['metrics_timeseries', 'smallsat_energy_log',
                                    'smallsat_buffer_log', 'mro_energy_log',
                                    'mro_buffer_log', 'routing_decisions']}
        ecgr_summary = {k: v for k, v in ecgr_res.items()
                        if k not in ['metrics_timeseries', 'smallsat_energy_log',
                                     'smallsat_buffer_log', 'mro_energy_log',
                                     'mro_buffer_log', 'routing_decisions']}
        pecgr_summary = {k: v for k, v in pecgr_res.items()
                         if k not in ['metrics_timeseries', 'smallsat_energy_log',
                                      'smallsat_buffer_log', 'mro_energy_log',
                                      'mro_buffer_log', 'routing_decisions']}
        cgr_summary['run_seed'] = run_seed
        ecgr_summary['run_seed'] = run_seed
        pecgr_summary['run_seed'] = run_seed
        all_cgr_results.append(cgr_summary)
        all_ecgr_results.append(ecgr_summary)
        all_pecgr_results.append(pecgr_summary)

        # Save detailed timeseries for the first run only
        if run_idx == 0:
            detailed = {
                "cgr": cgr_res,
                "ecgr": ecgr_res,
                "pecgr": pecgr_res,
            }
            with open(os.path.join(output_dir, "detailed_timeseries.json"), 'w') as f:
                json.dump(detailed, f, indent=2, default=str)

    # Compile aggregate statistics
    aggregate = compile_aggregate_stats(all_cgr_results, all_ecgr_results, all_pecgr_results)

    # Save all results
    final_output = {
        "simulation_config": {
            "duration_s": SIM_DURATION,
            "num_runs": num_runs,
            "base_seed": base_seed,
            "time_step_s": 10,
        },
        "aggregate_statistics": aggregate,
        "per_run_cgr": all_cgr_results,
        "per_run_ecgr": all_ecgr_results,
        "per_run_pecgr": all_pecgr_results,
    }

    output_path = os.path.join(output_dir, "simulation_results.json")
    with open(output_path, 'w') as f:
        json.dump(final_output, f, indent=2, default=str)

    print(f"\n{'='*70}")
    print(f"  All results saved to {output_path}")
    print(f"{'='*70}")

    # Print aggregate comparison
    print_aggregate_comparison(aggregate)

    return final_output


def compile_aggregate_stats(cgr_results, ecgr_results, pecgr_results):
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

    aggregate = {"cgr": {}, "ecgr": {}, "pecgr": {}}

    for algo, results in [("cgr", cgr_results), ("ecgr", ecgr_results), ("pecgr", pecgr_results)]:
        aggregate[algo] = {
            "delivery_ratio": stats([r["delivery_ratio"] for r in results]),
            "avg_latency_s": stats([r["avg_latency_s"] for r in results]),
            "p95_latency_s": stats([r["p95_latency_s"] for r in results]),
            "dropped": stats([r["dropped"] for r in results]),
            "smallsat_min_soc": stats([r["smallsat_min_soc"] for r in results]),
            "smallsat_avg_soc": stats([r["smallsat_avg_soc"] for r in results]),
            "smallsat_below_20pct": stats([r["smallsat_below_20pct_fraction"] for r in results]),
            "data_delivered_mb": stats([r["total_data_delivered_mb"] for r in results]),
        }

        # Per-priority aggregate
        for p in [1, 2, 3]:
            key = f"priority_{p}_delivery_ratio"
            vals = [r["priority_stats"][str(p)]["delivery_ratio"]
                    if str(p) in r["priority_stats"]
                    else r["priority_stats"].get(p, {}).get("delivery_ratio", 0)
                    for r in results]
            aggregate[algo][key] = stats(vals)

    return aggregate


def print_aggregate_comparison(aggregate):
    """Print formatted aggregate comparison table."""
    print(f"\n{'='*85}")
    print(f"  AGGREGATE COMPARISON (CGR vs ECGR vs P-ECGR)")
    print(f"{'='*85}")
    print(f"{'Metric':<30} {'CGR':>16} {'ECGR':>16} {'P-ECGR':>16}")
    print(f"{'─'*80}")

    metrics = [
        ("Delivery Ratio (%)", "delivery_ratio", 100),
        ("Avg Latency (s)", "avg_latency_s", 1),
        ("P95 Latency (s)", "p95_latency_s", 1),
        ("Bundles Dropped", "dropped", 1),
        ("SmallSat Min SoC (%)", "smallsat_min_soc", 100),
        ("SmallSat Avg SoC (%)", "smallsat_avg_soc", 100),
        ("SmallSat <20% Time (%)", "smallsat_below_20pct", 100),
        ("Data Delivered (MB)", "data_delivered_mb", 1),
    ]

    for label, key, scale in metrics:
        cgr_val = aggregate["cgr"][key]["mean"] * scale
        ecgr_val = aggregate["ecgr"][key]["mean"] * scale
        pecgr_val = aggregate["pecgr"][key]["mean"] * scale
        cgr_std = aggregate["cgr"][key]["std"] * scale
        ecgr_std = aggregate["ecgr"][key]["std"] * scale
        pecgr_std = aggregate["pecgr"][key]["std"] * scale
        print(f"  {label:<28} {cgr_val:>6.1f}±{cgr_std:<5.1f} "
              f"{ecgr_val:>6.1f}±{ecgr_std:<5.1f} "
              f"{pecgr_val:>6.1f}±{pecgr_std:<5.1f}")

    print(f"{'='*85}")


def main():
    parser = argparse.ArgumentParser(
        description="ECGR vs CGR Simulation for Deep-Space DTN"
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
