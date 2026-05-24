"""
Routing algorithms for Delay-Tolerant Networking.

Implements:
  1. Standard Contact Graph Routing (CGR) - Earliest Delivery Time
  2. Energy and Capacity-Aware CGR (ECGR) - Multi-attribute cost optimization

References:
  - Burleigh, S., "Contact Graph Routing", IETF draft-burleigh-dtnrg-cgr, 2010.
  - Fraire, J.A., et al., "CGR Enhancement for DTN", IEEE TASE, 2021.
"""

import heapq
from typing import List, Optional, Dict
from simulation.models import Contact, Node, Bundle, Route
from simulation.config import (
    DSN, ALPHA_BASE, BETA_BASE, GAMMA_BASE,
    PRIORITY_WEIGHTS, ENERGY_CRITICAL_THRESHOLD,
    ENERGY_WARNING_THRESHOLD, BUFFER_WARNING_THRESHOLD
)


# =============================================================================
# Contact Graph Construction
# =============================================================================
def build_contact_graph(contacts: List[Contact], current_time: float) -> Dict:
    """
    Build a contact graph from the contact plan, filtering for future contacts.

    Parameters
    ----------
    contacts : list of Contact
        Full contact plan.
    current_time : float
        Current simulation time; only contacts starting after this are used.

    Returns
    -------
    dict : adjacency list { source_node: [Contact, ...] }
    """
    graph = {}
    for c in contacts:
        if c.end_time > current_time and c.residual_capacity_bits > 0:
            if c.source not in graph:
                graph[c.source] = []
            graph[c.source].append(c)
    return graph


def find_all_routes(contacts: List[Contact], source: int, destination: int,
                    current_time: float, max_hops: int = 5) -> List[Route]:
    """
    Find all feasible routes from source to destination using modified Dijkstra.

    Uses earliest arrival time at each node as the optimization criterion.
    Implements Yen's k-shortest paths variant for finding multiple routes.

    Parameters
    ----------
    contacts : list of Contact
    source : int
    destination : int
    current_time : float
    max_hops : int

    Returns
    -------
    list of Route
    """
    graph = build_contact_graph(contacts, current_time)
    routes = []
    _counter = 0  # Monotonic tiebreaker for heap ordering

    # Priority queue: (arrival_time, counter, current_node, path_contacts, visited)
    initial_state = (current_time, _counter, source, [], frozenset([source]))
    pq = [initial_state]
    best_arrival = {}  # Track best arrival at each node to prune

    while pq and len(routes) < 10:  # Limit to 10 candidate routes
        arr_time, _, node, path, visited = heapq.heappop(pq)

        if node == destination:
            routes.append(Route(hops=list(path), source=source,
                               destination=destination))
            continue

        if len(path) >= max_hops:
            continue

        # Prune if we've found a better path to this node
        state_key = (node, len(path))
        if state_key in best_arrival and best_arrival[state_key] <= arr_time:
            continue
        best_arrival[state_key] = arr_time

        if node not in graph:
            continue

        for contact in graph[node]:
            next_node = contact.dest
            if next_node in visited:
                continue

            # Contact must start after we arrive at this node
            if contact.start_time < arr_time:
                # Can still use if contact hasn't ended
                if contact.end_time <= arr_time:
                    continue
                # Partial use
                effective_start = arr_time
            else:
                effective_start = contact.start_time

            next_arrival = contact.end_time + contact.owlt_s
            new_visited = visited | frozenset([next_node])
            new_path = path + [contact]

            _counter += 1
            heapq.heappush(pq, (next_arrival, _counter, next_node, new_path, new_visited))

    return routes


