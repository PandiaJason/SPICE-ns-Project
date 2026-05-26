import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.config import (
    SIM_DURATION, RANDOM_SEED, ROVER, SMALLSAT, MRO, DSN
)
from simulation.contact_plan import ContactPlanGenerator
from simulation.simulator import DTNSimulator, TrafficGenerator

# Generate contacts and traffic
base_seed = 42
cpg = ContactPlanGenerator(seed=base_seed)
contacts = cpg.generate_full_contact_plan()

tg = TrafficGenerator(seed=base_seed)
bundles = tg.generate_traffic(SIM_DURATION)

print(f"Generated {len(bundles)} bundles.")

for alg in ["CGR", "ECGR", "P-ECGR"]:
    sim = DTNSimulator(router_type=alg, seed=base_seed)
    sim.setup(contacts, bundles)
    results = sim.run()
    
    print(f"\n=== {alg} BUNDLE STATUS ===")
    # Count bundles at each node
    for node_id, node in sim.nodes.items():
        print(f"Node {node_id} ({node.name}): {len(node.bundle_queue)} bundles in queue")
        if len(node.bundle_queue) > 0:
            sizes = [b.size_mb for b in node.bundle_queue]
            priorities = [b.priority for b in node.bundle_queue]
            print(f"  Sizes: min={min(sizes):.1f}MB, max={max(sizes):.1f}MB, avg={sum(sizes)/len(sizes):.1f}MB")
            print(f"  Priorities: {dict((p, priorities.count(p)) for p in set(priorities))}")

    # Let's see if there are any bundles in transit that have hops
    transit_with_hops = 0
    transit_no_hops = 0
    for b in sim.bundles:
        # Note: sim.bundles holds the original/modified bundles
        # Let's find them in nodes
        pass
    
    # We can check sim.delivered_bundles and sim.dropped_bundles
    print(f"Delivered count: {len(sim.delivered_bundles)}")
    print(f"Dropped count: {len(sim.dropped_bundles)}")
