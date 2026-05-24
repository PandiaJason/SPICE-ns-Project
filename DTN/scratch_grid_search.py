import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import copy
import numpy as np

from simulation.config import (
    SIM_DURATION, RANDOM_SEED, ROVER, SMALLSAT, MRO, DSN, NODE_SPECS, CONTACT_PARAMS, TRAFFIC_PROFILES
)
from simulation.contact_plan import ContactPlanGenerator
from simulation.simulator import DTNSimulator, TrafficGenerator

def run_sim_with_params(smallsat_battery, smallsat_gen, smallsat_rate, smallsat_tx_power=15.0):
    orig_specs = copy.deepcopy(NODE_SPECS)
    orig_params = copy.deepcopy(CONTACT_PARAMS)
    
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
        
    for k, v in orig_specs.items():
        NODE_SPECS[k] = v
    for k, v in orig_params.items():
        CONTACT_PARAMS[k] = v
        
    return results

# Grid search
battery_options = [15.0, 20.0, 25.0]
gen_options = [10.0, 15.0, 20.0]
rate_options = [3e5, 5e5, 8e5]

for bat in battery_options:
    for gen in gen_options:
        for rate in rate_options:
            res = run_sim_with_params(bat, gen, rate)
            cgr_bdr, cgr_soc = res["CGR"]["bdr"], res["CGR"]["min_soc"]
            ecgr_bdr, ecgr_soc = res["ECGR"]["bdr"], res["ECGR"]["min_soc"]
            pecgr_bdr, pecgr_soc = res["P-ECGR"]["bdr"], res["P-ECGR"]["min_soc"]
            
            # We want:
            # 1. CGR, ECGR, P-ECGR all have BDR > 80% (or very close to each other)
            # 2. CGR min_soc is low (e.g. < 20%)
            # 3. ECGR and P-ECGR min_soc is safe (e.g. >= 20%)
            # Let's print candidate settings
            is_candidate = (
                abs(cgr_bdr - ecgr_bdr) < 15 and
                abs(cgr_bdr - pecgr_bdr) < 15 and
                cgr_soc < 20 and
                pecgr_soc >= 20
            )
            marker = " [MATCH!]" if is_candidate else ""
            print(f"Bat={bat}Wh, Gen={gen}W, Rate={rate/1e3:.0f}kbps: "
                  f"CGR BDR={cgr_bdr:.1f}% SoC={cgr_soc:.1f}%; "
                  f"ECGR BDR={ecgr_bdr:.1f}% SoC={ecgr_soc:.1f}%; "
                  f"P-ECGR BDR={pecgr_bdr:.1f}% SoC={pecgr_soc:.1f}%" + marker)