# =============================================================================
# Standard CGR: Earliest Delivery Time
# =============================================================================
class CGRRouter:
    """
    Standard Contact Graph Routing.

    Selects routes based on earliest delivery time (minimum delay).
    This is the baseline algorithm as described in RFC 9171 and
    Burleigh's CGR specification.
    """

    def __init__(self):
        self.name = "CGR"

    def select_route(self, routes: List[Route], bundle: Bundle,
                     nodes: Dict[int, Node], current_time: float) -> Optional[Route]:
        """
        Select the best route based on earliest arrival time.

        Parameters
        ----------
        routes : list of Route
        bundle : Bundle
        nodes : dict of Node
        current_time : float

        Returns
        -------
        Route or None
        """
        if not routes:
            return None

        # Filter routes that have sufficient capacity and prevent routing loops
        feasible = []
        for route in routes:
            if not route.hops:
                continue
            # Loop prevention: do not route to a node we have already visited
            if route.hops[0].dest in bundle.hops:
                continue
            # Check if all hops have enough residual capacity
            sufficient = True
            for hop in route.hops:
                if hop.residual_capacity_bytes() < bundle.size_bytes:
                    sufficient = False
                    break
            if sufficient:
                feasible.append(route)

        if not feasible:
            return None

        # Select route with earliest arrival time
        return min(feasible, key=lambda r: r.arrival_time)

    def compute_cost(self, route: Route, bundle: Bundle,
                     nodes: Dict[int, Node]) -> float:
        """Cost = arrival time (for comparison logging)."""
        return route.arrival_time


