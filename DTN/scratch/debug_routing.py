import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.config import (
    SIM_DURATION, RANDOM_SEED, ROVER, SMALLSAT, MRO, DSN, NODE_SPECS, CONTACT_PARAMS
)
from simulation.contact_plan import ContactPlanGenerator
from simulation.simulator import DTNSimulator, TrafficGenerator

def debug():
    base_seed = 42
    cpg = ContactPlanGenerator(seed=base_seed)
    contacts = cpg.generate_full_contact_plan()
    tg = TrafficGenerator(seed=base_seed)
    bundles = tg.generate_traffic(SIM_DURATION)
    
    # We want to see a specific decision where MRO was chosen over SmallSat.
    sim = DTNSimulator(router_type="P-ECGR", seed=base_seed)
    sim.setup(contacts, bundles)
    
    # Let's override select_route to print details
    original_select_route = sim.router.select_route
    decision_count = 0
    
    def debug_select_route(routes, bundle, nodes, t):
        nonlocal decision_count
        selected = original_select_route(routes, bundle, nodes, t)
        # Only print if we are at the Rover (0) and there are multiple routes and it's Priority 2
        if bundle.current_node == 0 and len(routes) > 1 and bundle.priority == 2:
            decision_count += 1
            print(f"\n--- Decision {decision_count} for Bundle {bundle.bundle_id} (Priority {bundle.priority}, Size {bundle.size_mb:.1f}MB) at t={t:.1f} ---")
            
            # Re-evaluate each route to show costs
            feasible = []
            for r in routes:
                if not r.hops: continue
                if r.hops[0].dest in bundle.hops: continue
                capacity_ok = all(h.residual_capacity_bytes() >= bundle.size_bytes for h in r.hops)
                buffer_ok = all(nodes[n].can_store(bundle.size_bytes) for n in r.relay_nodes)
                
                energy_ok = True
                for h in r.hops:
                    n_id = h.source
                    if n_id != r.source and n_id in nodes:
                        tx_time = bundle.size_bytes * 8 / r.bottleneck_rate
                        pred_energy = sim.router.predict_node_energy(nodes[n_id], t, h.start_time)
                        energy_needed = (nodes[n_id].tx_power_w + nodes[n_id].idle_power_w) * (tx_time / 3600.0)
                        if pred_energy < energy_needed:
                            energy_ok = False
                
                status = f"Feasible" if (capacity_ok and buffer_ok and energy_ok) else f"Infeasible (cap={capacity_ok}, buf={buffer_ok}, eng={energy_ok})"
                print(f"Route: {r.source} -> {' -> '.join(str(h.dest) for h in r.hops)} (delay={r.total_delay:.1f}s, arr={r.arrival_time:.1f}s) - {status}")
                if capacity_ok and buffer_ok and energy_ok:
                    feasible.append(r)
            
            if feasible:
                max_delay = max(r.total_delay for r in feasible)
                norm = {"max_delay": max_delay, "predicted_socs": sim.router.get_predicted_socs(feasible, bundle, nodes, t)}
                for r in feasible:
                    # Print cost components
                    alpha, beta, gamma = sim.router.compute_dynamic_weights_pred(bundle, nodes, r, norm["predicted_socs"])
                    delay_norm = r.total_delay / max(max_delay, 1.0)
                    
                    # Energy cost
                    energy_cost = 0.0
                    for n_id in r.relay_nodes:
                        pred_soc = norm["predicted_socs"].get(n_id, nodes[n_id].soc)
                        tx_time = bundle.size_bytes * 8 / r.bottleneck_rate
                        energy_needed_wh = (nodes[n_id].tx_power_w + nodes[n_id].idle_power_w) * (tx_time / 3600.0)
                        soc_drop = energy_needed_wh / nodes[n_id].battery_capacity_wh
                        post_tx_soc = pred_soc - soc_drop
                        if post_tx_soc < 0.35:
                            penalty = (0.35 - post_tx_soc) / 0.35
                            energy_cost += penalty * 10.0
                        if post_tx_soc < 0.20:
                            energy_cost += 50.0
                            
                    # Buffer cost
                    buffer_ratios = [bundle.size_bytes / max(nodes[n].available_buffer_bytes, 1.0) for n in r.relay_nodes]
                    max_buf_ratio = max(buffer_ratios) if buffer_ratios else 0.0
                    
                    cost = alpha * delay_norm + beta * energy_cost + gamma * max_buf_ratio
                    print(f"  Cost for {' -> '.join(str(h.dest) for h in r.hops)}: {cost:.4f}")
                    print(f"    delay_term={alpha * delay_norm:.4f} (alpha={alpha:.2f}, norm={delay_norm:.4f})")
                    print(f"    energy_term={beta * energy_cost:.4f} (beta={beta:.2f}, cost={energy_cost:.4f})")
                    print(f"    buffer_term={gamma * max_buf_ratio:.4f} (gamma={gamma:.2f}, ratio={max_buf_ratio:.4f})")
            
            print(f"Selected: {' -> '.join(str(h.dest) for h in selected.hops) if selected else 'None'}")
            
            if decision_count >= 5:
                sys.exit(0)
            
        return selected
    
    sim.router.select_route = debug_select_route
    sim.run()

if __name__ == "__main__":
    debug()
