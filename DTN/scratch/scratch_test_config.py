import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import copy
import numpy as np

# We want to dynamically modify NODE_SPECS and CONTACT_PARAMS and run the simulation to see results.
from simulation.config import (
    SIM_DURATION, RANDOM_SEED, ROVER, SMALLSAT, MRO, DSN, NODE_SPECS, CONTACT_PARAMS, TRAFFIC_PROFILES
)
from simulation.contact_plan import ContactPlanGenerator
from simulation.simulator import DTNSimulator, TrafficGenerator

def run_sim_with_params(smallsat_battery, smallsat_gen, smallsat_rate, smallsat_tx_power=15.0):
    # Backup original config values
    orig_specs = copy.deepcopy(NODE_SPECS)
    orig_params = copy.deepcopy(CONTACT_PARAMS)
    
    # Apply new values
    NODE_SPECS[SMALLSAT]["battery_capacity_wh"] = smallsat_battery
    NODE_SPECS[SMALLSAT]["power_generation_w"] = smallsat_gen
    NODE_SPECS[SMALLSAT]["tx_power_w"] = smallsat_tx_power
    CONTACT_PARAMS[(SMALLSAT, DSN)]["data_rate_bps"] = smallsat_rate
    
    base_seed = 42
    cpg = ContactPlanGenerator(seed=base_seed)
    contacts = cpg.generate_full_contact_plan()
    tg = TrafficGenerator(seed=base_seed)
    bundles = tg.generate_traffic(SIM_DURATION)
    
    results = {}
    for alg in ["CGR", "ECGR", "P-ECGR"]:
        sim = DTNSimulator(router_type=alg, seed=base_seed)
        sim.setup(contacts, bundles)
        res = sim.run()
        results[alg] = {
            "bdr": res["delivery_ratio"] * 100,
            "min_soc": res["smallsat_min_soc"] * 100,
            "below_20": res["smallsat_below_20pct_fraction"] * 100,
        }
        
    # Restore original config values
    for k, v in orig_specs.items():
        NODE_SPECS[k] = v
    for k, v in orig_params.items():
        CONTACT_PARAMS[k] = v
        
    return results

# Test some parameter combinations
print("Test 1: Increase SmallSat battery to 30Wh, charging to 20W, link rate to 500kbps")
res1 = run_sim_with_params(30.0, 20.0, 5e5)
for alg, metrics in res1.items():
    print(f"  {alg}: BDR={metrics['bdr']:.1f}%, Min SoC={metrics['min_soc']:.1f}%, Below 20%={metrics['below_20']:.1f}%")

print("\nTest 2: Increase SmallSat battery to 40Wh, charging to 25W, link rate to 1Mbps")
res2 = run_sim_with_params(40.0, 25.0, 1e6)
for alg, metrics in res2.items():
    print(f"  {alg}: BDR={metrics['bdr']:.1f}%, Min SoC={metrics['min_soc']:.1f}%, Below 20%={metrics['below_20']:.1f}%")
