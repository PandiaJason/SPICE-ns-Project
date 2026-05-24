"""
Main simulation engine for ECGR evaluation.

Implements a discrete-time event-driven simulator that models the
complete DTN bundle forwarding process including energy dynamics,
buffer management, eclipse transitions, and bundle lifecycle tracking.
"""

import copy
import json
import os
import numpy as np
from typing import List, Dict, Optional
from simulation.config import (
    SIM_DURATION, TIME_STEP, RANDOM_SEED,
    ROVER, SMALLSAT, MRO, DSN, NODE_NAMES,
    TRAFFIC_PROFILES, RESULTS_DIR, ECLIPSE_FRACTION
)
from simulation.models import Contact, Node, Bundle, Route
from simulation.routing import CGRRouter, ECGRRouter, PECGRRouter, EBECGRRouter, find_all_routes
from simulation.contact_plan import ContactPlanGenerator
from simulation.spice_data import SyntheticSPICE


class TrafficGenerator:
    """Generates bundle traffic based on configured traffic profiles."""

    def __init__(self, seed: int = RANDOM_SEED):
        self.rng = np.random.default_rng(seed)
        self.bundle_id_counter = 0

    def generate_traffic(self, duration: float = SIM_DURATION) -> List[Bundle]:
        """Generate all bundles for the simulation duration."""
        bundles = []
        for profile in TRAFFIC_PROFILES:
            t = self.rng.uniform(*profile["interval_range_s"])
            while t < duration:
                self.bundle_id_counter += 1
                size_mb = self.rng.uniform(*profile["size_range_mb"])
                size_bytes = size_mb * 1024 * 1024

                bundle = Bundle(
                    bundle_id=self.bundle_id_counter,
                    source=profile["source"],
                    destination=profile["destination"],
                    size_bytes=size_bytes,
                    priority=profile["priority"],
                    creation_time=t,
                    payload_type=profile["name"],
                )
                bundles.append(bundle)

                interval = self.rng.uniform(*profile["interval_range_s"])
                t += interval

        bundles.sort(key=lambda b: b.creation_time)
        return bundles


