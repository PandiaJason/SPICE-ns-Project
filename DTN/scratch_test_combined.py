import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import copy
import numpy as np

from simulation.config import (
    SIM_DURATION, RANDOM_SEED, ROVER, SMALLSAT, MRO, DSN, NODE_SPECS, CONTACT_PARAMS
)
from simulation.contact_plan import ContactPlanGenerator
from simulation.simulator import DTNSimulator, TrafficGenerator
from simulation.routing import CGRRouter, ECGRRouter, PECGRRouter, EBECGRRouter

def patched_cgr_select_route(self, routes, bundle, nodes, current_time):
    if not routes:
        return None
    feasible = []
    for route in routes:
        if not route.hops:
            continue
        if route.hops[0].dest in bundle.hops:
            continue
        sufficient = True
        for hop in route.hops:
            if hop.residual_capacity_bytes() < bundle.size_bytes:
                sufficient = False
                break
        if sufficient:
            feasible.append(route)
    if not feasible:
        return None
    return min(feasible, key=lambda r: r.arrival_time)

def patched_ecgr_select_route(self, routes, bundle, nodes, current_time):
    if not routes:
        return None
    feasible = []
    for route in routes:
        if not route.hops:
            continue
        if route.hops[0].dest in bundle.hops:
            continue
        capacity_ok = all(
            hop.residual_capacity_bytes() >= bundle.size_bytes
            for hop in route.hops
        )
        if not capacity_ok:
            continue
        buffer_ok = True
        for n_id in route.relay_nodes:
            if n_id in nodes and not nodes[n_id].can_store(bundle.size_bytes):
                buffer_ok = False
                break
        if not buffer_ok:
            continue
        energy_ok = True
        for n_id in route.relay_nodes:
            if n_id in nodes:
                tx_time = bundle.size_bytes * 8 / route.bottleneck_rate
                if not nodes[n_id].can_transmit(tx_time):
                    energy_ok = False
                    break
        if not energy_ok:
            continue
        feasible.append(route)
    if not feasible:
        return None
    max_delay = max(r.total_delay for r in feasible) if feasible else 86400.0
    normalization = {"max_delay": max_delay}
    best = min(feasible, key=lambda r: self.compute_cost(r, bundle, nodes, normalization))
    return best

def patched_ebecgr_select_route(self, routes, bundle, nodes, current_time):
    if not routes:
        return None
    self._clean_old_bookings(current_time)
    self._remove_bundle_bookings(bundle.bundle_id)
    feasible = []
    for route in routes:
        if not route.hops:
            continue
        if route.hops[0].dest in bundle.hops:
            continue
        capacity_ok = all(
            hop.residual_capacity_bytes() >= bundle.size_bytes
            for hop in route.hops
        )
        if not capacity_ok:
            continue
        buffer_ok = True
        for n_id in route.relay_nodes:
            if n_id in nodes and not nodes[n_id].can_store(bundle.size_bytes):
                buffer_ok = False
                break
        if not buffer_ok:
            continue
        energy_ok = True
        for i, hop in enumerate(route.hops):
            n_id = hop.source
            if n_id != route.source and n_id in nodes:
                tx_time = bundle.size_bytes * 8 / route.bottleneck_rate
                pred_energy = self.predict_node_energy(
                    nodes[n_id], current_time, hop.start_time, bundle.bundle_id
                )
                energy_needed = (nodes[n_id].tx_power_w + nodes[n_id].idle_power_w) * (tx_time / 3600.0)
                if pred_energy < energy_needed:
                    energy_ok = False
                    break
        if not energy_ok:
            continue
        feasible.append(route)
    if not feasible:
        return None
        
    predicted_socs = {}
    for route in feasible:
        for hop in route.hops:
            n_id = hop.source
            if n_id != route.source and n_id in nodes:
                pred_energy = self.predict_node_energy(
                    nodes[n_id], current_time, hop.start_time, bundle.bundle_id
                )
                pred_soc = pred_energy / nodes[n_id].battery_capacity_wh
                if n_id not in predicted_socs or pred_soc < predicted_socs[n_id]:
                    predicted_socs[n_id] = pred_soc

    max_delay = max(r.total_delay for r in feasible) if feasible else 86400.0
    normalization = {"max_delay": max_delay, "predicted_socs": predicted_socs}
    best = min(feasible, key=lambda r: self.compute_cost_pred(r, bundle, nodes, normalization, current_time))
    
    if best:
        for hop in best.hops:
            n_id = hop.source
            if n_id != best.source and n_id in nodes:
                tx_time = bundle.size_bytes * 8 / best.bottleneck_rate
                energy_needed = (nodes[n_id].tx_power_w + nodes[n_id].idle_power_w) * (tx_time / 3600.0)
                if n_id not in self.bookings:
                    self.bookings[n_id] = []
                self.bookings[n_id].append((hop.start_time, energy_needed, bundle.bundle_id))
    return best

CGRRouter.select_route = patched_cgr_select_route
ECGRRouter.select_route = patched_ecgr_select_route
EBECGRRouter.select_route = patched_ebecgr_select_route

# Modify SmallSat parameters
NODE_SPECS[SMALLSAT]["battery_capacity_wh"] = 16.0
NODE_SPECS[SMALLSAT]["power_generation_w"] = 12.0
CONTACT_PARAMS[(SMALLSAT, DSN)]["data_rate_bps"] = 5e5

print("Running simulation with Battery=16Wh, Gen=12W, Rate=500kbps + Loop Prevention:")
base_seed = 42
cpg = ContactPlanGenerator(seed=base_seed)
contacts = cpg.generate_full_contact_plan()
tg = TrafficGenerator(seed=base_seed)
bundles = tg.generate_traffic(SIM_DURATION)

for alg in ["CGR", "ECGR", "P-ECGR"]:
    sim = DTNSimulator(router_type=alg, seed=base_seed)
    sim.setup(contacts, bundles)
    res = sim.run()
    print(f"  {alg}: BDR={res['delivery_ratio']*100:.1f}%, Min SoC={res['smallsat_min_soc']*100:.1f}%, Below 20%={res['smallsat_below_20pct_fraction']*100:.1f}%")
