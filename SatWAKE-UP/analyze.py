# analyze.py
"""
Laser Inter-Satellite Link (ISL) Wake-on-Beacon IoT Simulator
Data Analysis & Publication-Quality Visualization

This script aggregates logs from the transmitter and receiver simulations, computes
research-quality metrics (pointing error offsets, occultation periods, and cumulative
energy budgets), and generates premium white-themed vector graphics directly under the
paper/figures directory.
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import spiceypy as spice

# Define paths
DATA_DIR = "/home/jason/SPICE-ns-Project/SatWAKE-UP/results"
FIG_DIR = DATA_DIR
TX_LOG_PATH = os.path.join(DATA_DIR, "transmitted_pulses.json")
RX_LOG_PATH = os.path.join(DATA_DIR, "receiver_log.json")
KERNELS_DIR = "/home/jason/SPICE-ns-Project/ns-3.47/kernels"

# Orbital elements / geometry
MARS_RADIUS_KM = 3389.5
ALTITUDE_KM = 400.0
A_KM = MARS_RADIUS_KM + ALTITUDE_KM

# FSM States
STATE_DEEP_SLEEP = "DEEP_SLEEP"
STATE_PREAMBLE_DETECT = "PREAMBLE_DET"
STATE_BOOT_RAIL = "BOOT_RAIL"
STATE_ACTIVE_SESSION = "ACTIVE_SESSION"

# Premium academic plotting style (white background, high-contrast, clean gridlines)
plt.style.use('default')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['grid.color'] = '#e5e5e5'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.linewidth'] = 0.5
plt.rcParams['text.color'] = 'black'
plt.rcParams['axes.labelcolor'] = 'black'
plt.rcParams['xtick.color'] = 'black'
plt.rcParams['ytick.color'] = 'black'
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['legend.fontsize'] = 12
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12

# Curated high-contrast color palette for white backgrounds
COLOR_PRIMARY = '#1e90ff'      # Electric Light Blue (Corrected / Laser Beam)
COLOR_SECONDARY = '#d62728'    # Crimson Red (Naive / Error)
COLOR_MARS = '#e2583e'         # Terracotta Orange (Mars)
COLOR_EARTH = '#1f77b4'        # Deep Royal Blue (Earth)
COLOR_FSM = '#7a3bcf'          # Rich Purple (FSM States)
COLOR_GLOW = '#2ca02c'         # Rich Green (Woken Up State)

def load_data():
    """Load transmitter and receiver logs."""
    if not os.path.exists(TX_LOG_PATH) or not os.path.exists(RX_LOG_PATH):
        raise FileNotFoundError("Simulation logs not found. Please run transmitter.py and receiver.py first.")
    with open(TX_LOG_PATH, "r") as f:
        tx_data = json.load(f)
    with open(RX_LOG_PATH, "r") as f:
        rx_data = json.load(f)
    return tx_data, rx_data

def plot_scenario_3d(tx, rx):
    """
    Generates two side-by-side 3D simulation snapshots of the local Martian orbit
    representing the two critical operational states:
    1. Occulted State (Eclipse/Deep Sleep)
    2. Active Contact State (Woken up/Active Session)
    Includes a premium HUD stats block below each subplot.
    """
    def is_point_occulted(p, earth_dir):
        u_earth = earth_dir / np.linalg.norm(earth_dir)
        proj = np.dot(p, u_earth)
        if proj >= 0:
            return False
        d2 = np.dot(p, p) - proj**2
        return d2 < 3389.5**2

    def plot_split_orbit(ax, positions, earth_dir):
        segments = []
        current_seg = [positions[0]]
        current_occ = is_point_occulted(positions[0], earth_dir)
        
        for p in positions[1:]:
            occ = is_point_occulted(p, earth_dir)
            if occ == current_occ:
                current_seg.append(p)
            else:
                segments.append((np.array(current_seg), current_occ))
                current_seg = [p]
                current_occ = occ
        segments.append((np.array(current_seg), current_occ))
        
        first_vis = True
        first_occ = True
        for seg, occ in segments:
            if occ:
                # Occulted segment: light-grey, thin, dashed
                ax.plot(seg[:, 0], seg[:, 1], seg[:, 2], color='#d3d3d3', linewidth=1.0, linestyle='--', alpha=0.5,
                        label='Orbit (Occulted)' if first_occ else "")
                first_occ = False
            else:
                # Visible segment: solid purple
                ax.plot(seg[:, 0], seg[:, 1], seg[:, 2], color=COLOR_FSM, linewidth=1.4, linestyle='-',
                        label='Orbit (Visible)' if first_vis else "")
                first_vis = False

    # 1. Find representative indices
    occ_idx = None
    min_clearance = float('inf')
    for idx, entry in enumerate(rx):
        if entry["is_occulted"] and entry["min_altitude_km"] < min_clearance:
            min_clearance = entry["min_altitude_km"]
            occ_idx = idx
    if occ_idx is None:
        occ_idx = 0
        
    wake_idx = None
    for idx, entry in enumerate(rx):
        if entry["signal_captured"] and entry["fsm_state"] == STATE_ACTIVE_SESSION:
            wake_idx = idx
            break
    if wake_idx is None:
        for idx, entry in enumerate(rx):
            if entry["signal_captured"]:
                wake_idx = idx
                break
    if wake_idx is None:
        wake_idx = 0

    fig = plt.figure(figsize=(16, 9))
    plt.subplots_adjust(bottom=0.22, top=0.90, left=0.05, right=0.95)

    # Common Mars sphere grid data
    u, v = np.mgrid[0:2*np.pi:30j, 0:np.pi:15j]
    x_mars = 3389.5 * np.cos(u) * np.sin(v)
    y_mars = 3389.5 * np.sin(u) * np.sin(v)
    z_mars = 3389.5 * np.cos(v)

    # Full satellite orbit path
    sat_positions = np.array([e["sat_pos_rel_mars_j2000"] for e in rx])

    # ================= SUBPLOT 1: OCCULTED STATE =================
    ax1 = fig.add_subplot(121, projection='3d')
    ax1.set_facecolor('white')
    ax1.xaxis.set_pane_color((0.98, 0.98, 0.98, 1.0))
    ax1.yaxis.set_pane_color((0.98, 0.98, 0.98, 1.0))
    ax1.zaxis.set_pane_color((0.98, 0.98, 0.98, 1.0))
    ax1.set_title("Simulation Snapshot A: Occulted State (Eclipse / Deep Sleep)", fontsize=13, weight='bold', pad=10)

    # Draw Mars
    ax1.plot_surface(x_mars, y_mars, z_mars, color='#e2583e', alpha=0.35, edgecolor='#993300', linewidth=0.5)
    
    # Blocked Incoming laser beam
    earth_dir_occ = -np.array(tx[occ_idx]["pointing_vector_j2000"])

    # Draw Orbit with occulted segments faded / dashed
    plot_split_orbit(ax1, sat_positions, earth_dir_occ)

    # Satellite Position at Occultation (drawn faded behind Mars as it is occulted)
    sat_pos_occ = np.array(rx[occ_idx]["sat_pos_rel_mars_j2000"])
    ax1.scatter(sat_pos_occ[0], sat_pos_occ[1], sat_pos_occ[2], color='#7f7f7f', s=60, edgecolor='black', zorder=1, alpha=0.15, label='Satellite (Occulted/Hidden)')

    # Blocked Incoming laser beam
    laser_len = 7000.0  # km

    # Calculate exact point where the laser intersects Mars' surface
    R_mars = 3389.5
    a_quad = 1.0
    b_quad = -2.0 * np.dot(sat_pos_occ, earth_dir_occ)
    c_quad = np.dot(sat_pos_occ, sat_pos_occ) - R_mars**2
    disc = b_quad**2 - 4.0 * a_quad * c_quad
    if disc >= 0:
        t_entry = (-b_quad + np.sqrt(disc)) / 2.0
    else:
        t_entry = 3600.0  # fallback

    # draw ray starting from distance, stopping at Mars boundary
    ax1.plot([sat_pos_occ[0] - earth_dir_occ[0]*laser_len, sat_pos_occ[0] - earth_dir_occ[0]*t_entry],
             [sat_pos_occ[1] - earth_dir_occ[1]*laser_len, sat_pos_occ[1] - earth_dir_occ[1]*t_entry],
             [sat_pos_occ[2] - earth_dir_occ[2]*laser_len, sat_pos_occ[2] - earth_dir_occ[2]*t_entry],
             color='#d62728', linewidth=1.5, linestyle=':', label='Blocked Laser Path')

    # Direction to Earth Quiver (pointing from satellite towards Earth, through Mars)
    ax1.quiver(sat_pos_occ[0], sat_pos_occ[1], sat_pos_occ[2],
               earth_dir_occ[0], earth_dir_occ[1], earth_dir_occ[2],
               length=1800.0, color='#1f77b4', linewidth=1.8, arrow_length_ratio=0.15, label='Direction to Earth')
    
    ax1.set_xlabel("Mars X (km)", fontsize=12)
    ax1.set_ylabel("Mars Y (km)", fontsize=12)
    ax1.set_zlabel("Mars Z (km)", fontsize=12)
    ax1.legend(loc='lower left', fontsize=11, frameon=True, facecolor='white')
    
    max_range = A_KM * 1.3
    ax1.set_xlim(-max_range, max_range)
    ax1.set_ylim(-max_range, max_range)
    ax1.set_zlim(-max_range, max_range)

    # Dynamic camera view angle from Earth's exact viewpoint on Mars (EXACT Earth Reference Frame)
    u_occ = earth_dir_occ / np.linalg.norm(earth_dir_occ)
    elev_occ = np.degrees(np.arcsin(u_occ[2]))
    azim_occ = np.degrees(np.arctan2(u_occ[1], u_occ[0]))
    ax1.view_init(elev=elev_occ, azim=azim_occ)

    # HUD Box A
    hud_occ = (
        f"★ SIMULATION STATE A: OCCULTED ECLIPSE ★\n"
        f"-----------------------------------------\n"
        f"Target UTC:      {rx[occ_idx]['utc'][:-4]}\n"
        f"Link Range:      {tx[occ_idx]['distance_km']:.1f} km\n"
        f"Prop Delay:      {tx[occ_idx]['light_time_sec']:.3f} s\n"
        f"LOS Clearance:   {rx[occ_idx]['min_altitude_km']:.1f} km (Blocked)\n"
        f"FSM State:       {rx[occ_idx]['fsm_state']}\n"
        f"Power gated:     {rx[occ_idx]['power_w']*1e6:.1f} uW (DEEP SLEEP)\n"
        f"MOSFET Switch:   OPEN (Standby)"
    )
    fig.text(0.06, 0.03, hud_occ, fontsize=9.0, family='monospace', color='black',
             bbox=dict(boxstyle="round,pad=0.6", facecolor='#fcfcfc', edgecolor='#d0d0d0', alpha=0.95))


    # ================= SUBPLOT 2: WOKEN-UP STATE =================
    ax2 = fig.add_subplot(122, projection='3d')
    ax2.set_facecolor('white')
    ax2.xaxis.set_pane_color((0.98, 0.98, 0.98, 1.0))
    ax2.yaxis.set_pane_color((0.98, 0.98, 0.98, 1.0))
    ax2.zaxis.set_pane_color((0.98, 0.98, 0.98, 1.0))
    ax2.set_title("Simulation Snapshot B: Contact & Active Session State", fontsize=13, weight='bold', pad=10)

    # Draw Mars
    ax2.plot_surface(x_mars, y_mars, z_mars, color='#e2583e', alpha=0.35, edgecolor='#993300', linewidth=0.5)
    
    # Active Incoming laser beam striking the satellite
    earth_dir_wake = -np.array(tx[wake_idx]["pointing_vector_j2000"])

    # Draw Orbit with occulted segments faded / dashed
    plot_split_orbit(ax2, sat_positions, earth_dir_wake)

    # Satellite Position at Wake-up (visible to Earth)
    sat_pos_wake = np.array(rx[wake_idx]["sat_pos_rel_mars_j2000"])
    ax2.scatter(sat_pos_wake[0], sat_pos_wake[1], sat_pos_wake[2], color='#2ca02c', s=60, edgecolor='black', zorder=5, label='Satellite (Woken Up / Visible)')

    ax2.plot([sat_pos_wake[0] - earth_dir_wake[0]*laser_len, sat_pos_wake[0]],
             [sat_pos_wake[1] - earth_dir_wake[1]*laser_len, sat_pos_wake[1]],
             [sat_pos_wake[2] - earth_dir_wake[2]*laser_len, sat_pos_wake[2]],
             color=COLOR_PRIMARY, linewidth=1.8, linestyle='-', label='SPICE Point-Ahead Beacon')
    
    # Boresight pointing vector (+Z Zenith)
    sensor_dir = np.array(rx[wake_idx]["sensor_pointing_j2000"])
    sensor_arrow_len = 1000.0  # km
    ax2.quiver(sat_pos_wake[0], sat_pos_wake[1], sat_pos_wake[2], 
               sensor_dir[0], sensor_dir[1], sensor_dir[2], 
               length=sensor_arrow_len, color='#2ca02c', linewidth=2.0, label='Sensor Pointing (Zenith)')

    # Direction to Earth Quiver (pointing from satellite towards Earth)
    ax2.quiver(sat_pos_wake[0], sat_pos_wake[1], sat_pos_wake[2],
               earth_dir_wake[0], earth_dir_wake[1], earth_dir_wake[2],
               length=1800.0, color='#1f77b4', linewidth=1.8, arrow_length_ratio=0.15, label='Direction to Earth')

    ax2.set_xlabel("Mars X (km)", fontsize=12)
    ax2.set_ylabel("Mars Y (km)", fontsize=12)
    ax2.set_zlabel("Mars Z (km)", fontsize=12)
    ax2.legend(loc='lower left', fontsize=11, frameon=True, facecolor='white')
    
    ax2.set_xlim(-max_range, max_range)
    ax2.set_ylim(-max_range, max_range)
    ax2.set_zlim(-max_range, max_range)

    # Dynamic camera view angle from Earth's exact viewpoint on Mars (EXACT Earth Reference Frame)
    u_wake = earth_dir_wake / np.linalg.norm(earth_dir_wake)
    elev_wake = np.degrees(np.arcsin(u_wake[2]))
    azim_wake = np.degrees(np.arctan2(u_wake[1], u_wake[0]))
    ax2.view_init(elev=elev_wake, azim=azim_wake)

    # HUD Box B
    hud_wake = (
        f"★ SIMULATION STATE B: ACTIVE CONTACT ★\n"
        f"-----------------------------------------\n"
        f"Target UTC:      {rx[wake_idx]['utc'][:-4]}\n"
        f"Link Range:      {tx[wake_idx]['distance_km']:.1f} km\n"
        f"Prop Delay:      {tx[wake_idx]['light_time_sec']:.3f} s\n"
        f"LOS Clearance:   {rx[wake_idx]['min_altitude_km']:.1f} km (Direct LOS)\n"
        f"FSM State:       {rx[wake_idx]['fsm_state']}\n"
        f"Power gated:     {rx[wake_idx]['power_w']:.2f} W (ACTIVE TRANSCEIVE)\n"
        f"MOSFET Switch:   CLOSED (Active)"
    )
    fig.text(0.55, 0.03, hud_wake, fontsize=9.0, family='monospace', color='black',
             bbox=dict(boxstyle="round,pad=0.6", facecolor='#fcfcfc', edgecolor='#d0d0d0', alpha=0.95))

    plt.suptitle("3D Martian Orbital Simulation Output: Occulted vs. Active Gating States (SPICE Engine)", fontsize=15, y=0.96, color='black', weight='bold')
    
    os.makedirs(FIG_DIR, exist_ok=True)
    output_png = os.path.join(FIG_DIR, "scenario_orbit.png")
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated 3D Scenario simulation snapshot plot: {output_png}")
    spice.clpool()

def plot_pointing_error(tx, rx):
    """
    Plots the pointing displacement error at Mars over time for corrected vs naive systems.
    """
    time_hours = np.array([e["et"] - rx[0]["et"] for e in rx]) / 3600.0
    disp_naive = np.array([e["disp_naive_km"] for e in rx])
    disp_corrected = np.array([e["disp_corrected_km"] * 1000.0 for e in rx])  # convert to meters
    beam_radius = np.array([e["beam_radius_km"] for e in rx])
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    
    # Plot Naive displacement vs Beam Footprint (in km)
    ax1.plot(time_hours, disp_naive, color=COLOR_SECONDARY, linewidth=2.0, label='Strategy A: Naive Tracking (No LT Correction)')
    ax1.plot(time_hours, beam_radius, color=COLOR_PRIMARY, linewidth=1.5, linestyle='--', label='Laser Beam Footprint Radius')
    ax1.set_ylabel("Displacement at Mars Orbit (km)", color='black', fontsize=14)
    ax1.set_title("Pointing Displacement comparison: Naive vs. SPICE Point-Ahead Correction", fontsize=13, weight='bold', pad=10, color='black')
    ax1.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='#e0e0e0', labelcolor='black', fontsize=12)
    ax1.grid(True)
    
    # Plot Corrected displacement (in meters)
    ax2.plot(time_hours, disp_corrected, color=COLOR_PRIMARY, linewidth=2.0, label='Strategy B: SPICE Point-Ahead Correction')
    ax2.set_ylabel("Displacement at Mars Orbit (meters)", color='black', fontsize=14)
    ax2.set_xlabel("Simulation Elapsed Time (hours)", color='black', fontsize=14)
    ax2.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='#e0e0e0', labelcolor='black', fontsize=12)
    ax2.grid(True)
    
    # Shade successful hit periods for corrected beam
    for i in range(len(rx) - 1):
        if rx[i]["signal_captured"]:
            ax1.axvspan(time_hours[i], time_hours[i+1], color='#2ca02c', alpha=0.1)
            ax2.axvspan(time_hours[i], time_hours[i+1], color='#2ca02c', alpha=0.1)
            
    plt.tight_layout()
    os.makedirs(FIG_DIR, exist_ok=True)
    output_png = os.path.join(FIG_DIR, "pointing_error.png")
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated Pointing Error metric plot: {output_png}")

def plot_energy_savings(rx):
    """
    Plots the energy consumption savings over time: Always-On vs. proposed Wake-on-Beacon FSM.
    """
    time_sec = np.array([e["et"] - rx[0]["et"] for e in rx])
    time_hours = time_sec / 3600.0
    
    # Power vectors
    power_wob = np.array([e["power_w"] for e in rx])
    
    # Always-On System
    power_always = np.zeros_like(power_wob)
    for i in range(len(rx)):
        if rx[i]["fsm_state"] == STATE_ACTIVE_SESSION:
            power_always[i] = 15.0
        else:
            power_always[i] = 10.0  # active listening standby
            
    # Integrate energy (J = W * sec)
    dt_sec = time_sec[1] - time_sec[0] if len(time_sec) > 1 else 60.0
    energy_always_kj = np.cumsum(power_always * dt_sec) / 1e3
    energy_wob_kj = np.cumsum(power_wob * dt_sec) / 1e3
    
    # Savings calculation
    final_always_wh = (energy_always_kj[-1] * 1e3) / 3600.0
    final_wob_wh = (energy_wob_kj[-1] * 1e3) / 3600.0
    percent_savings = (1.0 - (final_wob_wh / final_always_wh)) * 100.0
    
    fig, ax1 = plt.subplots(figsize=(11, 6))
    
    ax1.plot(time_hours, energy_always_kj, color=COLOR_SECONDARY, linewidth=2.2, label='Always-On Active Listening Receiver (Conventional)')
    ax1.plot(time_hours, energy_wob_kj, color=COLOR_PRIMARY, linewidth=2.2, label='Asynchronous Wake-on-Beacon FSM Receiver (Proposed)')
    
    ax1.set_ylabel("Cumulative Energy Consumption (Kilojoules)", color='black', fontsize=14)
    ax1.set_xlabel("Simulation Elapsed Time (hours)", color='black', fontsize=14)
    ax1.set_title(f"Cumulative Satellite Energy Budget Savings: {percent_savings:.4f}% preserved", fontsize=14, weight='bold', pad=15, color='black')
    ax1.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#e0e0e0', labelcolor='black', fontsize=12)
    ax1.grid(True)
    
    # Inset FSM power timeline
    ax2 = ax1.twinx()
    ax2.plot(time_hours, power_wob, color=COLOR_FSM, alpha=0.3, linewidth=1.0, linestyle=':')
    ax2.set_ylabel("Active Power State (Watts) [Purple Dotted Line]", color=COLOR_FSM, fontsize=12)
    ax2.tick_params(axis='y', labelcolor=COLOR_FSM)
    
    # Add key results in text box
    savings_text = (
        f"★ Energy Analysis Summary ★\n"
        f"Always-On Energy: {final_always_wh:.2f} Wh\n"
        f"Wake-on-Beacon:  {final_wob_wh:.2f} Wh\n"
        f"Total Savings:   {percent_savings:.4f}%"
    )
    ax1.text(0.68, 0.12, savings_text, transform=ax1.transAxes, fontsize=10, family='monospace', color='black',
             bbox=dict(boxstyle="round,pad=0.8", facecolor='#fcfcfc', edgecolor='#e0e0e0'))
             
    plt.tight_layout()
    os.makedirs(FIG_DIR, exist_ok=True)
    output_png = os.path.join(FIG_DIR, "energy_savings.png")
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated Energy Savings metric plot: {output_png}")

def plot_link_budget(tx, rx):
    """
    Computes and plots received optical power (dBm) and electrical SNR (dB)
    over time for corrected vs naive pointing.
    """
    time_hours = np.array([e["et"] - rx[0]["et"] for e in rx]) / 3600.0
    
    # Constants
    P_tx = 10.0e6           # 10 MW peak pulsed transmitter power (W)
    A_rx = 7.85e-3          # 10 cm collector aperture lens area (m^2)
    eta_opt = 0.7           # Optics transmission efficiency
    responsivity = 0.6      # Silicon PIN responsivity (A/W) at 905nm
    sigma_noise = 3.56e-11  # Total electrical noise current (A)
    threshold_db = 12.0     # Minimum signal decoding SNR threshold (dB)
    
    p_rx_corrected_dbm = []
    snr_corrected_db = []
    p_rx_naive_dbm = []
    snr_naive_db = []
    
    for i in range(len(rx)):
        e_rx = rx[i]
        e_tx = tx[i]
        
        is_occulted = e_rx["is_occulted"]
        incidence_angle = e_rx["incidence_angle_deg"]
        disp_corrected = e_rx["disp_corrected_km"] * 1e3 # m
        disp_naive = e_rx["disp_naive_km"] * 1e3 # m
        beam_radius = e_rx["beam_radius_km"] * 1e3 # m
        
        # incidence loss
        cos_inc = np.cos(np.radians(incidence_angle))
        if incidence_angle > 60.0 or cos_inc <= 0.0:
            cos_inc = 0.0
            
        # CORRECTED STRATEGY
        if is_occulted or cos_inc == 0.0:
            p_rx_c = 0.0
            snr_c = -100.0
        else:
            # Gaussian beam profile
            I_c = (2.0 * P_tx * eta_opt) / (np.pi * beam_radius**2) * np.exp(-2.0 * (disp_corrected / beam_radius)**2)
            p_rx_c = I_c * A_rx * cos_inc
            i_sig_c = responsivity * p_rx_c
            snr_c = 20.0 * np.log10(i_sig_c / sigma_noise) if i_sig_c > 0.0 else -100.0
            
        # NAIVE STRATEGY
        if is_occulted or cos_inc == 0.0:
            p_rx_n = 0.0
            snr_n = -100.0
        else:
            I_n = (2.0 * P_tx * eta_opt) / (np.pi * beam_radius**2) * np.exp(-2.0 * (disp_naive / beam_radius)**2)
            p_rx_n = I_n * A_rx * cos_inc
            i_sig_n = responsivity * p_rx_n
            snr_n = 20.0 * np.log10(i_sig_n / sigma_noise) if i_sig_n > 0.0 else -100.0
            
        # Convert power to dBm (10*log10(P/1mW))
        p_dbm_c = 10.0 * np.log10(p_rx_c / 1e-3) if p_rx_c > 0.0 else -150.0
        p_dbm_n = 10.0 * np.log10(p_rx_n / 1e-3) if p_rx_n > 0.0 else -150.0
        
        # bound values for clean plotting
        p_rx_corrected_dbm.append(max(p_dbm_c, -140.0))
        snr_corrected_db.append(max(snr_c, -20.0))
        p_rx_naive_dbm.append(max(p_dbm_n, -140.0))
        snr_naive_db.append(max(snr_n, -20.0))
        
    p_rx_corrected_dbm = np.array(p_rx_corrected_dbm)
    snr_corrected_db = np.array(snr_corrected_db)
    p_rx_naive_dbm = np.array(p_rx_naive_dbm)
    snr_naive_db = np.array(snr_naive_db)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    
    # 1. Received Power Plot
    ax1.plot(time_hours, p_rx_corrected_dbm, color=COLOR_PRIMARY, linewidth=2.0, label='Strategy B: SPICE Corrected Point-Ahead')
    ax1.plot(time_hours, p_rx_naive_dbm, color=COLOR_SECONDARY, linewidth=1.5, label='Strategy A: Naive Tracking')
    ax1.axhline(-110.0, color='gray', linestyle=':', label='Receiver Sensitivity Floor (-110 dBm)')
    ax1.set_ylabel("Received Optical Power (dBm)", color='black', fontsize=14)
    ax1.set_title("Interplanetary Link Budget: Received Optical Power & Electrical SNR at Mars", fontsize=13, weight='bold', pad=10, color='black')
    ax1.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='#e0e0e0', labelcolor='black', fontsize=12)
    ax1.grid(True)
    
    # 2. SNR Plot
    ax2.plot(time_hours, snr_corrected_db, color=COLOR_PRIMARY, linewidth=2.0, label='Strategy B: SPICE Corrected SNR')
    ax2.plot(time_hours, snr_naive_db, color=COLOR_SECONDARY, linewidth=1.5, label='Strategy A: Naive SNR')
    ax2.axhline(threshold_db, color='darkgreen', linestyle='--', linewidth=1.5, label=f'FSM Detection Threshold ({threshold_db} dB)')
    ax2.set_ylabel("Electrical Signal-to-Noise Ratio (dB)", color='black', fontsize=14)
    ax2.set_xlabel("Simulation Elapsed Time (hours)", color='black', fontsize=14)
    ax2.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='#e0e0e0', labelcolor='black', fontsize=12)
    ax2.grid(True)
    
    # Shade successful hit periods
    for i in range(len(rx) - 1):
        if rx[i]["signal_captured"]:
            ax1.axvspan(time_hours[i], time_hours[i+1], color='#2ca02c', alpha=0.1)
            ax2.axvspan(time_hours[i], time_hours[i+1], color='#2ca02c', alpha=0.1)
            
    plt.tight_layout()
    os.makedirs(FIG_DIR, exist_ok=True)
    output_png = os.path.join(FIG_DIR, "link_budget.png")
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated Link Budget metric plot: {output_png}")

if __name__ == "__main__":
    tx, rx = load_data()
    plot_scenario_3d(tx, rx)
    plot_pointing_error(tx, rx)
    plot_energy_savings(rx)
    plot_link_budget(tx, rx)
    print("--- Analysis & Plotting Finished Successfully ---")