class DTNSimulator:
    """
    Discrete-time DTN simulator.

    Simulates bundle forwarding through a contact-graph-routed
    deep-space network with energy and buffer constraints.
    """

    def __init__(self, router_type: str = "CGR", seed: int = RANDOM_SEED):
        self.router_type = router_type
        self.seed = seed
        self.rng = np.random.default_rng(seed)

        # Initialize router
        if router_type == "ECGR":
            self.router = ECGRRouter()
        elif router_type in ["P-ECGR", "PECGR"]:
            self.router = EBECGRRouter()
        else:
            self.router = CGRRouter()

        # Initialize nodes
        self.nodes: Dict[int, Node] = {}
        for node_id in [ROVER, SMALLSAT, MRO, DSN]:
            self.nodes[node_id] = Node(node_id)

        # Contact plan & traffic
        self.contacts: List[Contact] = []
        self.bundles: List[Bundle] = []
        self.delivered_bundles: List[Bundle] = []
        self.dropped_bundles: List[Bundle] = []

        # SPICE data for eclipse modeling
        self.spice = SyntheticSPICE(seed=seed)
        self.eclipse_windows = self.spice.compute_eclipse_windows('smallsat')

        # Metrics logging
        self.metrics_log: List[dict] = []
        self.routing_decisions: List[dict] = []

    def setup(self, contacts: List[Contact], bundles: List[Bundle]):
        """
        Configure simulation with contact plan and traffic.

        Parameters
        ----------
        contacts : list of Contact
            Pre-generated contact plan.
        bundles : list of Bundle
            Pre-generated traffic bundles.
        """
        # Deep copy to avoid mutation across runs
        self.contacts = [copy.deepcopy(c) for c in contacts]
        self.bundles = [copy.deepcopy(b) for b in bundles]
        self.delivered_bundles = []
        self.dropped_bundles = []
        self.metrics_log = []
        self.routing_decisions = []

        # Reset nodes and router
        for node in self.nodes.values():
            node.reset()
        if hasattr(self.router, "reset"):
            self.router.reset()

    def _is_in_eclipse(self, t: float) -> bool:
        """Check if SmallSat is in Mars shadow at time t."""
        for start, end in self.eclipse_windows:
            if start <= t < end:
                return True
        return False

    def _get_active_contacts(self, t: float) -> List[Contact]:
        """Get all contacts active at time t."""
        return [c for c in self.contacts if c.is_active(t)]

    def _inject_bundles(self, t: float):
        """Inject new bundles created at or before time t into source node."""
        to_inject = [b for b in self.bundles
                     if b.creation_time <= t and b.current_node == b.source
                     and not b.is_delivered and not b.is_dropped
                     and b not in self.nodes[b.source].bundle_queue]

        for bundle in to_inject:
            node = self.nodes[bundle.source]
            if node.can_store(bundle.size_bytes):
                node.store_bundle(bundle)
            else:
                bundle.is_dropped = True
                bundle.drop_reason = "source_buffer_full"
                self.dropped_bundles.append(bundle)

    def _forward_bundles(self, t: float):
        """Attempt to forward queued bundles at each node."""
        active_contacts = self._get_active_contacts(t)

        for node_id in [ROVER, SMALLSAT, MRO]:
            node = self.nodes[node_id]
            if not node.bundle_queue:
                continue

            # Sort by priority (critical first)
            queue = sorted(node.bundle_queue, key=lambda b: b.priority)

            for bundle in list(queue):
                if bundle.is_delivered or bundle.is_dropped:
                    continue

                # Find outgoing contacts from this node
                outgoing = [c for c in active_contacts if c.source == node_id]
                if not outgoing:
                    continue

                # Find routes from current node to destination
                routes = find_all_routes(
                    self.contacts, node_id, bundle.destination, t
                )

                if not routes:
                    continue

                # Select route using current algorithm
                selected = self.router.select_route(
                    routes, bundle, self.nodes, t
                )

                if selected is None:
                    continue

                # Get next hop from selected route
                if not selected.hops:
                    continue
                next_hop_contact = selected.hops[0]

                # Verify the contact is still active
                if not next_hop_contact.is_active(t):
                    continue

                next_node_id = next_hop_contact.dest
                next_node = self.nodes[next_node_id]

                # Transmission time
                tx_time = bundle.size_bytes * 8 / next_hop_contact.data_rate_bps

                # --- CGR: no energy/buffer pre-checks (blind forwarding) ---
                # --- ECGR: already filtered in route selection ---

                # Energy check: CGR transmits regardless, draining battery
                if not node.is_ground and not node.can_transmit(tx_time):
                    if self.router_type == "CGR":
                        # CGR attempts transmission anyway - energy depleted
                        node.energy_wh = 0.0  # Battery drained
                        bundle.is_dropped = True
                        bundle.drop_reason = "tx_energy_exhausted"
                        self.dropped_bundles.append(bundle)
                        node.remove_bundle(bundle)
                        continue
                    else:
                        # ECGR should have already filtered this
                        continue

                # Deliver to DSN
                if next_node_id == DSN:
                    bundle.is_delivered = True
                    bundle.delivery_time = t + tx_time + next_hop_contact.owlt_s
                    bundle.hops.append(next_node_id)
                    bundle.route_algorithm = self.router_type
                    self.delivered_bundles.append(bundle)
                    node.remove_bundle(bundle)
                    node.update_energy(tx_time, is_transmitting=True)
                    next_hop_contact.residual_capacity_bits -= bundle.size_bytes * 8

                    self.routing_decisions.append({
                        "time": t, "bundle_id": bundle.bundle_id,
                        "from": node_id, "to": next_node_id,
                        "algorithm": self.router_type,
                        "bundle_size_mb": bundle.size_mb,
                        "priority": bundle.priority,
                        "relay_soc": 1.0,
                    })

                # Forward to relay
                elif next_node.can_store(bundle.size_bytes):
                    node.remove_bundle(bundle)
                    next_node.store_bundle(bundle)
                    bundle.hops.append(next_node_id)
                    node.update_energy(tx_time, is_transmitting=True)
                    next_node.update_energy(tx_time, is_receiving=True)
                    next_hop_contact.residual_capacity_bits -= bundle.size_bytes * 8

                    self.routing_decisions.append({
                        "time": t, "bundle_id": bundle.bundle_id,
                        "from": node_id, "to": next_node_id,
                        "algorithm": self.router_type,
                        "bundle_size_mb": bundle.size_mb,
                        "priority": bundle.priority,
                        "relay_soc": next_node.soc if not next_node.is_ground else 1.0,
                    })

                else:
                    # Buffer overflow at relay
                    if self.router_type == "CGR":
                        bundle.is_dropped = True
                        bundle.drop_reason = "relay_buffer_overflow"
                        self.dropped_bundles.append(bundle)
                        node.remove_bundle(bundle)
                    # ECGR would have avoided this route

    def _update_node_states(self, t: float, dt: float):
        """Update energy and eclipse states for all nodes."""
        # Update SmallSat eclipse state
        self.nodes[SMALLSAT].in_eclipse = self._is_in_eclipse(t)

        # Update energy for all non-ground nodes
        for node_id in [ROVER, SMALLSAT, MRO]:
            self.nodes[node_id].update_energy(dt)

    def _log_metrics(self, t: float):
        """Record metrics at current time step."""
        for node in self.nodes.values():
            node.log_state(t)

        total_created = len([b for b in self.bundles if b.creation_time <= t])
        total_delivered = len(self.delivered_bundles)
        total_dropped = len(self.dropped_bundles)

        self.metrics_log.append({
            "time": t,
            "bundles_created": total_created,
            "bundles_delivered": total_delivered,
            "bundles_dropped": total_dropped,
            "delivery_ratio": total_delivered / max(total_created, 1),
            "smallsat_soc": self.nodes[SMALLSAT].soc,
            "smallsat_buffer_util": self.nodes[SMALLSAT].buffer_utilization,
            "mro_soc": self.nodes[MRO].soc,
            "mro_buffer_util": self.nodes[MRO].buffer_utilization,
            "rover_soc": self.nodes[ROVER].soc,
        })

    def run(self) -> dict:
        """
        Execute the simulation.

        Returns
        -------
        dict : Summary results including all metrics.
        """
        print(f"\n{'='*60}")
        print(f"  Running {self.router_type} Simulation")
        print(f"  Duration: {SIM_DURATION}s | Time Step: {TIME_STEP}s")
        print(f"  Bundles: {len(self.bundles)} | Contacts: {len(self.contacts)}")
        print(f"{'='*60}")

        log_interval = SIM_DURATION // 10

        for t in np.arange(0, SIM_DURATION, TIME_STEP):
            # Progress reporting
            if int(t) % log_interval == 0 and t > 0:
                pct = t / SIM_DURATION * 100
                ss_soc = self.nodes[SMALLSAT].soc * 100
                delivered = len(self.delivered_bundles)
                print(f"  [{pct:5.1f}%] t={int(t):6d}s | "
                      f"Delivered: {delivered} | "
                      f"SmallSat SoC: {ss_soc:.1f}%")

            # Simulation steps
            self._update_node_states(t, TIME_STEP)
            self._inject_bundles(t)
            self._forward_bundles(t)

            # Log metrics every 60 seconds
            if int(t) % 60 == 0:
                self._log_metrics(t)

        # Final metrics
        results = self._compile_results()
        self._print_summary(results)
        return results

    def _compile_results(self) -> dict:
        """Compile final simulation results."""
        total_bundles = len(self.bundles)
        delivered = len(self.delivered_bundles)
        dropped = len(self.dropped_bundles)
        in_transit = total_bundles - delivered - dropped

        # Latency statistics
        latencies = [b.latency for b in self.delivered_bundles if b.latency > 0]
        avg_latency = np.mean(latencies) if latencies else 0.0
        median_latency = np.median(latencies) if latencies else 0.0
        p95_latency = np.percentile(latencies, 95) if latencies else 0.0

        # Per-priority statistics
        priority_stats = {}
        for p in [1, 2, 3]:
            p_bundles = [b for b in self.bundles if b.priority == p]
            p_delivered = [b for b in self.delivered_bundles if b.priority == p]
            p_dropped = [b for b in self.dropped_bundles if b.priority == p]
            p_latencies = [b.latency for b in p_delivered if b.latency > 0]

            priority_stats[p] = {
                "total": len(p_bundles),
                "delivered": len(p_delivered),
                "dropped": len(p_dropped),
                "delivery_ratio": len(p_delivered) / max(len(p_bundles), 1),
                "avg_latency": float(np.mean(p_latencies)) if p_latencies else 0.0,
            }

        # Drop reason analysis
        drop_reasons = {}
        for b in self.dropped_bundles:
            reason = b.drop_reason
            drop_reasons[reason] = drop_reasons.get(reason, 0) + 1

        # SmallSat energy statistics
        ss_energy = self.nodes[SMALLSAT].energy_log
        ss_min_soc = min(e[2] for e in ss_energy) if ss_energy else 0.0
        ss_avg_soc = np.mean([e[2] for e in ss_energy]) if ss_energy else 0.0
        ss_below_20 = sum(1 for e in ss_energy if e[2] < 0.20) / max(len(ss_energy), 1)

        # Data volume statistics
        total_data_generated_mb = sum(b.size_mb for b in self.bundles)
        total_data_delivered_mb = sum(b.size_mb for b in self.delivered_bundles)

        # Routing through SmallSat
        ss_routed = len([d for d in self.routing_decisions
                        if d["to"] == SMALLSAT or d["from"] == SMALLSAT])

        return {
            "algorithm": self.router_type,
            "total_bundles": total_bundles,
            "delivered": delivered,
            "dropped": dropped,
            "in_transit": in_transit,
            "delivery_ratio": delivered / max(total_bundles, 1),
            "avg_latency_s": avg_latency,
            "median_latency_s": median_latency,
            "p95_latency_s": p95_latency,
            "priority_stats": priority_stats,
            "drop_reasons": drop_reasons,
            "smallsat_min_soc": ss_min_soc,
            "smallsat_avg_soc": ss_avg_soc,
            "smallsat_below_20pct_fraction": ss_below_20,
            "total_data_generated_mb": total_data_generated_mb,
            "total_data_delivered_mb": total_data_delivered_mb,
            "smallsat_routes": ss_routed,
            "total_routing_decisions": len(self.routing_decisions),
            "metrics_timeseries": self.metrics_log,
            "smallsat_energy_log": [(t, e, s) for t, e, s in self.nodes[SMALLSAT].energy_log],
            "smallsat_buffer_log": [(t, u, r) for t, u, r in self.nodes[SMALLSAT].buffer_log],
            "mro_energy_log": [(t, e, s) for t, e, s in self.nodes[MRO].energy_log],
            "mro_buffer_log": [(t, u, r) for t, u, r in self.nodes[MRO].buffer_log],
            "routing_decisions": self.routing_decisions,
        }

    def _print_summary(self, results: dict):
        """Print a formatted summary of simulation results."""
        print(f"\n{'─'*50}")
        print(f"  {results['algorithm']} Results Summary")
        print(f"{'─'*50}")
        print(f"  Bundle Delivery Ratio:   {results['delivery_ratio']*100:.1f}%")
        print(f"  Delivered / Total:       {results['delivered']}/{results['total_bundles']}")
        print(f"  Dropped:                 {results['dropped']}")
        print(f"  In Transit:              {results['in_transit']}")
        print(f"  Avg Latency:             {results['avg_latency_s']:.1f}s")
        print(f"  P95 Latency:             {results['p95_latency_s']:.1f}s")
        print(f"  SmallSat Min SoC:        {results['smallsat_min_soc']*100:.1f}%")
        print(f"  SmallSat Avg SoC:        {results['smallsat_avg_soc']*100:.1f}%")
        print(f"  SmallSat <20% Fraction:  {results['smallsat_below_20pct_fraction']*100:.1f}%")
        print(f"  Data Delivered:          {results['total_data_delivered_mb']:.1f} MB")
        if results['drop_reasons']:
            print(f"  Drop Reasons:")
            for reason, count in results['drop_reasons'].items():
                print(f"    - {reason}: {count}")
        print(f"{'─'*50}")
