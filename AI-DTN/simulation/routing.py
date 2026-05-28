"""
Routing algorithms for the ML-CGR simulation.

Implements:
  1. Standard Contact Graph Routing (CGR) - Earliest Delivery Time baseline
  2. ML-CGR: Machine Learning-Driven Predictive Link-Quality Estimation
             for Proactive Bundle Fragmentation in Energy-Aware CGR

The ML-CGR algorithm integrates:
  - An online Random Forest predictor that estimates contact-level LQI from
    orbital state features (elevation, range-rate, eclipse, SoC, buffer)
  - Proactive bundle fragmentation decisions driven by predicted LQI
  - Energy-aware route selection inherited from ECGR cost functions
  - A sliding-window online retraining loop that uses observed LQI history

References:
  - Burleigh, S., "Contact Graph Routing", IETF draft-burleigh-dtnrg-cgr, 2010.
  - Fraire, J.A., et al., "CGR Enhancement for DTN", IEEE TASE, 2021.
  - Breiman, L., "Random Forests", Machine Learning, 45, 2001.
"""

import heapq
import numpy as np
from typing import List, Optional, Dict, Deque
from collections import deque
from simulation.models import Contact, Node, Bundle, Route, LinkQualitySample
from simulation.config import (
    DSN, ALPHA_BASE, BETA_BASE, GAMMA_BASE,
    PRIORITY_WEIGHTS, ENERGY_CRITICAL_THRESHOLD,
    ENERGY_WARNING_THRESHOLD, BUFFER_WARNING_THRESHOLD,
    LQI_GOOD_THRESHOLD, LQI_WARN_THRESHOLD, LQI_POOR_THRESHOLD,
    FRAG_SIZE_GOOD_MB, FRAG_SIZE_WARN_MB, FRAG_SIZE_POOR_MB,
    FRAG_TRIGGER_SIZE_MB, MIN_FRAGMENT_SIZE_MB,
    ML_N_ESTIMATORS, ML_MAX_DEPTH, ML_TRAINING_WINDOW,
    ML_RETRAIN_INTERVAL, ML_WARMUP_SAMPLES, ML_FEATURES
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
    current_time : float

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
    _counter = 0

    initial_state = (current_time, _counter, source, [], frozenset([source]))
    pq = [initial_state]
    best_arrival = {}

    while pq and len(routes) < 10:
        arr_time, _, node, path, visited = heapq.heappop(pq)

        if node == destination:
            routes.append(Route(hops=list(path), source=source,
                               destination=destination))
            continue

        if len(path) >= max_hops:
            continue

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

            if contact.start_time < arr_time:
                if contact.end_time <= arr_time:
                    continue
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
    Burleigh's CGR specification. Resource-blind: does not consider
    energy, buffer state, or link quality.
    """

    def __init__(self):
        self.name = "CGR"

    def select_route(self, routes: List[Route], bundle: Bundle,
                     nodes: Dict[int, Node], current_time: float) -> Optional[Route]:
        """Select the best route based on earliest arrival time."""
        if not routes:
            return None

        feasible = []
        for route in routes:
            if not route.hops:
                continue
            if route.hops[0].dest in bundle.hops:
                continue
            sufficient = all(
                hop.residual_capacity_bytes() >= bundle.size_bytes
                for hop in route.hops
            )
            if sufficient:
                feasible.append(route)

        if not feasible:
            return None

        return min(feasible, key=lambda r: r.arrival_time)

    def compute_cost(self, route: Route, bundle: Bundle,
                     nodes: Dict[int, Node]) -> float:
        """Cost = arrival time (for comparison logging)."""
        return route.arrival_time

    def should_fragment(self, bundle: Bundle, route: Route,
                        current_time: float) -> Optional[float]:
        """Standard CGR does not fragment bundles. Returns None."""
        return None


# =============================================================================
# ML Link Quality Predictor (Online Random Forest)
# =============================================================================
class MLLinkQualityPredictor:
    """
    Online Random Forest-based Link Quality Index (LQI) predictor.

    Trained incrementally on historical contact observations. At inference
    time it predicts the LQI for a future contact given its orbital feature
    vector. When insufficient training data is available (warm-up phase),
    falls back to the physics-based LQI stored on the Contact object.

    The predictor is retrained at configurable intervals to incorporate
    recent link observations, adapting to changing orbital geometries,
    eclipse dynamics, and relay energy states.

    Features used (in order, matching ML_FEATURES config):
        [0] elevation_deg       : Satellite elevation from rover (deg)
        [1] range_rate_km_s     : Range rate at contact midpoint (km/s)
        [2] soc_relay           : Relay SoC at contact start [0, 1]
        [3] eclipse_flag        : 1.0 if relay in eclipse, else 0.0
        [4] contact_duration_s  : Contact window duration (s)
        [5] time_of_day_norm    : Time of day normalized to [0, 1]
        [6] buffer_util_relay   : Relay buffer utilization [0, 1]
    """

    def __init__(self, seed: int = 42):
        self._rng = np.random.default_rng(seed)
        self._training_buffer: Deque[LinkQualitySample] = deque(
            maxlen=ML_TRAINING_WINDOW
        )
        self._model = None          # Lazy-initialized after warmup
        self._last_retrain_time = -float('inf')
        self._n_predictions = 0
        self._prediction_errors: List[float] = []  # For RMSE logging
        self._is_warmed_up = False
        self._seed = seed

    def _build_model(self):
        """Build a fresh sklearn RandomForestRegressor."""
        try:
            from sklearn.ensemble import RandomForestRegressor
            return RandomForestRegressor(
                n_estimators=ML_N_ESTIMATORS,
                max_depth=ML_MAX_DEPTH,
                random_state=self._seed,
                n_jobs=1,
            )
        except ImportError:
            return None  # Fallback to physics-based LQI

    def add_observation(self, sample: LinkQualitySample):
        """Add a link quality observation to the training buffer."""
        self._training_buffer.append(sample)

    def maybe_retrain(self, current_time: float) -> bool:
        """
        Retrain the model if enough time has elapsed and there are
        sufficient training samples.

        Returns
        -------
        bool : True if model was retrained.
        """
        if len(self._training_buffer) < ML_WARMUP_SAMPLES:
            return False

        if current_time - self._last_retrain_time < ML_RETRAIN_INTERVAL:
            return False

        X = np.array([s.to_feature_vector() for s in self._training_buffer])
        y = np.array([s.measured_lqi for s in self._training_buffer])

        model = self._build_model()
        if model is None:
            return False

        model.fit(X, y)
        self._model = model
        self._last_retrain_time = current_time
        self._is_warmed_up = True
        return True

    def predict_lqi(self, features: dict, fallback_lqi: float = 0.75) -> float:
        """
        Predict LQI for a contact given its feature vector.

        Falls back to physics-based LQI during warm-up or if sklearn
        is not available.

        Parameters
        ----------
        features : dict   Keys matching ML_FEATURES
        fallback_lqi : float   Physics-based LQI estimate (from Contact.lqi)

        Returns
        -------
        float : Predicted LQI in [0, 1]
        """
        if not self._is_warmed_up or self._model is None:
            # During warm-up: interpolate between fallback and a
            # noise-reduced estimate (not fully random)
            warmup_fraction = len(self._training_buffer) / ML_WARMUP_SAMPLES
            noise = self._rng.normal(0, 0.05 * (1 - warmup_fraction))
            return float(np.clip(fallback_lqi + noise, 0.05, 1.0))

        x = np.array([features.get(f, 0.0) for f in ML_FEATURES]).reshape(1, -1)
        pred = self._model.predict(x)[0]
        self._n_predictions += 1
        return float(np.clip(pred, 0.05, 1.0))

    def get_feature_importances(self) -> Optional[Dict[str, float]]:
        """Return feature importance dict if model is trained."""
        if self._model is None:
            return None
        return {f: float(imp)
                for f, imp in zip(ML_FEATURES, self._model.feature_importances_)}

    def reset(self):
        """Reset predictor state between simulation runs."""
        self._training_buffer.clear()
        self._model = None
        self._last_retrain_time = -float('inf')
        self._n_predictions = 0
        self._prediction_errors.clear()
        self._is_warmed_up = False


# =============================================================================
# ML-CGR: ML-Driven Predictive Link-Quality CGR with Proactive Fragmentation
# =============================================================================
class MLCGRRouter:
    """
    Machine Learning-Driven Predictive Link-Quality Estimation for Proactive
    Bundle Fragmentation in Energy-Aware CGR (ML-CGR).

    Algorithm Overview
    ------------------
    1. **ML Link Quality Prediction**: At each routing epoch, the router
       queries the online Random Forest predictor to estimate the LQI of
       each candidate contact. The predictor uses a 7-feature orbital state
       vector: [elevation, range_rate, relay_SoC, eclipse_flag,
       contact_duration, time_of_day, relay_buffer_util].

    2. **Proactive Bundle Fragmentation**: Prior to route selection, if the
       predicted LQI of the best route's bottleneck hop falls below quality
       thresholds, the bundle is proactively fragmented into smaller pieces.
       Fragment size is adapted to the predicted LQI:
           - LQI >= 0.75 (Good):      fragment_size = FRAG_SIZE_GOOD_MB
           - 0.45 <= LQI < 0.75 (Warn): fragment_size = FRAG_SIZE_WARN_MB
           - LQI < 0.45 (Poor):       fragment_size = FRAG_SIZE_POOR_MB
       This prevents large bundles from failing partial transmissions on
       degraded links, improving overall delivery ratio.

    3. **Energy-Aware Cost Function**: Route selection uses a multi-attribute
       cost function (inherited from ECGR) that jointly optimizes:
           Cost = α·D_norm + β·(1/E_min) + γ·(S/B_min) + δ·(1/LQI_min)
       where δ is an additional LQI penalty weight. The dynamic weights
       (α, β, γ, δ) adapt based on bundle priority and network state.

    4. **Online Retraining Loop**: After each contact concludes, the router
       logs the observed LQI (derived from actual throughput vs. scheduled
       capacity) and periodically retrains the Random Forest model. This
       creates a closed-loop system that improves predictions as the
       simulation progresses.

    Cost Function
    -------------
    C_ML(r, b) = α·D̂ + β·Φ_E(r) + γ·Φ_B(r,b) + δ·Φ_LQI(r)

    where:
        D̂        = normalized end-to-end delay
        Φ_E(r)   = energy penalty (inverse of min relay SoC)
        Φ_B(r,b) = buffer penalty (bundle-to-available-buffer ratio)
        Φ_LQI(r) = LQI penalty (inverse of predicted min LQI on route)
        δ        = LQI weight (default 1.0, boosted for poor links)
    """

    DELTA_BASE = 1.0        # Base LQI weight

    def __init__(self, spice=None, seed: int = 42):
        self.name = "ML-CGR"
        self.predictor = MLLinkQualityPredictor(seed=seed)
        self.spice = spice  # SyntheticSPICE instance for feature extraction
        self._bundle_id_counter = 0
        # Track generated fragments so they can be returned to the simulator
        self._pending_fragments: List[Bundle] = []
        # Feature cache: contact_id -> predicted_lqi
        self._lqi_cache: Dict[int, float] = {}

    def reset(self):
        """Reset router state between Monte Carlo runs."""
        self.predictor.reset()
        self._pending_fragments.clear()
        self._lqi_cache.clear()

    def _new_bundle_id(self) -> int:
        self._bundle_id_counter += 1
        return 100000 + self._bundle_id_counter

    def _extract_features(self, contact: Contact, relay_node: Optional[Node],
                           current_time: float) -> dict:
        """
        Extract the ML feature vector for a contact at current_time.

        Parameters
        ----------
        contact : Contact
        relay_node : Node   The relay at contact.source (may be None)
        current_time : float

        Returns
        -------
        dict with keys matching ML_FEATURES
        """
        # Elevation and range-rate from SPICE
        if self.spice is not None:
            sat_type = None
            if contact.source == 1 or contact.dest == 1:  # SMALLSAT = 1
                sat_type = 'smallsat'
            elif contact.source == 2 or contact.dest == 2:  # MRO = 2
                sat_type = 'mro'

            if sat_type and contact.owlt_s < 1.0:
                mid_t = min(contact.start_time + contact.duration / 2,
                            current_time + 60)
                pos = self.spice.satellite_position(mid_t, sat_type)
                elev = max(self.spice.compute_elevation(pos), 0.0)
                rr = abs(self.spice.compute_range_rate(mid_t, sat_type))
            else:
                elev = 30.0   # Default for deep-space links
                rr = 0.5
        else:
            elev = 30.0
            rr = 0.5

        soc = relay_node.soc if relay_node and not relay_node.is_ground else 1.0
        eclipse = 1.0 if (relay_node and relay_node.in_eclipse) else 0.0
        buf_util = relay_node.buffer_utilization if relay_node else 0.0
        duration = max(contact.end_time - current_time, 0.0)
        tod_norm = (current_time % 86400) / 86400.0

        return {
            "elevation_deg": elev,
            "range_rate_km_s": rr,
            "soc_relay": soc,
            "eclipse_flag": eclipse,
            "contact_duration_s": duration,
            "time_of_day_norm": tod_norm,
            "buffer_util_relay": buf_util,
        }

    def predict_route_lqi(self, route: Route, nodes: Dict[int, Node],
                          current_time: float) -> float:
        """
        Predict the bottleneck LQI for a route.

        Uses cached predictions when available; otherwise queries the ML
        predictor. The bottleneck is the minimum predicted LQI across hops.
        """
        lqis = []
        for hop in route.hops:
            if hop.contact_id in self._lqi_cache:
                lqis.append(self._lqi_cache[hop.contact_id])
                continue

            relay_node = nodes.get(hop.source)
            features = self._extract_features(hop, relay_node, current_time)
            predicted = self.predictor.predict_lqi(features, fallback_lqi=hop.lqi)
            self._lqi_cache[hop.contact_id] = predicted
            lqis.append(predicted)

        return min(lqis) if lqis else 1.0

    def should_fragment(self, bundle: Bundle, predicted_lqi: float,
                        current_time: float) -> Optional[float]:
        """
        Determine whether to fragment the bundle and the optimal fragment size.

        Fragmentation is triggered when:
        - Bundle size > FRAG_TRIGGER_SIZE_MB
        - Predicted bottleneck LQI < LQI_GOOD_THRESHOLD

        Parameters
        ----------
        bundle : Bundle
        predicted_lqi : float   Predicted bottleneck LQI for best route
        current_time : float

        Returns
        -------
        float or None : Fragment size in MB, or None if no fragmentation needed
        """
        if bundle.size_mb <= FRAG_TRIGGER_SIZE_MB:
            return None  # Small bundles do not benefit from fragmentation
        if bundle.is_fragment:
            return None  # Do not re-fragment

        if predicted_lqi >= LQI_GOOD_THRESHOLD:
            return None  # Good link quality: no fragmentation needed
        elif predicted_lqi >= LQI_WARN_THRESHOLD:
            return FRAG_SIZE_WARN_MB
        elif predicted_lqi >= LQI_POOR_THRESHOLD:
            return FRAG_SIZE_POOR_MB
        else:
            return FRAG_SIZE_POOR_MB  # Most aggressive

    def fragment_bundle(self, bundle: Bundle, frag_size_mb: float,
                        current_time: float) -> List[Bundle]:
        """
        Fragment a bundle into smaller pieces of at most frag_size_mb.

        Parameters
        ----------
        bundle : Bundle
        frag_size_mb : float   Target fragment size (MB)
        current_time : float

        Returns
        -------
        list of Bundle : Fragment bundles
        """
        frag_size_bytes = max(frag_size_mb * 1024 * 1024,
                              MIN_FRAGMENT_SIZE_MB * 1024 * 1024)
        n_frags = int(np.ceil(bundle.size_bytes / frag_size_bytes))
        n_frags = max(n_frags, 1)

        fragments = []
        remaining = bundle.size_bytes

        for i in range(n_frags):
            size = min(frag_size_bytes, remaining)
            remaining -= size

            frag = Bundle(
                bundle_id=self._new_bundle_id(),
                source=bundle.source,
                destination=bundle.destination,
                size_bytes=size,
                priority=bundle.priority,
                creation_time=current_time,
                payload_type=bundle.payload_type,
                current_node=bundle.current_node,
                route_algorithm="ML-CGR",
                is_fragment=True,
                parent_bundle_id=bundle.bundle_id,
                fragment_index=i,
                total_fragments=n_frags,
                predicted_lqi=bundle.predicted_lqi,
            )
            frag.hops = list(bundle.hops)
            fragments.append(frag)

        return fragments

    def compute_dynamic_weights(self, bundle: Bundle, nodes: Dict[int, Node],
                                 route: Route, predicted_lqi: float) -> tuple:
        """
        Compute dynamic (α, β, γ, δ) weights based on bundle priority,
        network state, and predicted link quality.

        Returns
        -------
        tuple : (alpha, beta, gamma, delta)
        """
        pw = PRIORITY_WEIGHTS.get(bundle.priority, PRIORITY_WEIGHTS[2])
        alpha = ALPHA_BASE * pw["alpha"]
        beta = BETA_BASE * pw["beta"]
        gamma = GAMMA_BASE * pw["gamma"]
        delta = self.DELTA_BASE

        relay_nodes = route.relay_nodes
        if relay_nodes:
            min_soc = min(nodes[n].soc for n in relay_nodes if n in nodes)
            max_buf = max(nodes[n].buffer_utilization for n in relay_nodes
                         if n in nodes)

            if min_soc < ENERGY_CRITICAL_THRESHOLD:
                beta *= 4.0
            elif min_soc < ENERGY_WARNING_THRESHOLD:
                beta *= 2.0

            if max_buf > BUFFER_WARNING_THRESHOLD:
                gamma *= 3.0

        # Boost LQI penalty on poor predicted links
        if predicted_lqi < LQI_POOR_THRESHOLD:
            delta *= 5.0
        elif predicted_lqi < LQI_WARN_THRESHOLD:
            delta *= 2.5

        return alpha, beta, gamma, delta

    def compute_cost(self, route: Route, bundle: Bundle,
                     nodes: Dict[int, Node], normalization: dict,
                     current_time: float, predicted_lqi: float) -> float:
        """
        Compute the multi-attribute ML-CGR cost for a route.

        Cost = α·D̂ + β·Φ_E + γ·Φ_B + δ·Φ_LQI

        Parameters
        ----------
        route : Route
        bundle : Bundle
        nodes : dict
        normalization : dict
        current_time : float
        predicted_lqi : float   Predicted bottleneck LQI for this route

        Returns
        -------
        float : Cost value
        """
        alpha, beta, gamma, delta = self.compute_dynamic_weights(
            bundle, nodes, route, predicted_lqi
        )

        # --- Delay term ---
        delay = max(route.arrival_time - current_time, 0.0)
        max_delay = normalization.get("max_delay", 86400.0)
        delay_norm = delay / max(max_delay, 1.0)

        # --- Energy term ---
        relay_nodes = route.relay_nodes
        if relay_nodes:
            energy_ratios = [nodes[n].soc for n in relay_nodes if n in nodes]
            min_energy = min(energy_ratios) if energy_ratios else 1.0
        else:
            min_energy = 1.0
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

        # --- LQI penalty term ---
        lqi_cost = 1.0 / max(predicted_lqi, 0.05)

        cost = (alpha * delay_norm + beta * energy_cost
                + gamma * max_buffer_ratio + delta * lqi_cost)
        return cost

    def select_route(self, routes: List[Route], bundle: Bundle,
                     nodes: Dict[int, Node], current_time: float) -> Optional[Route]:
        """
        Select the best route using the ML-CGR multi-attribute cost function.

        Steps:
        1. Filter routes for capacity and energy feasibility
        2. Predict LQI for each feasible route
        3. Compute multi-attribute cost including LQI penalty
        4. Return route with minimum cost

        Parameters
        ----------
        routes : list of Route
        bundle : Bundle
        nodes : dict
        current_time : float

        Returns
        -------
        Route or None
        """
        if not routes:
            return None

        # Trigger ML model retraining if needed
        self.predictor.maybe_retrain(current_time)

        # Clear per-epoch LQI cache
        self._lqi_cache.clear()

        # Filter for feasibility
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
            for hop in route.hops:
                n_id = hop.source
                if n_id != route.source and n_id in nodes:
                    tx_time = bundle.size_bytes * 8 / route.bottleneck_rate
                    if not nodes[n_id].can_transmit(tx_time):
                        energy_ok = False
                        break
            if not energy_ok:
                continue

            feasible.append(route)

        if not feasible:
            return None

        # Predict LQI for each feasible route
        route_lqis = {}
        for route in feasible:
            predicted_lqi = self.predict_route_lqi(route, nodes, current_time)
            route_lqis[id(route)] = predicted_lqi

        # Compute normalization
        delays = [max(r.arrival_time - current_time, 0.0) for r in feasible]
        max_delay = max(delays) if delays else 86400.0
        normalization = {"max_delay": max_delay}

        # Select route with minimum ML-CGR cost
        best = min(
            feasible,
            key=lambda r: self.compute_cost(
                r, bundle, nodes, normalization, current_time,
                route_lqis[id(r)]
            )
        )

        # Store predicted LQI on the bundle for fragmentation decision
        bundle.predicted_lqi = route_lqis.get(id(best), 1.0)
        return best

    def add_lqi_observation(self, contact: Contact, actual_lqi: float,
                             relay_node: Optional[Node],
                             current_time: float):
        """
        Record an observed LQI measurement to the ML training buffer.

        Called by the simulator after a contact completes, with the
        measured LQI derived from actual vs. scheduled throughput.

        Parameters
        ----------
        contact : Contact
        actual_lqi : float   Observed LQI (actual_bits_sent / scheduled_bits)
        relay_node : Node or None
        current_time : float
        """
        if relay_node is None:
            return

        soc = relay_node.soc if not relay_node.is_ground else 1.0
        eclipse = 1.0 if relay_node.in_eclipse else 0.0
        buf_util = relay_node.buffer_utilization

        if self.spice is not None:
            sat_type = None
            if contact.source == 1 or contact.dest == 1:
                sat_type = 'smallsat'
            elif contact.source == 2 or contact.dest == 2:
                sat_type = 'mro'

            if sat_type and contact.owlt_s < 1.0:
                mid_t = contact.start_time + contact.duration / 2
                pos = self.spice.satellite_position(mid_t, sat_type)
                elev = max(self.spice.compute_elevation(pos), 0.0)
                rr = abs(self.spice.compute_range_rate(mid_t, sat_type))
            else:
                elev, rr = 30.0, 0.5
        else:
            elev, rr = 30.0, 0.5

        sample = LinkQualitySample(
            time=current_time,
            link_key=(contact.source, contact.dest),
            elevation_deg=elev,
            range_rate_km_s=rr,
            soc_relay=soc,
            eclipse_flag=eclipse,
            contact_duration_s=contact.duration,
            time_of_day_norm=(contact.start_time % 86400) / 86400.0,
            buffer_util_relay=buf_util,
            measured_lqi=actual_lqi,
        )
        self.predictor.add_observation(sample)