# =============================================================================
# ECGR: Energy and Capacity-Aware CGR
# =============================================================================
class ECGRRouter:
    """
    Energy and Capacity-Aware Contact Graph Routing (ECGR).

    Extends standard CGR with a multi-attribute cost function that
    considers relay node energy state and buffer availability:

        Cost = α·D_norm + β·(1/E_min) + γ·(S/B_min)

    where:
        D_norm  = normalized end-to-end delay
        E_min   = minimum energy ratio among relay nodes
        S/B_min = maximum bundle-to-buffer ratio among relay nodes
        α, β, γ = dynamic weights based on data priority and network state

    The dynamic weight adaptation responds to:
        - Bundle priority (critical vs. housekeeping)
        - Network-wide energy state (boosted when batteries are low)
        - Buffer congestion levels
    """

    def __init__(self):
        self.name = "ECGR"

    def compute_dynamic_weights(self, bundle: Bundle,
                                 nodes: Dict[int, Node],
                                 route: Route) -> tuple:
        """
        Compute dynamic α, β, γ weights based on bundle priority
        and current network state.

        Returns
        -------
        tuple : (alpha, beta, gamma)
        """
        pw = PRIORITY_WEIGHTS.get(bundle.priority,
                                   PRIORITY_WEIGHTS[2])
        alpha = ALPHA_BASE * pw["alpha"]
        beta = BETA_BASE * pw["beta"]
        gamma = GAMMA_BASE * pw["gamma"]

        # Adaptive boost based on relay node states
        relay_nodes = route.relay_nodes
        if relay_nodes:
            min_soc = min(nodes[n].soc for n in relay_nodes
                         if n in nodes)
            max_buf = max(nodes[n].buffer_utilization for n in relay_nodes
                         if n in nodes)

            # Energy-aware adaptation
            if min_soc < ENERGY_CRITICAL_THRESHOLD:
                beta *= 4.0     # Strong penalty for critically low energy
            elif min_soc < ENERGY_WARNING_THRESHOLD:
                beta *= 2.0     # Moderate penalty

            # Buffer-aware adaptation
            if max_buf > BUFFER_WARNING_THRESHOLD:
                gamma *= 3.0    # Strong penalty for congested buffers

        return alpha, beta, gamma

    def compute_cost(self, route: Route, bundle: Bundle,
                     nodes: Dict[int, Node],
                     normalization: dict = None,
                     current_time: float = 0.0) -> float:
        """
        Compute the multi-attribute ECGR cost for a route.

        Parameters
        ----------
        route : Route
        bundle : Bundle
        nodes : dict of Node
        normalization : dict with 'max_delay' for normalizing delay term

        Returns
        -------
        float : computed cost value
        """
        alpha, beta, gamma = self.compute_dynamic_weights(bundle, nodes, route)

        # --- Delay term ---
        delay = max(route.arrival_time - current_time, 0.0)
        max_delay = normalization.get("max_delay", 86400.0) if normalization else 86400.0
        delay_norm = delay / max(max_delay, 1.0)

        # --- Energy term ---
        relay_nodes = route.relay_nodes
        if relay_nodes:
            energy_ratios = [nodes[n].soc for n in relay_nodes if n in nodes]
            min_energy = min(energy_ratios) if energy_ratios else 1.0
        else:
            min_energy = 1.0
        # Avoid division by zero
        energy_cost = 1.0 / max(min_energy, 0.01)

        # --- Buffer term ---
        if relay_nodes:
            buffer_ratios = []
            for n in relay_nodes:
                if n in nodes:
                    avail = nodes[n].available_buffer_bytes
                    ratio = bundle.size_bytes / max(avail, 1.0)
                    buffer_ratios.append(ratio)
            max_buffer_ratio = max(buffer_ratios) if buffer_ratios else 0.0
        else:
            max_buffer_ratio = 0.0

        cost = alpha * delay_norm + beta * energy_cost + gamma * max_buffer_ratio
        return cost

    def select_route(self, routes: List[Route], bundle: Bundle,
                     nodes: Dict[int, Node],
                     current_time: float) -> Optional[Route]:
        """
        Select the best route based on multi-attribute ECGR cost.

        Parameters
        ----------
        routes : list of Route
        bundle : Bundle
        nodes : dict of Node
        current_time : float

        Returns
        -------
        Route or None
        """
        if not routes:
            return None

        # Filter for feasibility (capacity + energy + buffer) and prevent routing loops
        feasible = []
        for route in routes:
            if not route.hops:
                continue
            # Loop prevention: do not route to a node we have already visited
            if route.hops[0].dest in bundle.hops:
                continue

            # Check capacity
            capacity_ok = all(
                hop.residual_capacity_bytes() >= bundle.size_bytes
                for hop in route.hops
            )
            if not capacity_ok:
                continue

            # Check relay buffer availability
            buffer_ok = True
            for n_id in route.relay_nodes:
                if n_id in nodes and not nodes[n_id].can_store(bundle.size_bytes):
                    buffer_ok = False
                    break
            if not buffer_ok:
                continue

            # Check relay energy (ECGR-specific: won't route through dead nodes)
            energy_ok = True
            for n_id in route.relay_nodes:
                if n_id in nodes:
                    # Estimate transmission time
                    tx_time = bundle.size_bytes * 8 / route.bottleneck_rate
                    if not nodes[n_id].can_transmit(tx_time):
                        energy_ok = False
                        break
            if not energy_ok:
                continue

            feasible.append(route)

        if not feasible:
            return None

        # Compute normalization factors
        delays = [max(r.arrival_time - current_time, 0.0) for r in feasible]
        max_delay = max(delays) if delays else 86400.0
        normalization = {"max_delay": max_delay}

        # Select route with minimum ECGR cost
        best = min(feasible,
                   key=lambda r: self.compute_cost(r, bundle, nodes, normalization, current_time))
        return best


