import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.config import (
    SIM_DURATION, RANDOM_SEED, ROVER, SMALLSAT, MRO, DSN
)
from simulation.contact_plan import ContactPlanGenerator
from simulation.simulator import DTNSimulator, TrafficGenerator

base_seed = 42
cpg = ContactPlanGenerator(seed=base_seed)
contacts = cpg.generate_full_contact_plan()
tg = TrafficGenerator(seed=base_seed)
bundles = tg.generate_traffic(SIM_DURATION)

for alg in ["CGR", "ECGR", "P-ECGR"]:
    sim = DTNSimulator(router_type=alg, seed=base_seed)
    sim.setup(contacts, bundles)
    # Let's intercept select_route or run the simulation and look at decisions
    sim.run()
    print(f"\n=== {alg} DECISIONS SUMMARY ===")
    decisions = sim.routing_decisions
    print(f"Total decisions: {len(decisions)}")
    # Count transitions
    transitions = {}
    for d in decisions:
        key = (d["from"], d["to"])
        transitions[key] = transitions.get(key, 0) + 1
    for key, count in transitions.items():
        print(f"  {key[0]} -> {key[1]}: {count}")
