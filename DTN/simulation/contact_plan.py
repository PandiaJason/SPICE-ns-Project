"""
Contact Plan Generator for the ECGR simulation.

Generates a time-resolved contact plan from synthetic orbital data,
defining all communication opportunities in the Mars relay network.
Outputs in both native format and ION-DTN compatible format.
"""

import json
import os
import numpy as np
from simulation.config import (
    ROVER, SMALLSAT, MRO, DSN, CONTACT_PARAMS,
    SIM_DURATION, RANDOM_SEED, RESULTS_DIR, NODE_NAMES
)
from simulation.spice_data import SyntheticSPICE
from simulation.models import Contact


class ContactPlanGenerator:
    """
    Generates a realistic contact plan from orbital mechanics data.

    Combines SPICE-derived visibility windows with link-layer parameters
    to produce a set of Contact objects for the simulation.
    """

    def __init__(self, seed: int = RANDOM_SEED):
        self.rng = np.random.default_rng(seed)
        self.spice = SyntheticSPICE(seed=seed)
        self.contacts: list = []
        self.contact_id_counter = 0

    def _next_id(self) -> int:
        self.contact_id_counter += 1
        return self.contact_id_counter

    def generate_orbital_contacts(self) -> list:
        """
        Generate contacts derived from orbital visibility computations.
        Uses the synthetic SPICE module for physically-grounded contact windows.
        """
        contacts = []

        # --- Rover <-> SmallSat contacts (from orbital visibility) ---
        ss_windows = self.spice.compute_visibility_windows('smallsat')
        params = CONTACT_PARAMS[(ROVER, SMALLSAT)]
        for start, end in ss_windows:
            # Add jitter to simulate real-world variations
            jitter = self.rng.normal(0, 30)
            s = max(0, start + jitter)
            duration = end - start
            duration *= self.rng.uniform(0.8, 1.2)
            duration = np.clip(duration, 120, params["avg_duration_s"] * 2)
            e = s + duration

            c_fwd = Contact(self._next_id(), ROVER, SMALLSAT,
                            s, e, params["data_rate_bps"], params["owlt_s"])
            c_rev = Contact(self._next_id(), SMALLSAT, ROVER,
                            s, e, params["data_rate_bps"], params["owlt_s"])
            contacts.extend([c_fwd, c_rev])

        # --- Rover <-> MRO contacts ---
        mro_windows = self.spice.compute_visibility_windows('mro')
        params = CONTACT_PARAMS[(ROVER, MRO)]
        for start, end in mro_windows:
            jitter = self.rng.normal(0, 30)
            s = max(0, start + jitter)
            duration = (end - start) * self.rng.uniform(0.8, 1.2)
            duration = np.clip(duration, 120, params["avg_duration_s"] * 2)
            e = s + duration

            c_fwd = Contact(self._next_id(), ROVER, MRO,
                            s, e, params["data_rate_bps"], params["owlt_s"])
            c_rev = Contact(self._next_id(), MRO, ROVER,
                            s, e, params["data_rate_bps"], params["owlt_s"])
            contacts.extend([c_fwd, c_rev])

        # --- SmallSat <-> MRO contacts ---
        isl_windows = self.spice.compute_inter_satellite_windows()
        params = CONTACT_PARAMS[(SMALLSAT, MRO)]
        for start, end in isl_windows:
            duration = end - start
            duration = np.clip(duration, 60, params["avg_duration_s"] * 2)
            e = start + duration

            c_fwd = Contact(self._next_id(), SMALLSAT, MRO,
                            start, e, params["data_rate_bps"], params["owlt_s"])
            c_rev = Contact(self._next_id(), MRO, SMALLSAT,
                            start, e, params["data_rate_bps"], params["owlt_s"])
            contacts.extend([c_fwd, c_rev])

        # --- SmallSat -> DSN contacts ---
        ss_earth = self.spice.compute_earth_visibility('smallsat')
        params = CONTACT_PARAMS[(SMALLSAT, DSN)]
        for start, end in ss_earth:
            duration = end - start
            # SmallSat-DSN contacts are shorter due to limited antenna
            duration = min(duration, params["avg_duration_s"] +
                          self.rng.normal(0, params["std_duration_s"]))
            duration = max(300, duration)
            e = start + duration

            c = Contact(self._next_id(), SMALLSAT, DSN,
                        start, e, params["data_rate_bps"], params["owlt_s"])
            contacts.append(c)

        # --- MRO -> DSN contacts ---
        mro_earth = self.spice.compute_earth_visibility('mro')
        params = CONTACT_PARAMS[(MRO, DSN)]
        for start, end in mro_earth:
            duration = end - start
            duration = min(duration, params["avg_duration_s"] +
                          self.rng.normal(0, params["std_duration_s"]))
            duration = max(600, duration)
            e = start + duration

            c = Contact(self._next_id(), MRO, DSN,
                        start, e, params["data_rate_bps"], params["owlt_s"])
            contacts.append(c)

        # Sort by start time
        contacts.sort(key=lambda c: c.start_time)
        self.contacts = contacts
        return contacts

    def generate_supplementary_contacts(self) -> list:
        """
        Generate additional contacts using statistical models to ensure
        sufficient network connectivity for meaningful simulation.
        """
        additional = []

        for (src, dst), params in CONTACT_PARAMS.items():
            # Count existing contacts for this pair
            existing = [c for c in self.contacts
                       if c.source == src and c.dest == dst]
            needed = max(0, params["contacts_per_day"] - len(existing))

            if needed > 0:
                # Generate evenly-spaced additional contacts
                interval = SIM_DURATION / (needed + 1)
                for i in range(needed):
                    start = interval * (i + 1) + self.rng.normal(0, interval * 0.1)
                    start = np.clip(start, 0, SIM_DURATION - params["avg_duration_s"])
                    duration = max(120, self.rng.normal(
                        params["avg_duration_s"], params["std_duration_s"]))
                    end = start + duration

                    # Avoid overlapping with existing contacts
                    overlap = False
                    for ec in existing + additional:
                        if (ec.source == src and ec.dest == dst and
                            start < ec.end_time and end > ec.start_time):
                            overlap = True
                            break

                    if not overlap:
                        c = Contact(self._next_id(), src, dst,
                                   start, end, params["data_rate_bps"],
                                   params["owlt_s"])
                        additional.append(c)

                        # Bidirectional for local links
                        if params["owlt_s"] < 1.0 and dst != DSN:
                            c_rev = Contact(self._next_id(), dst, src,
                                          start, end, params["data_rate_bps"],
                                          params["owlt_s"])
                            additional.append(c_rev)

        self.contacts.extend(additional)
        self.contacts.sort(key=lambda c: c.start_time)
        return additional

    def generate_full_contact_plan(self) -> list:
        """Generate complete contact plan from orbital + supplementary data."""
        self.generate_orbital_contacts()
        self.generate_supplementary_contacts()
        print(f"[ContactPlan] Generated {len(self.contacts)} contacts total")
        for (src, dst) in CONTACT_PARAMS:
            count = len([c for c in self.contacts
                        if c.source == src and c.dest == dst])
            print(f"  {NODE_NAMES[src]} -> {NODE_NAMES[dst]}: {count} contacts")
        return self.contacts

    def export_ion_dtn_format(self, filepath: str):
        """
        Export contact plan in ION-DTN compatible format.

        Format: a contact +<start> +<end> <src> <dst> <rate>
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write("## ION-DTN Contact Plan\n")
            f.write("## Generated by ECGR Simulation\n")
            f.write(f"## Duration: {SIM_DURATION}s\n\n")
            for c in self.contacts:
                f.write(f"a contact +{int(c.start_time)} "
                       f"+{int(c.end_time)} "
                       f"{c.source + 1} {c.dest + 1} "
                       f"{int(c.data_rate_bps)}\n")
        print(f"[ION-DTN] Contact plan exported to {filepath}")

    def export_json(self, filepath: str):
        """Export contact plan as JSON for analysis."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        data = []
        for c in self.contacts:
            data.append({
                "id": c.contact_id,
                "source": c.source,
                "dest": c.dest,
                "source_name": NODE_NAMES[c.source],
                "dest_name": NODE_NAMES[c.dest],
                "start_time": c.start_time,
                "end_time": c.end_time,
                "duration_s": c.duration,
                "data_rate_bps": c.data_rate_bps,
                "owlt_s": c.owlt_s,
                "capacity_MB": c.capacity_bytes / (1024 * 1024),
            })
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[JSON] Contact plan exported to {filepath}")