# =============================================================================
# P-ECGR: Predictive Energy and Capacity-Aware CGR
# =============================================================================
class PECGRRouter(ECGRRouter):
    """
    Predictive Energy and Capacity-Aware Contact Graph Routing (P-ECGR).

    Extends ECGR by predicting the future energy state of relay nodes at the
    actual time of transmission, rather than evaluating only the current state.
    This resolves the over-conservative routing decisions of standard ECGR,
    allowing it to route through a node if the battery will have recharged by
    the time transmission occurs.
    """

    def __init__(self):
        super().__init__()
        self.name = "P-ECGR"

    def predict_node_energy(self, node: Node, current_time: float, target_time: float) -> float:
        """Predict battery energy (Wh) at target_time based on charging/idle rates."""
        if node.is_ground:
            return node.battery_capacity_wh
        
        dt_hours = (target_time - current_time) / 3600.0
        if dt_hours <= 0:
            return node.energy_wh
            
        # Average power generation taking eclipse into account
        # Import ECLIPSE_FRACTION locally to avoid circular dependencies if any
        from simulation.config import ECLIPSE_FRACTION
        avg_gen = node.power_gen_w * (1.0 - ECLIPSE_FRACTION)
        net_power = avg_gen - node.idle_power_w
        
        predicted_energy = node.energy_wh + net_power * dt_hours
        return max(0.0, min(node.battery_capacity_wh, predicted_energy))

    def get_predicted_socs(self, routes_or_route, bundle: Bundle, nodes: Dict[int, Node], current_time: float) -> Dict[int, float]:
        """Get predicted SoC for each relay node at its transmission start time."""
        predicted_socs = {}
        routes = [routes_or_route] if isinstance(routes_or_route, Route) else routes_or_route
        for route in routes:
            for i, hop in enumerate(route.hops):
                n_id = hop.source
                if n_id != route.source and n_id in nodes:
                    pred_energy = self.predict_node_energy(nodes[n_id], current_time, hop.start_time)
                    pred_soc = pred_energy / nodes[n_id].battery_capacity_wh
                    if n_id not in predicted_socs or pred_soc < predicted_socs[n_id]:
                        predicted_socs[n_id] = pred_soc
        return predicted_socs

    def compute_dynamic_weights_pred(self, bundle: Bundle, nodes: Dict[int, Node], route: Route, predicted_socs: Dict[int, float]) -> tuple:
        pw = PRIORITY_WEIGHTS.get(bundle.priority, PRIORITY_WEIGHTS[2])
        alpha = ALPHA_BASE * pw["alpha"]
        beta = BETA_BASE * pw["beta"]
        gamma = GAMMA_BASE * pw["gamma"]

        relay_nodes = route.relay_nodes
        if relay_nodes:
            min_soc = min(predicted_socs.get(n, nodes[n].soc) for n in relay_nodes if n in nodes)
            max_buf = max(nodes[n].buffer_utilization for n in relay_nodes if n in nodes)

            if min_soc < ENERGY_CRITICAL_THRESHOLD:
                beta *= 4.0
            elif min_soc < ENERGY_WARNING_THRESHOLD:
                beta *= 2.0

            if max_buf > BUFFER_WARNING_THRESHOLD:
                gamma *= 3.0

        return alpha, beta, gamma

    def select_route(self, routes: List[Route], bundle: Bundle,
                     nodes: Dict[int, Node], current_time: float) -> Optional[Route]:
        if not routes:
            return None

        # Filter for feasibility (capacity + predicted energy + buffer) and prevent routing loops
        feasible = []
        for route in routes:
            if not route.hops:
                continue
            # Loop prevention: do not route to a node we have already visited
            if route.hops[0].dest in bundle.hops:
                continue

            # Check capacity
            capacity_ok = all(
                hop.residual_capacity_bytes() >= bundle.size_bytes
                for hop in route.hops
            )
            if not capacity_ok:
                continue

            # Check relay buffer availability
            buffer_ok = True
            for n_id in route.relay_nodes:
                if n_id in nodes and not nodes[n_id].can_store(bundle.size_bytes):
                    buffer_ok = False
                    break
            if not buffer_ok:
                continue

            # Check relay predicted energy
            energy_ok = True
            for i, hop in enumerate(route.hops):
                n_id = hop.source
                if n_id != route.source and n_id in nodes:
                    # Estimate transmission time
                    tx_time = bundle.size_bytes * 8 / route.bottleneck_rate
                    pred_energy = self.predict_node_energy(nodes[n_id], current_time, hop.start_time)
                    
                    # Need enough energy for transmission + idle power during transmission
                    energy_needed = (nodes[n_id].tx_power_w + nodes[n_id].idle_power_w) * (tx_time / 3600.0)
                    if pred_energy < energy_needed:
                        energy_ok = False
                        break
            if not energy_ok:
                continue

            feasible.append(route)

        if not feasible:
            return None

        # Predict SoCs for all relay nodes on feasible routes
        predicted_socs = self.get_predicted_socs(feasible, bundle, nodes, current_time)

        # Compute normalization factors
        delays = [max(r.arrival_time - current_time, 0.0) for r in feasible]
        max_delay = max(delays) if delays else 86400.0
        normalization = {"max_delay": max_delay, "predicted_socs": predicted_socs}

        # Select route with minimum P-ECGR cost
        best = min(feasible,
                   key=lambda r: self.compute_cost_pred(r, bundle, nodes, normalization, current_time))
        return best

    def compute_cost_pred(self, route: Route, bundle: Bundle,
                          nodes: Dict[int, Node],
                          normalization: dict, current_time: float) -> float:
        predicted_socs = normalization.get("predicted_socs", {})
        relay_nodes = route.relay_nodes
        
        # --- Delay term ---
        delay = max(route.arrival_time - current_time, 0.0)
        max_delay = normalization.get("max_delay", 86400.0)
        delay_norm = delay / max(max_delay, 1.0)

        # --- Energy term: deadband penalty based on predicted post-tx SoC ---
        energy_cost = 0.0
        for n_id in relay_nodes:
            if n_id in nodes:
                pred_soc = predicted_socs.get(n_id, nodes[n_id].soc)
                
                # Estimate transmission duration and resulting energy drop
                tx_time = bundle.size_bytes * 8 / route.bottleneck_rate
                energy_needed_wh = (nodes[n_id].tx_power_w + nodes[n_id].idle_power_w) * (tx_time / 3600.0)
                soc_drop = energy_needed_wh / nodes[n_id].battery_capacity_wh
                
                post_tx_soc = pred_soc - soc_drop
                
                # Apply penalty only if post_tx_soc is below warning threshold
                # This prevents constant penalization when in the safe zone
                if post_tx_soc < ENERGY_WARNING_THRESHOLD:
                    # Penalize based on how far below it goes
                    penalty = (ENERGY_WARNING_THRESHOLD - post_tx_soc) / ENERGY_WARNING_THRESHOLD
                    energy_cost += penalty * 10.0  # Strong penalty
                    
                # If it drops below critical threshold, apply massive penalty
                if post_tx_soc < ENERGY_CRITICAL_THRESHOLD:
                    energy_cost += 50.0

        # --- Buffer term ---
        if relay_nodes:
            buffer_ratios = []
            for n in relay_nodes:
                if n in nodes:
                    avail = nodes[n].available_buffer_bytes
                    ratio = bundle.size_bytes / max(avail, 1.0)
                    buffer_ratios.append(ratio)
            max_buffer_ratio = max(buffer_ratios) if buffer_ratios else 0.0
        else:
            max_buffer_ratio = 0.0

        # Retrieve priority weights
        pw = PRIORITY_WEIGHTS.get(bundle.priority, PRIORITY_WEIGHTS[2])
        alpha = ALPHA_BASE * pw["alpha"]
        beta = BETA_BASE * pw["beta"]
        gamma = GAMMA_BASE * pw["gamma"]

        cost = alpha * delay_norm + beta * energy_cost + gamma * max_buffer_ratio
        return cost


