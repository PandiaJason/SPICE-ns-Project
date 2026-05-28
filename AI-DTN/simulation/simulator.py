"""
Main simulation engine for ML-CGR evaluation.

Implements a discrete-time event-driven simulator that models the complete
DTN bundle forwarding process including energy dynamics, buffer management,
eclipse transitions, bundle fragmentation, and ML-based link quality
observation feedback loops.
"""

import copy
import json
import os
import numpy as np
from typing import List, Dict, Optional
from simulation.config import (
    SIM_DURATION, TIME_STEP, RANDOM_SEED,
    ROVER, SMALLSAT, MRO, DSN, NODE_NAMES,
    TRAFFIC_PROFILES, RESULTS_DIR, ECLIPSE_FRACTION,
    FRAG_TRIGGER_SIZE_MB
)
from simulation.models import Contact, Node, Bundle, Route
from simulation.routing import CGRRouter, MLCGRRouter, find_all_routes
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
    Discrete-time DTN simulator for ML-CGR evaluation.

    Simulates bundle forwarding through a contact-graph-routed
    deep-space network with energy and buffer constraints, ML-driven
    link quality prediction, and proactive bundle fragmentation.
    """

    def __init__(self, router_type: str = "CGR", seed: int = RANDOM_SEED):
        self.router_type = router_type
        self.seed = seed
        self.rng = np.random.default_rng(seed)

        # Initialize SPICE for both routers
        self.spice = SyntheticSPICE(seed=seed)
        self.eclipse_windows = self.spice.compute_eclipse_windows('smallsat')

        # Initialize router
        if router_type == "ML-CGR":
            self.router = MLCGRRouter(spice=self.spice, seed=seed)
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

        # Fragment tracking
        self.fragmented_bundles: List[Bundle] = []  # Original bundles that were fragmented
        self.all_fragments: List[Bundle] = []       # All generated fragments

        # ML-specific logging
        self.lqi_predictions: List[dict] = []
        self.fragmentation_events: List[dict] = []

        # Metrics logging
        self.metrics_log: List[dict] = []
        self.routing_decisions: List[dict] = []

    def setup(self, contacts: List[Contact], bundles: List[Bundle]):
        """Configure simulation with contact plan and traffic."""
        self.contacts = [copy.deepcopy(c) for c in contacts]
        self.bundles = [copy.deepcopy(b) for b in bundles]
        self.delivered_bundles = []
        self.dropped_bundles = []
        self.fragmented_bundles = []
        self.all_fragments = []
        self.lqi_predictions = []
        self.fragmentation_events = []
        self.metrics_log = []
        self.routing_decisions = []

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

    def _inject_fragment(self, fragment: Bundle, t: float):
        """Inject a fragment bundle directly into its source node queue."""
        node = self.nodes[fragment.source]
        if node.can_store(fragment.size_bytes):
            node.store_bundle(fragment)
            self.bundles.append(fragment)
            self.all_fragments.append(fragment)
        else:
            fragment.is_dropped = True
            fragment.drop_reason = "source_buffer_full_fragment"
            self.dropped_bundles.append(fragment)

    def _handle_fragmentation(self, bundle: Bundle, route: Route,
                               t: float) -> Optional[List[Bundle]]:
        """
        Determine if bundle should be fragmented and generate fragments.

        Returns
        -------
        list of Bundle or None : Generated fragments, or None if no fragmentation
        """
        if self.router_type != "ML-CGR":
            return None
        if bundle.is_fragment:
            return None

        predicted_lqi = bundle.predicted_lqi
        frag_size = self.router.should_fragment(bundle, predicted_lqi, t)

        if frag_size is None:
            return None

        # Generate fragments
        fragments = self.router.fragment_bundle(bundle, frag_size, t)
        if len(fragments) <= 1:
            return None

        # Mark original bundle as fragmented (will be replaced)
        bundle.is_dropped = True
        bundle.drop_reason = "fragmented"
        self.fragmented_bundles.append(bundle)

        self.fragmentation_events.append({
            "time": t,
            "bundle_id": bundle.bundle_id,
            "original_size_mb": bundle.size_mb,
            "n_fragments": len(fragments),
            "frag_size_mb": frag_size,
            "predicted_lqi": predicted_lqi,
        })

        self.lqi_predictions.append({
            "time": t,
            "bundle_id": bundle.bundle_id,
            "predicted_lqi": predicted_lqi,
            "fragment_triggered": True,
            "n_fragments": len(fragments),
        })

        return fragments

    def _record_lqi_observation(self, contact: Contact, actual_bits_sent: float,
                                 t: float):
        """
        Compute observed LQI and feed it to the ML predictor.

        LQI = actual_bits_sent / scheduled_capacity_bits
        """
        if self.router_type != "ML-CGR":
            return

        scheduled_bits = contact.data_rate_bps * contact.duration
        observed_lqi = float(np.clip(
            actual_bits_sent / max(scheduled_bits, 1.0), 0.05, 1.0
        ))

        relay_node = self.nodes.get(contact.source)
        self.router.add_lqi_observation(contact, observed_lqi, relay_node, t)

    def _forward_bundles(self, t: float):
        """Attempt to forward queued bundles at each node."""
        active_contacts = self._get_active_contacts(t)

        for node_id in [ROVER, SMALLSAT, MRO]:
            node = self.nodes[node_id]
            if not node.bundle_queue:
                continue

            queue = sorted(node.bundle_queue, key=lambda b: b.priority)

            for bundle in list(queue):
                if bundle.is_delivered or bundle.is_dropped:
                    continue

                outgoing = [c for c in active_contacts if c.source == node_id]
                if not outgoing:
                    continue

                routes = find_all_routes(
                    self.contacts, node_id, bundle.destination, t
                )
                if not routes:
                    continue

                selected = self.router.select_route(
                    routes, bundle, self.nodes, t
                )
                if selected is None:
                    continue

                if not selected.hops:
                    continue
                next_hop_contact = selected.hops[0]

                if not next_hop_contact.is_active(t):
                    continue

                next_node_id = next_hop_contact.dest
                next_node = self.nodes[next_node_id]
                tx_time = bundle.size_bytes * 8 / next_hop_contact.data_rate_bps

                # ---- Proactive Fragmentation (ML-CGR only) ----
                if self.router_type == "ML-CGR" and not bundle.is_fragment:
                    fragments = self._handle_fragmentation(bundle, selected, t)
                    if fragments is not None:
                        node.remove_bundle(bundle)
                        for frag in fragments:
                            self._inject_fragment(frag, t)
                        continue  # Restart with fragments

                # ---- CGR: blind forwarding; energy check ----
                if not node.is_ground and not node.can_transmit(tx_time):
                    if self.router_type == "CGR":
                        node.energy_wh = 0.0
                        bundle.is_dropped = True
                        bundle.drop_reason = "tx_energy_exhausted"
                        self.dropped_bundles.append(bundle)
                        node.remove_bundle(bundle)
                        # Record poor LQI observation from failed transmission
                        self._record_lqi_observation(
                            next_hop_contact, 0.0, t)
                        continue
                    else:
                        continue

                # ---- Deliver to DSN ----
                if next_node_id == DSN:
                    bundle.is_delivered = True
                    bundle.delivery_time = t + tx_time + next_hop_contact.owlt_s
                    bundle.hops.append(next_node_id)
                    bundle.route_algorithm = self.router_type
                    self.delivered_bundles.append(bundle)
                    node.remove_bundle(bundle)
                    node.update_energy(tx_time, is_transmitting=True)
                    actual_bits = bundle.size_bytes * 8
                    next_hop_contact.residual_capacity_bits -= actual_bits
                    self._record_lqi_observation(next_hop_contact, actual_bits, t)

                    self.routing_decisions.append({
                        "time": t,
                        "bundle_id": bundle.bundle_id,
                        "from": node_id,
                        "to": next_node_id,
                        "algorithm": self.router_type,
                        "bundle_size_mb": bundle.size_mb,
                        "priority": bundle.priority,
                        "relay_soc": 1.0,
                        "predicted_lqi": bundle.predicted_lqi,
                        "is_fragment": bundle.is_fragment,
                    })

                # ---- Forward to relay ----
                elif next_node.can_store(bundle.size_bytes):
                    node.remove_bundle(bundle)
                    next_node.store_bundle(bundle)
                    bundle.hops.append(next_node_id)
                    node.update_energy(tx_time, is_transmitting=True)
                    next_node.update_energy(tx_time, is_receiving=True)
                    actual_bits = bundle.size_bytes * 8
                    next_hop_contact.residual_capacity_bits -= actual_bits
                    self._record_lqi_observation(next_hop_contact, actual_bits, t)

                    self.routing_decisions.append({
                        "time": t,
                        "bundle_id": bundle.bundle_id,
                        "from": node_id,
                        "to": next_node_id,
                        "algorithm": self.router_type,
                        "bundle_size_mb": bundle.size_mb,
                        "priority": bundle.priority,
                        "relay_soc": next_node.soc if not next_node.is_ground else 1.0,
                        "predicted_lqi": bundle.predicted_lqi,
                        "is_fragment": bundle.is_fragment,
                    })

                else:
                    # Buffer overflow at relay
                    if self.router_type == "CGR":
                        bundle.is_dropped = True
                        bundle.drop_reason = "relay_buffer_overflow"
                        self.dropped_bundles.append(bundle)
                        node.remove_bundle(bundle)
                        self._record_lqi_observation(
                            next_hop_contact, 0.0, t)

    def _update_node_states(self, t: float, dt: float):
        """Update energy and eclipse states for all nodes."""
        self.nodes[SMALLSAT].in_eclipse = self._is_in_eclipse(t)
        for node_id in [ROVER, SMALLSAT, MRO]:
            self.nodes[node_id].update_energy(dt)

    def _log_metrics(self, t: float):
        """Record metrics at current time step."""
        for node in self.nodes.values():
            node.log_state(t)

        total_created = len([b for b in self.bundles if b.creation_time <= t])
        total_delivered = len(self.delivered_bundles)
        total_dropped = len([b for b in self.dropped_bundles
                             if b.drop_reason != "fragmented"])
        n_fragments = len(self.all_fragments)

        self.metrics_log.append({
            "time": t,
            "bundles_created": total_created,
            "bundles_delivered": total_delivered,
            "bundles_dropped": total_dropped,
            "fragments_created": n_fragments,
            "delivery_ratio": total_delivered / max(total_created, 1),
            "smallsat_soc": self.nodes[SMALLSAT].soc,
            "smallsat_buffer_util": self.nodes[SMALLSAT].buffer_utilization,
            "mro_soc": self.nodes[MRO].soc,
            "mro_buffer_util": self.nodes[MRO].buffer_utilization,
            "rover_soc": self.nodes[ROVER].soc,
        })

    def run(self) -> dict:
        """Execute the simulation. Returns summary results dict."""
        print(f"\n{'='*60}")
        print(f"  Running {self.router_type} Simulation")
        print(f"  Duration: {SIM_DURATION}s | Time Step: {TIME_STEP}s")
        print(f"  Bundles: {len(self.bundles)} | Contacts: {len(self.contacts)}")
        print(f"{'='*60}")

        log_interval = SIM_DURATION // 10

        for t in np.arange(0, SIM_DURATION, TIME_STEP):
            if int(t) % log_interval == 0 and t > 0:
                pct = t / SIM_DURATION * 100
                ss_soc = self.nodes[SMALLSAT].soc * 100
                delivered = len(self.delivered_bundles)
                n_frags = len(self.all_fragments)
                print(f"  [{pct:5.1f}%] t={int(t):6d}s | "
                      f"Delivered: {delivered} | "
                      f"Fragments: {n_frags} | "
                      f"SmallSat SoC: {ss_soc:.1f}%")

            self._update_node_states(t, TIME_STEP)
            self._inject_bundles(t)
            self._forward_bundles(t)

            if int(t) % 60 == 0:
                self._log_metrics(t)

        results = self._compile_results()
        self._print_summary(results)
        return results

    def _compile_results(self) -> dict:
        """Compile final simulation results."""
        # Exclude "fragmented" drops from count (they are logical replacements)
        real_drops = [b for b in self.dropped_bundles
                      if b.drop_reason != "fragmented"]

        # Original (non-fragment) bundles
        original_bundles = [b for b in self.bundles if not b.is_fragment]
        total_bundles = len(original_bundles)

        # For fragmented original bundles: count as delivered if ALL fragments delivered
        delivered_frag_ids = {b.parent_bundle_id for b in self.delivered_bundles
                              if b.is_fragment}
        all_frag_ids = {b.parent_bundle_id for b in self.all_fragments}
        # Fragmented parents delivered = all their fragments got through
        parents_with_all_frags_delivered = set()
        for pid in all_frag_ids:
            pid_frags = [b for b in self.all_fragments if b.parent_bundle_id == pid]
            pid_delivered = [b for b in self.delivered_bundles
                             if b.is_fragment and b.parent_bundle_id == pid]
            if len(pid_delivered) == len(pid_frags) and len(pid_frags) > 0:
                parents_with_all_frags_delivered.add(pid)

        # Bundles delivered = non-fragment delivered + fragmented parents fully reassembled
        direct_delivered = [b for b in self.delivered_bundles if not b.is_fragment]
        fragmented_parent_delivered = [b for b in self.fragmented_bundles
                                       if b.bundle_id in parents_with_all_frags_delivered]
        delivered = len(direct_delivered) + len(fragmented_parent_delivered)

        dropped = len([b for b in real_drops if not b.is_fragment])
        in_transit = total_bundles - delivered - dropped

        # Count fragments separately
        n_frag_events = len(self.fragmented_bundles)
        n_fragments_total = len(self.all_fragments)
        frag_delivered = len([b for b in self.delivered_bundles if b.is_fragment])

        # Latency statistics — direct + reassembled (use max fragment delivery time)
        direct_latencies = [b.latency for b in direct_delivered if b.latency > 0]
        frag_latencies = []
        for parent in fragmented_parent_delivered:
            frags = [b for b in self.delivered_bundles
                     if b.is_fragment and b.parent_bundle_id == parent.bundle_id]
            if frags:
                max_delivery = max(b.delivery_time for b in frags)
                frag_latencies.append(max_delivery - parent.creation_time)
        latencies = direct_latencies + frag_latencies
        avg_latency = float(np.mean(latencies)) if latencies else 0.0
        median_latency = float(np.median(latencies)) if latencies else 0.0
        p95_latency = float(np.percentile(latencies, 95)) if latencies else 0.0

        # Per-priority statistics
        priority_stats = {}
        for p in [1, 2, 3]:
            p_bundles = [b for b in original_bundles if b.priority == p]
            p_direct_del = [b for b in direct_delivered if b.priority == p]
            p_frag_del = [b for b in fragmented_parent_delivered if b.priority == p]
            p_dropped = [b for b in real_drops
                        if b.priority == p and not b.is_fragment]
            p_delivered = p_direct_del + p_frag_del
            p_latencies = ([b.latency for b in p_direct_del if b.latency > 0]
                          + [max(b.delivery_time for b in
                                [x for x in self.delivered_bundles
                                 if x.is_fragment and x.parent_bundle_id == par.bundle_id])
                             - par.creation_time
                             for par in p_frag_del
                             if any(x.is_fragment and x.parent_bundle_id == par.bundle_id
                                    for x in self.delivered_bundles)])

            priority_stats[p] = {
                "total": len(p_bundles),
                "delivered": len(p_delivered),
                "dropped": len(p_dropped),
                "delivery_ratio": len(p_delivered) / max(len(p_bundles), 1),
                "avg_latency": float(np.mean(p_latencies)) if p_latencies else 0.0,
            }

        # Drop reason analysis
        drop_reasons = {}
        for b in real_drops:
            if not b.is_fragment:
                reason = b.drop_reason
                drop_reasons[reason] = drop_reasons.get(reason, 0) + 1

        # SmallSat energy statistics
        ss_energy = self.nodes[SMALLSAT].energy_log
        ss_min_soc = min(e[2] for e in ss_energy) if ss_energy else 0.0
        ss_avg_soc = np.mean([e[2] for e in ss_energy]) if ss_energy else 0.0
        ss_below_20 = sum(1 for e in ss_energy if e[2] < 0.20) / max(len(ss_energy), 1)

        # Data volume statistics: count direct + fragment-reassembled
        total_data_generated_mb = sum(b.size_mb for b in original_bundles)
        total_data_delivered_mb = (
            sum(b.size_mb for b in direct_delivered)
            + sum(b.size_mb for b in fragmented_parent_delivered)
        )

        # Routing through SmallSat
        ss_routed = len([d for d in self.routing_decisions
                        if d["to"] == SMALLSAT or d["from"] == SMALLSAT])

        # ML-specific statistics
        avg_predicted_lqi = np.mean([d["predicted_lqi"]
                                     for d in self.routing_decisions]) if self.routing_decisions else 1.0
        frag_events = self.fragmentation_events

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
            # Fragmentation statistics
            "n_fragmentation_events": n_frag_events,
            "n_fragments_total": n_fragments_total,
            "n_fragments_delivered": frag_delivered,
            "fragmentation_events": frag_events,
            # LQI statistics
            "avg_predicted_lqi": float(avg_predicted_lqi),
            "lqi_predictions": self.lqi_predictions,
            # Timeseries
            "metrics_timeseries": self.metrics_log,
            "smallsat_energy_log": [(t, e, s) for t, e, s in self.nodes[SMALLSAT].energy_log],
            "smallsat_buffer_log": [(t, u, r) for t, u, r in self.nodes[SMALLSAT].buffer_log],
            "mro_energy_log": [(t, e, s) for t, e, s in self.nodes[MRO].energy_log],
            "mro_buffer_log": [(t, u, r) for t, u, r in self.nodes[MRO].buffer_log],
            "routing_decisions": self.routing_decisions,
        }

    def _print_summary(self, results: dict):
        """Print a formatted summary of simulation results."""
        print(f"\n{'─'*55}")
        print(f"  {results['algorithm']} Results Summary")
        print(f"{'─'*55}")
        print(f"  Bundle Delivery Ratio:   {results['delivery_ratio']*100:.1f}%")
        print(f"  Delivered / Total:       {results['delivered']}/{results['total_bundles']}")
        print(f"  Dropped:                 {results['dropped']}")
        print(f"  In Transit:              {results['in_transit']}")
        print(f"  Avg Latency:             {results['avg_latency_s']:.1f}s")
        print(f"  P95 Latency:             {results['p95_latency_s']:.1f}s")
        print(f"  SmallSat Min SoC:        {results['smallsat_min_soc']*100:.1f}%")
        print(f"  SmallSat Avg SoC:        {results['smallsat_avg_soc']*100:.1f}%")
        print(f"  Data Delivered:          {results['total_data_delivered_mb']:.1f} MB")
        print(f"  Avg Predicted LQI:       {results['avg_predicted_lqi']:.3f}")
        print(f"  Fragmentation Events:    {results['n_fragmentation_events']}")
        print(f"  Total Fragments:         {results['n_fragments_total']}")
        if results['drop_reasons']:
            print(f"  Drop Reasons:")
            for reason, count in results['drop_reasons'].items():
                print(f"    - {reason}: {count}")
        print(f"{'─'*55}")
