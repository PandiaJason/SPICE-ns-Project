# receiver.py
"""
Laser Inter-Satellite Link (ISL) Wake-on-Beacon IoT Simulator
Receiver Unit (Mars Orbiter Satellite)

This script simulates the distant satellite orbiting Mars. It propagates the satellite's
orbit using SPICE data, checks for incoming wake-up laser signals from Earth, models
physical obstructions (Mars occultation) and photodiode geometric pointing constraints,
and executes the low-power Finite State Machine (FSM) power-gating logic.
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

# Orbital elements (identical to transmitter for synchronization)
MARS_RADIUS_KM = 3389.5
ALTITUDE_KM = 400.0
A_KM = MARS_RADIUS_KM + ALTITUDE_KM
E = 0.05
I_RAD = np.radians(45.0)
LAN_RAD = np.radians(30.0)
AP_RAD = np.radians(60.0)
M0_RAD = np.radians(0.0)
EPOCH_UTC = "2026-06-01T12:00:00"
MARS_GM = 42828.375214

# FSM States & Power Consumption
STATE_DEEP_SLEEP = "DEEP_SLEEP"          # P < 1 uW (standby)
STATE_PREAMBLE_DETECT = "PREAMBLE_DET"    # P = 10 uW (evaluation)
STATE_BOOT_RAIL = "BOOT_RAIL"            # P = 0.5 W (transistor closed, booting)
STATE_ACTIVE_SESSION = "ACTIVE_SESSION"  # P = 15.0 W (data link active)

POWER_SLEEP_W = 2.8e-6  # 2.8 uW
POWER_PREAMBLE_W = 10e-6  # 10 uW
POWER_BOOT_W = 0.5  # 0.5 Watts
POWER_ACTIVE_W = 15.0  # 15.0 Watts

# Receiver Hardware Configuration
FOV_HALF_ANGLE_DEG = 60.0  # Conical FOV of 120 degrees (60 deg half-angle)
WAKEUP_KEY = "0x55AA77FF8899AABB"
SESSION_DURATION_SEC = 600.0  # Active communication session duration (10 mins)
BOOT_TIME_SEC = 5.0  # Time required to boot transceiver and lock mirrors

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
    q = A_KM * (1.0 - E)
    elts = [q, E, I_RAD, LAN_RAD, AP_RAD, M0_RAD, t0, MARS_GM]
    state = spice.conics(elts, et)
    pos = state[:3]  # km
    vel = state[3:]  # km/s
    return pos, vel

def check_occultation(earth_pos_ssb, sat_pos_ssb, mars_pos_ssb):
    """
    Determine if Mars blocks the line of sight between Earth and the Satellite.
    Calculates the perpendicular distance from Mars center to the ray.
    """
    # A = Earth, B = Satellite, C = Mars center
    A = np.array(earth_pos_ssb)
    B = np.array(sat_pos_ssb)
    C = np.array(mars_pos_ssb)
    
    AB = B - A
    AC = C - A
    
    # Projection factor s
    s = np.dot(AC, AB) / np.dot(AB, AB)
    
    # Closest point on line segment AB to C
    if s < 0.0:
        closest_point = A
    elif s > 1.0:
        closest_point = B
    else:
        closest_point = A + s * AB
        
    perp_dist = np.linalg.norm(C - closest_point)
    is_occulted = (perp_dist < MARS_RADIUS_KM) and (0.0 <= s <= 1.0)
    
    return is_occulted, perp_dist

def simulate_receiver():
    """
    Simulates the satellite receiver orbiting Mars, reading the independent
    transmitted beam plans, checking hits/occultations, and executing FSM transitions.
    """
    load_kernels()
    
    # Read the transmitter log (representing physical light waves in space)
    tx_plan_path = "/home/jason/SPICE-ns-Project/SatWAKE-UP/paper/transmitted_pulses.json"
    if not os.path.exists(tx_plan_path):
        print(f"Error: Transmitter plan {tx_plan_path} not found. Run transmitter.py first.")
        return
        
    with open(tx_plan_path, "r") as f:
        transmissions = json.load(f)
        
    print(f"--- Mars Orbiter Wake-on-Beacon Receiver Simulation ---")
    print(f"Loaded {len(transmissions)} potential beacon pulses from Earth.")
    
    # Initialize receiver state
    current_state = STATE_DEEP_SLEEP
    session_end_et = 0.0
    boot_complete_et = 0.0
    
    c = spice.clight()  # km/s
    receiver_log = []
    
    for tx in transmissions:
        t_rec = tx["target_receive_et"]
        t_fire = tx["fire_et"]
        pointing_vector = np.array(tx["pointing_vector_j2000"])
        naive_pointing = np.array(tx["naive_pointing_vector_j2000"])
        earth_pos_fire = np.array(tx["earth_pos_fire_j2000"])
        div_rad = np.radians(tx["divergence_urad"] / 1e6)
        
        # 1. Propagate satellite and Mars center at local arrival time t_rec
        mars_state_rec, _ = spice.spkezr('MARS BARYCENTER', t_rec, 'J2000', 'NONE', 'SSB')
        mars_pos_rec = mars_state_rec[:3]
        
        sat_rel_mars, sat_vel_mars = get_satellite_rel_mars(t_rec)
        sat_pos_rec = mars_pos_rec + sat_rel_mars  # km
        
        # 2. Check if Earth has direct Line of Sight (Mars Occultation check)
        is_occulted, min_altitude_km = check_occultation(earth_pos_fire, sat_pos_rec, mars_pos_rec)
        
        # 3. Calculate distance from Earth firing location to satellite
        d_sat = np.linalg.norm(sat_pos_rec - earth_pos_fire)
        beam_radius_km = d_sat * np.tan(div_rad / 2.0)
        
        # 4. Check beam spot centering (Displacement)
        # Corrected beam center location at distance d_sat
        beam_center_corrected = earth_pos_fire + d_sat * pointing_vector
        disp_corrected = np.linalg.norm(sat_pos_rec - beam_center_corrected)
        
        # Naive beam center location at distance d_sat
        beam_center_naive = earth_pos_fire + d_sat * naive_pointing
        disp_naive = np.linalg.norm(sat_pos_rec - beam_center_naive)
        
        # Determine if the physical signal hit the satellite (using corrected pointing)
        hit_corrected = (disp_corrected <= beam_radius_km)
        hit_naive = (disp_naive <= beam_radius_km)
        
        # 5. Check photodiode pointing vector & incidence angle
        # Satellite is nadir-pointing: -Z points to Mars, +Z (sensor face) points Zenith (away from Mars)
        sensor_pointing_j2000 = sat_rel_mars / np.linalg.norm(sat_rel_mars)
        
        # Incoming light direction vector at the satellite
        light_direction_j2000 = (sat_pos_rec - earth_pos_fire) / d_sat
        
        # Angle between sensor pointing (+Z) and direction pointing back to Earth (-light_direction)
        cos_theta = np.dot(sensor_pointing_j2000, -light_direction_j2000)
        # Clip to ensure valid arccos range
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        incidence_angle_deg = np.degrees(np.arccos(cos_theta))
        
        sensor_visible = (incidence_angle_deg <= FOV_HALF_ANGLE_DEG)
        
        # 6. Physical signal successfully captured condition
        signal_captured = hit_corrected and (not is_occulted) and sensor_visible
        
        # 7. Update FSM State & Power Consumption based on time and signals
        # Check if active session is complete
        if current_state == STATE_ACTIVE_SESSION and t_rec >= session_end_et:
            current_state = STATE_DEEP_SLEEP
            print(f"[{tx['target_receive_utc']}] FSM Transition: ACTIVE_SESSION -> DEEP_SLEEP (Session Complete)")
            
        elif current_state == STATE_BOOT_RAIL and t_rec >= boot_complete_et:
            current_state = STATE_ACTIVE_SESSION
            session_end_et = t_rec + SESSION_DURATION_SEC
            print(f"[{tx['target_receive_utc']}] FSM Transition: BOOT_RAIL -> ACTIVE_SESSION (Transceiver Online)")
            
        # Process new optical wake-up trigger
        if signal_captured and tx["modulation_key"] == WAKEUP_KEY:
            if current_state == STATE_DEEP_SLEEP:
                current_state = STATE_BOOT_RAIL
                boot_complete_et = t_rec + BOOT_TIME_SEC
                print(f"[{tx['target_receive_utc']}] FSM Transition: DEEP_SLEEP -> BOOT_RAIL (Wake-on-Beacon Triggered!)")
            # If already booting or active, the signal just keeps the session refreshed or ignored
            
        # Map current state to power draw
        if current_state == STATE_DEEP_SLEEP:
            power_w = POWER_SLEEP_W
        elif current_state == STATE_PREAMBLE_DETECT:
            power_w = POWER_PREAMBLE_W
        elif current_state == STATE_BOOT_RAIL:
            power_w = POWER_BOOT_W
        elif current_state == STATE_ACTIVE_SESSION:
            power_w = POWER_ACTIVE_W
        else:
            power_w = POWER_SLEEP_W
            
        # Log this state step
        log_entry = {
            "et": float(t_rec),
            "utc": tx["target_receive_utc"],
            "sat_pos_rel_mars_j2000": sat_rel_mars.tolist(),
            "sensor_pointing_j2000": sensor_pointing_j2000.tolist(),
            "incidence_angle_deg": float(incidence_angle_deg),
            "is_occulted": bool(is_occulted),
            "min_altitude_km": float(min_altitude_km),
            "beam_radius_km": float(beam_radius_km),
            "disp_corrected_km": float(disp_corrected),
            "disp_naive_km": float(disp_naive),
            "hit_corrected": bool(hit_corrected),
            "hit_naive": bool(hit_naive),
            "signal_captured": bool(signal_captured),
            "fsm_state": current_state,
            "power_w": float(power_w)
        }
        receiver_log.append(log_entry)
        
    # Write the receiver log data to file
    output_path = "/home/jason/SPICE-ns-Project/SatWAKE-UP/paper/receiver_log.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(receiver_log, f, indent=4)
        
    print(f"Receiver simulation completed. Log written to {output_path}.")
    spice.clpool()

if __name__ == "__main__":
    simulate_receiver()
