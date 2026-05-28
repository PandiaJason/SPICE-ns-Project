"""
Synthetic SPICE-like orbital data generator for the ML-CGR simulation.

Generates ephemeris data mimicking NASA SPICE kernel outputs for Mars-orbiting
satellites. Computes visibility windows, eclipse periods, contact opportunities,
and additional range-rate/elevation data needed by the ML link-quality predictor.

Reference: Vallado, D.A., "Fundamentals of Astrodynamics and Applications", 4th Ed.
"""

import numpy as np
from simulation.config import (
    MARS_RADIUS_KM, SMALLSAT_ALT_KM, MRO_ALT_KM,
    SMALLSAT_PERIOD_S, MRO_PERIOD_S, ECLIPSE_FRACTION,
    SIM_DURATION, RANDOM_SEED
)


class SyntheticSPICE:
    """
    Generates synthetic orbital ephemeris data analogous to NASA SPICE toolkit
    outputs for a Mars relay network scenario. Extended to also compute
    range-rate and elevation profiles needed by the ML link-quality predictor.
    """

    def __init__(self, seed: int = RANDOM_SEED):
        self.rng = np.random.default_rng(seed)

        # Orbital elements (simplified circular orbits)
        self.smallsat_a = MARS_RADIUS_KM + SMALLSAT_ALT_KM
        self.mro_a = MARS_RADIUS_KM + MRO_ALT_KM

        self.smallsat_period = SMALLSAT_PERIOD_S
        self.mro_period = MRO_PERIOD_S

        # Initial orbital phases (radians)
        self.smallsat_phase0 = self.rng.uniform(0, 2 * np.pi)
        self.mro_phase0 = self.rng.uniform(0, 2 * np.pi)

        # Inclinations (degrees)
        self.smallsat_inc = 87.0
        self.mro_inc = 93.0

        # Rover position
        self.rover_lat = -4.5
        self.rover_lon = 77.4

        # Minimum elevation for contact
        self.min_elevation = 10.0

    def satellite_position(self, t: float, sat_type: str) -> dict:
        """Compute satellite position at time t in Mars-centered frame."""
        if sat_type == 'smallsat':
            period = self.smallsat_period
            phase0 = self.smallsat_phase0
            alt = SMALLSAT_ALT_KM
            inc = self.smallsat_inc
        else:
            period = self.mro_period
            phase0 = self.mro_phase0
            alt = MRO_ALT_KM
            inc = self.mro_inc

        n = 2 * np.pi / period
        phase = (phase0 + n * t) % (2 * np.pi)

        lat = np.degrees(np.arcsin(np.sin(np.radians(inc)) * np.sin(phase)))
        mars_rot_rate = 2 * np.pi / (24.6 * 3600)
        lon = np.degrees(phase) - np.degrees(mars_rot_rate * t)
        lon = ((lon + 180) % 360) - 180

        return {"lat": lat, "lon": lon, "alt": alt, "phase": phase,
                "angular_velocity": n}

    def compute_elevation(self, sat_pos: dict) -> float:
        """Compute elevation angle of satellite as seen from rover."""
        dlat = np.radians(sat_pos["lat"] - self.rover_lat)
        dlon = np.radians(sat_pos["lon"] - self.rover_lon)
        angular_dist = np.sqrt(dlat**2 + (dlon * np.cos(np.radians(self.rover_lat)))**2)

        rho = np.arcsin(MARS_RADIUS_KM / (MARS_RADIUS_KM + sat_pos["alt"]))
        max_angle = np.pi / 2 - rho

        if angular_dist > max_angle:
            return -90.0
        return np.degrees(max_angle - angular_dist)

    def compute_range_rate(self, t: float, sat_type: str, dt: float = 5.0) -> float:
        """
        Compute range rate (km/s) between satellite and rover at time t.
        Uses numerical differentiation of range.
        """
        pos1 = self.satellite_position(t, sat_type)
        pos2 = self.satellite_position(t + dt, sat_type)

        # Approximate range from rover (using angular separation * orbital radius)
        r = MARS_RADIUS_KM + pos1["alt"]
        dlat1 = np.radians(pos1["lat"] - self.rover_lat)
        dlon1 = np.radians(pos1["lon"] - self.rover_lon)
        ang1 = np.sqrt(dlat1**2 + (dlon1 * np.cos(np.radians(self.rover_lat)))**2)
        range1 = r * ang1

        dlat2 = np.radians(pos2["lat"] - self.rover_lat)
        dlon2 = np.radians(pos2["lon"] - self.rover_lon)
        ang2 = np.sqrt(dlat2**2 + (dlon2 * np.cos(np.radians(self.rover_lat)))**2)
        range2 = r * ang2

        return (range2 - range1) / dt

    def compute_visibility_windows(self, sat_type: str,
                                    duration: float = SIM_DURATION,
                                    dt: float = 30.0) -> list:
        """Compute time windows when satellite is visible from rover."""
        windows = []
        visible = False
        window_start = 0.0

        for t in np.arange(0, duration, dt):
            pos = self.satellite_position(t, sat_type)
            elev = self.compute_elevation(pos)

            if elev >= self.min_elevation and not visible:
                visible = True
                window_start = t
            elif elev < self.min_elevation and visible:
                visible = False
                if t - window_start > 60:
                    windows.append((window_start, t))

        return windows

    def compute_eclipse_windows(self, sat_type: str,
                                 duration: float = SIM_DURATION) -> list:
        """Compute eclipse periods for a satellite."""
        if sat_type == 'smallsat':
            period = self.smallsat_period
        else:
            period = self.mro_period

        eclipse_duration = period * ECLIPSE_FRACTION
        windows = []
        offset = self.rng.uniform(0, period)
        t = offset

        while t < duration:
            start = t
            end = min(t + eclipse_duration, duration)
            windows.append((start, end))
            t += period

        return windows

    def compute_inter_satellite_windows(self, duration: float = SIM_DURATION,
                                         dt: float = 30.0) -> list:
        """Compute contact windows between SmallSat and MRO."""
        windows = []
        in_range = False
        window_start = 0.0
        max_sep_km = 2000.0

        for t in np.arange(0, duration, dt):
            ss_pos = self.satellite_position(t, 'smallsat')
            mro_pos = self.satellite_position(t, 'mro')

            dlat = np.radians(ss_pos["lat"] - mro_pos["lat"])
            dlon = np.radians(ss_pos["lon"] - mro_pos["lon"])
            angular_sep = np.sqrt(dlat**2 + dlon**2)
            approx_dist = angular_sep * (MARS_RADIUS_KM + (ss_pos["alt"] + mro_pos["alt"]) / 2)

            if approx_dist <= max_sep_km and not in_range:
                in_range = True
                window_start = t
            elif approx_dist > max_sep_km and in_range:
                in_range = False
                if t - window_start > 60:
                    windows.append((window_start, t))

        return windows

    def compute_earth_visibility(self, sat_type: str,
                                  duration: float = SIM_DURATION) -> list:
        """Compute windows when satellite can communicate with DSN."""
        if sat_type == 'smallsat':
            period = self.smallsat_period
        else:
            period = self.mro_period

        windows = []
        earth_visible_fraction = 0.55
        visible_duration = period * earth_visible_fraction

        t = self.rng.uniform(0, period * 0.3)
        while t < duration:
            start = t
            end = min(t + visible_duration, duration)
            windows.append((start, end))
            t += period

        return windows

    def get_contact_lqi_features(self, t: float, sat_type: str,
                                   contact_duration_s: float,
                                   relay_soc: float = 0.7,
                                   relay_buffer_util: float = 0.2,
                                   in_eclipse: bool = False) -> dict:
        """
        Compute the feature vector for the ML link-quality predictor
        at a given time and satellite configuration.

        Returns
        -------
        dict with feature values keyed by feature name.
        """
        pos = self.satellite_position(t, sat_type)
        elev = self.compute_elevation(pos)
        range_rate = self.compute_range_rate(t, sat_type)

        return {
            "elevation_deg": max(elev, 0.0),
            "range_rate_km_s": range_rate,
            "soc_relay": relay_soc,
            "eclipse_flag": 1.0 if in_eclipse else 0.0,
            "contact_duration_s": contact_duration_s,
            "time_of_day_norm": (t % SIM_DURATION) / SIM_DURATION,
            "buffer_util_relay": relay_buffer_util,
        }

    def generate_ephemeris_table(self, sat_type: str,
                                  duration: float = SIM_DURATION,
                                  dt: float = 60.0) -> list:
        """Generate a SPICE-like ephemeris table."""
        table = []
        for t in np.arange(0, duration, dt):
            pos = self.satellite_position(t, sat_type)
            elev = self.compute_elevation(pos)
            rr = self.compute_range_rate(t, sat_type)
            table.append({
                "epoch_s": t,
                "epoch_utc": f"2026-07-15T{int(t//3600):02d}:{int((t%3600)//60):02d}:{int(t%60):02d}",
                "lat_deg": round(pos["lat"], 4),
                "lon_deg": round(pos["lon"], 4),
                "alt_km": pos["alt"],
                "elevation_from_rover_deg": round(elev, 2),
                "range_rate_km_s": round(rr, 4),
                "phase_rad": round(pos["phase"], 4),
            })
        return table