# =============================================================================
# EB-ECGR: Energy-Booked Predictive CGR
# =============================================================================
class EBECGRRouter(PECGRRouter):
    """
    Energy-Booked Predictive Contact Graph Routing (EB-ECGR).

    Addresses the 'energy overbooking' problem by maintaining a reservation registry
    of committed transmissions for each relay node. When routing a new bundle,
    future energy states are predicted by subtracting already-committed transmissions
    from the solar charging profile. This prevents traffic congestion at
    resource-constrained relays, automatically spilling excess traffic to
    high-capacity relays like MRO.
    """

    def __init__(self):
        super().__init__()
        self.name = "EB-ECGR"
        # Bookings registry: {node_id: [(tx_start_time, energy_wh_consumed, bundle_id), ...]}
        self.bookings = {}

    def reset(self):
        """Reset bookings registry between simulation runs."""
        self.bookings.clear()

    def _clean_old_bookings(self, current_time: float):
        """Remove bookings that started in the past, as they are already reflected in current SoC."""
        for n_id in list(self.bookings.keys()):
            self.bookings[n_id] = [
                b for b in self.bookings[n_id]
                if b[0] >= current_time
            ]

    def _remove_bundle_bookings(self, bundle_id: int):
        """Remove any existing bookings for this bundle_id to allow clean re-routing."""
        for n_id in self.bookings:
            self.bookings[n_id] = [
                b for b in self.bookings[n_id]
                if b[2] != bundle_id
            ]

    def predict_node_energy(self, node: Node, current_time: float, target_time: float, bundle_id: int = -1) -> float:
        """Predict node energy at target_time, subtracting energy committed to other bundles."""
        if node.is_ground:
            return node.battery_capacity_wh

        # 1. Base solar charging prediction
        dt_hours = (target_time - current_time) / 3600.0
        if dt_hours <= 0:
            base_energy = node.energy_wh
        else:
            from simulation.config import ECLIPSE_FRACTION
            avg_gen = node.power_gen_w * (1.0 - ECLIPSE_FRACTION)
            net_power = avg_gen - node.idle_power_w
            base_energy = node.energy_wh + net_power * dt_hours
            base_energy = max(0.0, min(node.battery_capacity_wh, base_energy))

        # 2. Subtract already booked energy from other bundles
        booked_energy = 0.0
        if node.node_id in self.bookings:
            for tx_start, e_wh, b_id in self.bookings[node.node_id]:
                # Subtract only if transmission starts in the future relative to current_time,
                # is scheduled before the target_time of this contact,
                # and is not for the same bundle
                if current_time <= tx_start < target_time and b_id != bundle_id:
                    booked_energy += e_wh

        predicted = base_energy - booked_energy
        return max(0.0, predicted)

    def select_route(self, routes: List[Route], bundle: Bundle,
                     nodes: Dict[int, Node], current_time: float) -> Optional[Route]:
        if not routes:
            return None

        # Clean old bookings and remove any previous reservations for this specific bundle
        self._clean_old_bookings(current_time)
        self._remove_bundle_bookings(bundle.bundle_id)

        # Filter for feasibility using predicted (and booked) energy and prevent routing loops
        feasible = []
        for route in routes:
            if not route.hops:
                continue
            # Loop prevention: do not route to a node we have already visited
            if route.hops[0].dest in bundle.hops:
                continue

            # Check capacity
            capacity_ok = all(
                hop.residual_capacity_bytes() >= bundle.size_bytes
                for hop in route.hops
            )
            if not capacity_ok:
                continue

            # Check relay buffer availability
            buffer_ok = True
            for n_id in route.relay_nodes:
                if n_id in nodes and not nodes[n_id].can_store(bundle.size_bytes):
                    buffer_ok = False
                    break
            if not buffer_ok:
                continue

            # Check relay predicted energy (accounting for bookings)
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

        # Calculate predicted SoCs for feasible routes
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

        delays = [max(r.arrival_time - current_time, 0.0) for r in feasible]
        max_delay = max(delays) if delays else 86400.0
        normalization = {"max_delay": max_delay, "predicted_socs": predicted_socs}

        best = min(feasible,
                   key=lambda r: self.compute_cost_pred(r, bundle, nodes, normalization, current_time))

        if best:
            # Commit energy bookings for the selected route
            for hop in best.hops:
                n_id = hop.source
                if n_id != best.source and n_id in nodes:
                    tx_time = bundle.size_bytes * 8 / best.bottleneck_rate
                    energy_needed = (nodes[n_id].tx_power_w + nodes[n_id].idle_power_w) * (tx_time / 3600.0)
                    if n_id not in self.bookings:
                        self.bookings[n_id] = []
                    self.bookings[n_id].append((hop.start_time, energy_needed, bundle.bundle_id))

        return best
