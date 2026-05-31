# transmitter.py
"""
Laser Inter-Satellite Link (ISL) Wake-on-Beacon IoT Simulator
Transmitter Unit (Earth Ground Station / DSN Center)

This script simulates the Earth-based wake-up laser transmitter. It uses SPICE kernels
to determine planetary positions and orbital dynamics, computes the precise light travel
time and point-ahead angle to hit a Mars Orbiter, and logs the firing parameters.
"""

import os
import json
import numpy as np
import spiceypy as spice

# Define paths to SPICE kernels
KERNELS_DIR = "/home/jason/SPICE-ns-Project/ns-3.47/kernels"
DE440_BSP = os.path.join(KERNELS_DIR, "de440.bsp")
NAIF0012_TLS = os.path.join(KERNELS_DIR, "naif0012.tls")
GM_DE431_TPC = os.path.join(KERNELS_DIR, "gm_de431.tpc")

# Orbital elements for Mars Orbiter (Low Mars Orbit, slightly elliptical)
# Semi-major axis = 3789.5 km (approx. 400 km altitude)
MARS_RADIUS_KM = 3389.5
ALTITUDE_KM = 400.0
A_KM = MARS_RADIUS_KM + ALTITUDE_KM
E = 0.05  # Eccentricity
I_RAD = np.radians(45.0)  # Inclination
LAN_RAD = np.radians(30.0)  # Longitude of Ascending Node
AP_RAD = np.radians(60.0)  # Argument of Periapsis
M0_RAD = np.radians(0.0)  # Mean anomaly at epoch
EPOCH_UTC = "2026-06-01T12:00:00"  # Epoch of elements
MARS_GM = 42828.375214  # Mars GM in km^3/s^2

# Laser properties
LASER_DIVERGENCE_URAD = 20.0  # microradians
WAKEUP_KEY = "0x55AA77FF8899AABB"  # Cryptographic modulation key

def load_kernels():
    """Load the necessary SPICE kernels."""
    spice.furnsh(DE440_BSP)
    spice.furnsh(NAIF0012_TLS)
    spice.furnsh(GM_DE431_TPC)

def get_satellite_rel_mars(et):
    """
    Compute the position and velocity of the satellite relative to Mars center
    using SPICE conics propagation.
    """
    t0 = spice.str2et(EPOCH_UTC)
    q = A_KM * (1.0 - E)  # Pericenter distance
    
    # 8-element Keplerian elements array for SPICE conics
    elts = [
        q,
        E,
        I_RAD,
        LAN_RAD,
        AP_RAD,
        M0_RAD,
        t0,
        MARS_GM
    ]
    state = spice.conics(elts, et)
    pos = state[:3]  # km
    vel = state[3:]  # km/s
    return pos, vel

def calculate_pointing(t_rec):
    """
    Solve the light-time equation to find the exact firing time (t_fire)
    and point-ahead vector from Earth's center to hit the satellite at t_rec.
    """
    c = spice.clight()  # Speed of light in km/s
    
    # 1. Get Mars center position at receive time t_rec relative to SSB
    mars_rec, _ = spice.spkezr('MARS BARYCENTER', t_rec, 'J2000', 'NONE', 'SSB')
    mars_pos_rec = mars_rec[:3]
    
    # 2. Get Satellite position relative to Mars at t_rec
    sat_rel_mars, _ = get_satellite_rel_mars(t_rec)
    sat_pos_rec = mars_pos_rec + sat_rel_mars  # Satellite position relative to SSB at t_rec
    
    # 3. Fixed-point iteration to solve: t_fire = t_rec - ||r_sat(t_rec) - r_earth(t_fire)|| / c
    tau = 600.0  # Initial guess of 10 minutes (600s)
    earth_pos_fire = None
    
    for _ in range(10):
        t_fire_temp = t_rec - tau
        earth_fire_state, _ = spice.spkezr('EARTH', t_fire_temp, 'J2000', 'NONE', 'SSB')
        earth_pos_fire = earth_fire_state[:3]
        dist = np.linalg.norm(sat_pos_rec - earth_pos_fire)
        tau = dist / c
        
    t_fire = t_rec - tau
    
    # Re-evaluate final Earth position at final t_fire
    earth_fire_state, _ = spice.spkezr('EARTH', t_fire, 'J2000', 'NONE', 'SSB')
    earth_pos_fire = earth_fire_state[:3]
    
    # Precise line-of-sight vector from Earth at t_fire to satellite at t_rec
    los_vector = sat_pos_rec - earth_pos_fire
    distance_km = np.linalg.norm(los_vector)
    pointing_direction = los_vector / distance_km
    
    return t_fire, pointing_direction, distance_km, sat_pos_rec, earth_pos_fire

