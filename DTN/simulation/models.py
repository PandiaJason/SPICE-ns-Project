"""
Data models for the ECGR simulation.

Defines Contact, Node, Bundle, and Route classes that represent
the core entities in a deep-space Delay-Tolerant Network.
"""

import copy
from dataclasses import dataclass, field
from typing import List, Optional
from simulation.config import NODE_SPECS, NODE_NAMES, ECLIPSE_FRACTION


# =============================================================================
# Contact Model
# =============================================================================
@dataclass
class Contact:
    """A communication opportunity between two DTN nodes."""
    contact_id: int
    source: int
    dest: int
    start_time: float
    end_time: float
    data_rate_bps: float
    owlt_s: float = 0.0
    residual_capacity_bits: float = 0.0

    def __post_init__(self):
        if self.residual_capacity_bits == 0.0:
            self.residual_capacity_bits = self.data_rate_bps * self.duration

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def capacity_bytes(self) -> float:
        return self.residual_capacity_bits / 8.0

    def is_active(self, t: float) -> bool:
        return self.start_time <= t < self.end_time

    def residual_capacity_bytes(self) -> float:
        return self.residual_capacity_bits / 8.0


# =============================================================================
# Bundle Model
# =============================================================================
@dataclass
class Bundle:
    """A DTN data bundle (protocol data unit)."""
    bundle_id: int
    source: int
    destination: int
    size_bytes: float
    priority: int               # 1=critical, 2=normal, 3=low
    creation_time: float
    payload_type: str = ""
    delivery_time: float = -1.0
    is_delivered: bool = False
    is_dropped: bool = False
    drop_reason: str = ""
    current_node: int = -1
    hops: List[int] = field(default_factory=list)
    route_algorithm: str = ""

    def __post_init__(self):
        if self.current_node == -1:
            self.current_node = self.source
        if not self.hops:
            self.hops = [self.source]

    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 * 1024)

    @property
    def latency(self) -> float:
        if self.is_delivered:
            return self.delivery_time - self.creation_time
        return -1.0


# =============================================================================
# Node Model
# =============================================================================
class Node:
    """A DTN network node with energy and buffer constraints."""

    def __init__(self, node_id: int):
        spec = NODE_SPECS[node_id]
        self.node_id = node_id
        self.name = NODE_NAMES[node_id]
        self.is_ground = spec["is_ground"]

        # Energy model (Wh)
        self.battery_capacity_wh = spec["battery_capacity_wh"]
        self.energy_wh = spec["battery_capacity_wh"] * spec["initial_soc"]
        self.power_gen_w = spec["power_generation_w"]
        self.idle_power_w = spec["idle_power_w"]
        self.tx_power_w = spec["tx_power_w"]
        self.rx_power_w = spec["rx_power_w"]

        # Buffer model (bytes)
        self.buffer_capacity_bytes = spec["buffer_capacity_mb"] * 1024 * 1024
        self.buffer_used_bytes = 0.0

        # Bundle queue
        self.bundle_queue: List[Bundle] = []

        # Logging
        self.energy_log: List[tuple] = []   # (time, energy_wh, soc)
        self.buffer_log: List[tuple] = []   # (time, used_bytes, utilization)

        # Eclipse tracking (for solar-powered nodes)
        self.in_eclipse = False

    @property
    def soc(self) -> float:
        """State of charge [0, 1]."""
        return self.energy_wh / self.battery_capacity_wh

    @property
    def buffer_utilization(self) -> float:
        """Buffer utilization [0, 1]."""
        return self.buffer_used_bytes / self.buffer_capacity_bytes

    @property
    def available_buffer_bytes(self) -> float:
        return self.buffer_capacity_bytes - self.buffer_used_bytes

    def update_energy(self, dt_s: float, is_transmitting: bool = False,
                      is_receiving: bool = False):
        """Update energy state for a time step dt_s seconds."""
        if self.is_ground:
            return

        # Power consumption
        power_consumed_w = self.idle_power_w
        if is_transmitting:
            power_consumed_w += self.tx_power_w
        if is_receiving:
            power_consumed_w += self.rx_power_w

        # Power generation (zero during eclipse)
        power_gen = 0.0 if self.in_eclipse else self.power_gen_w

        # Net power
        net_power_w = power_gen - power_consumed_w
        energy_delta_wh = net_power_w * (dt_s / 3600.0)

        self.energy_wh = max(0.0, min(self.battery_capacity_wh,
                                       self.energy_wh + energy_delta_wh))

    def can_store(self, size_bytes: float) -> bool:
        return self.available_buffer_bytes >= size_bytes

    def store_bundle(self, bundle: Bundle) -> bool:
        if not self.can_store(bundle.size_bytes):
            return False
        self.bundle_queue.append(bundle)
        self.buffer_used_bytes += bundle.size_bytes
        bundle.current_node = self.node_id
        return True

    def remove_bundle(self, bundle: Bundle):
        if bundle in self.bundle_queue:
            self.bundle_queue.remove(bundle)
            self.buffer_used_bytes = max(0.0,
                self.buffer_used_bytes - bundle.size_bytes)

    def can_transmit(self, duration_s: float) -> bool:
        """Check if node has enough energy to transmit for duration_s."""
        if self.is_ground:
            return True
        energy_needed = (self.tx_power_w + self.idle_power_w) * (duration_s / 3600.0)
        return self.energy_wh >= energy_needed

    def log_state(self, t: float):
        self.energy_log.append((t, self.energy_wh, self.soc))
        self.buffer_log.append((t, self.buffer_used_bytes, self.buffer_utilization))

    def reset(self):
        """Reset node to initial state."""
        spec = NODE_SPECS[self.node_id]
        self.energy_wh = spec["battery_capacity_wh"] * spec["initial_soc"]
        self.buffer_used_bytes = 0.0
        self.bundle_queue.clear()
        self.energy_log.clear()
        self.buffer_log.clear()
        self.in_eclipse = False


# =============================================================================
# Route Model
# =============================================================================
@dataclass
class Route:
    """A sequence of contacts forming a path from source to destination."""
    hops: List[Contact]
    source: int
    destination: int

    @property
    def arrival_time(self) -> float:
        if not self.hops:
            return float('inf')
        return self.hops[-1].end_time + self.hops[-1].owlt_s

    @property
    def departure_time(self) -> float:
        if not self.hops:
            return float('inf')
        return self.hops[0].start_time

    @property
    def total_delay(self) -> float:
        return self.arrival_time - self.departure_time

    @property
    def relay_nodes(self) -> List[int]:
        """Return intermediate relay node IDs."""
        nodes = []
        for hop in self.hops:
            if hop.source != self.source and hop.source not in nodes:
                nodes.append(hop.source)
        return nodes

    @property
    def bottleneck_rate(self) -> float:
        if not self.hops:
            return 0.0
        return min(h.data_rate_bps for h in self.hops)
