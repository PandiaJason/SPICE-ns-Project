"""
Contact Plan Generator for the ML-CGR simulation.

Generates a time-resolved contact plan from synthetic orbital data.
Extends the base contact plan with dynamic link-quality indices (LQI)
computed from orbital geometry, eclipse status, and link-quality model params.
"""

import json
import os
import numpy as np
from simulation.config import (
    ROVER, SMALLSAT, MRO, DSN, CONTACT_PARAMS,
    SIM_DURATION, RANDOM_SEED, RESULTS_DIR, NODE_NAMES,
    LINK_QUALITY_PARAMS
)
from simulation.spice_data import SyntheticSPICE
from simulation.models import Contact


class ContactPlanGenerator:
    """
    Generates a realistic contact plan from orbital mechanics data.

    Extends the base generator to include dynamic Link Quality Index (LQI)
    estimation per contact based on elevation geometry, range rate, and
    eclipse conditions — providing ground truth for the ML predictor training.
    """

    def __init__(self, seed: int = RANDOM_SEED):
        self.rng = np.random.default_rng(seed)
        self.spice = SyntheticSPICE(seed=seed)
        self.contacts: list = []
        self.contact_id_counter = 0

    def _next_id(self) -> int:
        self.contact_id_counter += 1
        return self.contact_id_counter

    def _compute_lqi(self, src: int, dst: int, start_time: float,
                     duration: float, in_eclipse: bool = False) -> float:
        """
        Compute a physics-inspired Link Quality Index for a contact.

        The LQI is derived from the orbital geometry and link parameters,
        serving as ground truth for training the ML predictor.

        Parameters
        ----------
        src, dst : int   Node IDs
        start_time : float  Contact start time
        duration : float    Contact duration (s)
        in_eclipse : bool   Whether relay is in eclipse

        Returns
        -------
        float : LQI in [0, 1]
        """
        key = (src, dst) if (src, dst) in LINK_QUALITY_PARAMS else (dst, src)
        if key not in LINK_QUALITY_PARAMS:
            return 0.75  # Default

        params = LINK_QUALITY_PARAMS[key]
        lqi = params["base_lqi"]

        # Eclipse degradation
        if in_eclipse:
            lqi -= params["eclipse_degradation"]

        # Determine satellite type for elevation/range-rate
        sat_type = None
        if SMALLSAT in (src, dst):
            sat_type = 'smallsat'
        elif MRO in (src, dst):
            sat_type = 'mro'

        if sat_type and DSN not in (src, dst):
            # Elevation-based quality boost (higher elevation = better LQI)
            mid_t = start_time + duration / 2
            pos = self.spice.satellite_position(mid_t, sat_type)
            elev = self.spice.compute_elevation(pos)
            if elev > 0:
                lqi += 0.10 * (elev / 90.0)

            # Range-rate induced degradation (high range-rate = Doppler stress)
            rr = abs(self.spice.compute_range_rate(mid_t, sat_type))
            lqi -= params["range_rate_factor"] * min(rr / 5.0, 1.0)

        # Temporal stochastic variation (representing solar plasma, atmospheric scintillation)
        noise = self.rng.normal(0, params["doppler_variance"])
        lqi += noise

        return float(np.clip(lqi, 0.05, 1.0))

    def _get_eclipse_at(self, t: float, eclipse_windows: list) -> bool:
        """Check if time t falls within any eclipse window."""
        for start, end in eclipse_windows:
            if start <= t < end:
                return True
        return False

    def generate_orbital_contacts(self) -> list:
        """
        Generate contacts derived from orbital visibility computations.
        Includes LQI estimation for each contact.
        """
        contacts = []
        eclipse_windows = self.spice.compute_eclipse_windows('smallsat')

        # --- Rover <-> SmallSat contacts ---
        ss_windows = self.spice.compute_visibility_windows('smallsat')
        params = CONTACT_PARAMS[(ROVER, SMALLSAT)]
        for start, end in ss_windows:
            jitter = self.rng.normal(0, 30)
            s = max(0, start + jitter)
            duration = end - start
            duration *= self.rng.uniform(0.8, 1.2)
            duration = np.clip(duration, 120, params["avg_duration_s"] * 2)
            e = s + duration
            in_ecl = self._get_eclipse_at(s + duration / 2, eclipse_windows)
            lqi = self._compute_lqi(ROVER, SMALLSAT, s, duration, in_ecl)

            c_fwd = Contact(self._next_id(), ROVER, SMALLSAT,
                            s, e, params["data_rate_bps"], params["owlt_s"], lqi=lqi)
            c_rev = Contact(self._next_id(), SMALLSAT, ROVER,
                            s, e, params["data_rate_bps"], params["owlt_s"], lqi=lqi)
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
            lqi = self._compute_lqi(ROVER, MRO, s, duration, False)

            c_fwd = Contact(self._next_id(), ROVER, MRO,
                            s, e, params["data_rate_bps"], params["owlt_s"], lqi=lqi)
            c_rev = Contact(self._next_id(), MRO, ROVER,
                            s, e, params["data_rate_bps"], params["owlt_s"], lqi=lqi)
            contacts.extend([c_fwd, c_rev])

        # --- SmallSat <-> MRO contacts ---
        isl_windows = self.spice.compute_inter_satellite_windows()
        params = CONTACT_PARAMS[(SMALLSAT, MRO)]
        for start, end in isl_windows:
            duration = end - start
            duration = np.clip(duration, 60, params["avg_duration_s"] * 2)
            e = start + duration
            in_ecl = self._get_eclipse_at(start + duration / 2, eclipse_windows)
            lqi = self._compute_lqi(SMALLSAT, MRO, start, duration, in_ecl)

            c_fwd = Contact(self._next_id(), SMALLSAT, MRO,
                            start, e, params["data_rate_bps"], params["owlt_s"], lqi=lqi)
            c_rev = Contact(self._next_id(), MRO, SMALLSAT,
                            start, e, params["data_rate_bps"], params["owlt_s"], lqi=lqi)
            contacts.extend([c_fwd, c_rev])

        # --- SmallSat -> DSN contacts ---
        ss_earth = self.spice.compute_earth_visibility('smallsat')
        params = CONTACT_PARAMS[(SMALLSAT, DSN)]
        for start, end in ss_earth:
            duration = end - start
            duration = min(duration, params["avg_duration_s"] +
                          self.rng.normal(0, params["std_duration_s"]))
            duration = max(300, duration)
            e = start + duration
            in_ecl = self._get_eclipse_at(start + duration / 2, eclipse_windows)
            lqi = self._compute_lqi(SMALLSAT, DSN, start, duration, in_ecl)

            c = Contact(self._next_id(), SMALLSAT, DSN,
                        start, e, params["data_rate_bps"], params["owlt_s"], lqi=lqi)
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
            lqi = self._compute_lqi(MRO, DSN, start, duration, False)

            c = Contact(self._next_id(), MRO, DSN,
                        start, e, params["data_rate_bps"], params["owlt_s"], lqi=lqi)
            contacts.append(c)

        contacts.sort(key=lambda c: c.start_time)
        self.contacts = contacts
        return contacts

    def generate_supplementary_contacts(self) -> list:
        """Generate additional contacts using statistical models."""
        additional = []

        for (src, dst), params in CONTACT_PARAMS.items():
            existing = [c for c in self.contacts
                       if c.source == src and c.dest == dst]
            needed = max(0, params["contacts_per_day"] - len(existing))

            if needed > 0:
                interval = SIM_DURATION / (needed + 1)
                for i in range(needed):
                    start = interval * (i + 1) + self.rng.normal(0, interval * 0.1)
                    start = np.clip(start, 0, SIM_DURATION - params["avg_duration_s"])
                    duration = max(120, self.rng.normal(
                        params["avg_duration_s"], params["std_duration_s"]))
                    end = start + duration

                    overlap = False
                    for ec in existing + additional:
                        if (ec.source == src and ec.dest == dst and
                            start < ec.end_time and end > ec.start_time):
                            overlap = True
                            break

                    if not overlap:
                        lqi = self._compute_lqi(src, dst, start, duration, False)
                        c = Contact(self._next_id(), src, dst,
                                   start, end, params["data_rate_bps"],
                                   params["owlt_s"], lqi=lqi)
                        additional.append(c)

                        if params["owlt_s"] < 1.0 and dst != DSN:
                            c_rev = Contact(self._next_id(), dst, src,
                                          start, end, params["data_rate_bps"],
                                          params["owlt_s"], lqi=lqi)
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
            avg_lqi = np.mean([c.lqi for c in self.contacts
                               if c.source == src and c.dest == dst]) if count > 0 else 0
            print(f"  {NODE_NAMES[src]} -> {NODE_NAMES[dst]}: "
                  f"{count} contacts, avg LQI={avg_lqi:.3f}")
        return self.contacts

    def export_ion_dtn_format(self, filepath: str):
        """Export contact plan in ION-DTN compatible format."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write("## ION-DTN Contact Plan\n")
            f.write("## Generated by ML-CGR Simulation\n")
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
                "lqi": c.lqi,
            })
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[JSON] Contact plan exported to {filepath}")
