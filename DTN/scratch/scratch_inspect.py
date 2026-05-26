import json
import os

base_dir = "/home/jason/DTN"
results_file = os.path.join(base_dir, "results", "simulation_results.json")

with open(results_file, 'r') as f:
    data = json.load(f)

# Let's print the aggregate statistics
print("Aggregate Statistics:")
for alg in ["cgr", "ecgr", "pecgr"]:
    stats = data["aggregate_statistics"][alg]
    print(f"  {alg}:")
    for k, v in stats.items():
        if "mean" in v:
            print(f"    {k}: {v['mean']:.2f} +/- {v['std']:.2f}")

# Let's inspect the first run's routing decisions
for alg, key in [("CGR", "per_run_cgr"), ("ECGR", "per_run_ecgr"), ("P-ECGR", "per_run_pecgr")]:
    run = data[key][0]
    print(f"\n{alg} Run details:")
    print(f"  Total bundles: {run['total_bundles']}")
    print(f"  Delivered: {run['delivered']}")
    print(f"  Dropped: {run['dropped']}")
    print(f"  In Transit: {run['in_transit']}")
    
    # We can inspect the routing decisions from the simulator run by printing some stats about them
    # Wait, the simulator class returns results, let's see if the run logs routing decisions
    # Let's check if the JSON has routing decisions
    # Let's write a small script that runs the simulator directly for 1 run and inspects its state.