def simulate_transmissions(start_utc, end_utc, interval_sec):
    """
    Generate a series of target transmission times and compute the firing vectors.
    """
    load_kernels()
    
    t_start = spice.str2et(start_utc)
    t_end = spice.str2et(end_utc)
    t_steps = np.arange(t_start, t_end, interval_sec)
    
    transmissions = []
    
    print(f"--- Earth Transmitter Point-Ahead Simulation ---")
    print(f"Simulation Range: {start_utc} to {end_utc}")
    print(f"Solving point-ahead vector for {len(t_steps)} targets...")
    
    for t_rec in t_steps:
        # Solve the light path equations
        t_fire, pointing_vector, distance_km, sat_rec, earth_fire = calculate_pointing(t_rec)
        
        # Calculate naive pointing vector (pointing directly at where the satellite is seen at t_fire)
        # Note: What Earth *sees* at t_fire is the satellite position at t_fire - light_time
        # Let's get the light-time corrected position of the satellite from Earth's frame at t_fire
        state_seen, lt_seen = spice.spkezr('MARS BARYCENTER', t_fire, 'J2000', 'CN+S', 'EARTH')
        mars_seen = state_seen[:3]
        # In a real uncorrected system, a simple tracking system might point at Mars' current visual position
        # and assume the satellite is in orbit.
        # Let's calculate the naive pointing as pointing to the satellite's position at t_fire:
        mars_fire, _ = spice.spkezr('MARS BARYCENTER', t_fire, 'J2000', 'NONE', 'SSB')
        mars_fire_pos = mars_fire[:3]
        sat_rel_mars_fire, _ = get_satellite_rel_mars(t_fire)
        sat_fire = mars_fire_pos + sat_rel_mars_fire
        naive_pointing = (sat_fire - earth_fire) / np.linalg.norm(sat_fire - earth_fire)
        
        # Save transmission record
        tx_record = {
            "target_receive_et": t_rec,
            "target_receive_utc": spice.et2utc(t_rec, "ISOC", 3),
            "fire_et": t_fire,
            "fire_utc": spice.et2utc(t_fire, "ISOC", 3),
            "light_time_sec": t_rec - t_fire,
            "distance_km": distance_km,
            "pointing_vector_j2000": pointing_vector.tolist(),
            "naive_pointing_vector_j2000": naive_pointing.tolist(),
            "sat_pos_rec_j2000": sat_rec.tolist(),
            "earth_pos_fire_j2000": earth_fire.tolist(),
            "modulation_key": WAKEUP_KEY,
            "divergence_urad": LASER_DIVERGENCE_URAD
        }
        transmissions.append(tx_record)
        
    # Write the transmitted beam data to file
    output_path = "/home/jason/SPICE-ns-Project/SatWAKE-UP/paper/transmitted_pulses.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(transmissions, f, indent=4)
        
    print(f"Simulation completed. Pointing vectors logged to {output_path}.")
    spice.clpool()  # Unload kernels to clean up memory

if __name__ == "__main__":
    # Simulate for 2 Sol duration (approx. 49.6 hours / 25 satellite orbits)
    simulate_transmissions(
        start_utc="2026-06-01T12:00:00",
        end_utc="2026-06-03T13:40:00",
        interval_sec=60.0  # High-fidelity step size of 60 seconds (1 minute)
    )
