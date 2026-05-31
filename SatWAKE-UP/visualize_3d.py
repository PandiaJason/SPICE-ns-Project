# visualize_3d.py
"""
Laser Inter-Satellite Link (ISL) Wake-on-Beacon IoT Simulator
Interactive 3D Scenario Animation & Mobility Recreator (Academic White Theme)

This script loads the transmitter and receiver logs, animates the orbital trajectories,
and models the physical propagation of the wake-up laser pulse across deep space
and its subsequent hit or miss on the Mars Orbiter using publication-grade styles.
All figures are saved under paper/.
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
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

# Premium academic plotting styles
plt.style.use('default')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['text.color'] = 'black'
plt.rcParams['axes.labelcolor'] = 'black'
plt.rcParams['xtick.color'] = 'black'
plt.rcParams['ytick.color'] = 'black'

# Curated high-contrast color palette
COLOR_PRIMARY = '#008877'      # Rich Dark Teal (Corrected / Laser Beam)
COLOR_SECONDARY = '#d62728'    # Crimson Red (Naive / Error)
COLOR_MARS = '#e2583e'         # Terracotta Orange (Mars)
COLOR_EARTH = '#1f77b4'        # Deep Royal Blue (Earth)
COLOR_SAT = '#2ca02c'          # Rich Green (Satellite)

def load_data():
    with open(TX_LOG_PATH, "r") as f:
        tx = json.load(f)
    with open(RX_LOG_PATH, "r") as f:
        rx = json.load(f)
    return tx, rx

def generate_animation():
    tx, rx = load_data()
    
    # We will pick the first 6 hours (360 steps) of the 2-Sol simulation log
    # and take every 3rd step to render a smooth, high-fidelity 120-frame animation.
    step_skip = 3
    tx_anim = tx[0:360:step_skip]
    rx_anim = rx[0:360:step_skip]
    
    num_frames = len(tx_anim)
    
    # Pre-load orbital tracks for Mars and Earth in SSB
    spice.furnsh(os.path.join(KERNELS_DIR, "de440.bsp"))
    spice.furnsh(os.path.join(KERNELS_DIR, "naif0012.tls"))
    
    t_start = rx_anim[0]["et"]
    t_end = rx_anim[-1]["et"]
    t_arr = np.linspace(t_start, t_end, 200)
    
    earth_track = []
    mars_track = []
    for t in t_arr:
        e_state, _ = spice.spkezr('EARTH', t, 'J2000', 'NONE', 'SSB')
        m_state, _ = spice.spkezr('MARS BARYCENTER', t, 'J2000', 'NONE', 'SSB')
        earth_track.append(e_state[:3])
        mars_track.append(m_state[:3])
        
    earth_track = np.array(earth_track)
    mars_track = np.array(mars_track)
    
    # Setup Figure and Subplots (Height increased and margins compressed to make space for bottom HUD)
    fig = plt.figure(figsize=(15, 8.5))
    plt.subplots_adjust(bottom=0.22, top=0.90, left=0.06, right=0.94)
    
    # Panel 1: Heliocentric Interplanetary scale
    ax1 = fig.add_subplot(121, projection='3d')
    ax1.set_facecolor('white')
    ax1.xaxis.set_pane_color((0.98, 0.98, 0.98, 1.0))
    ax1.yaxis.set_pane_color((0.98, 0.98, 0.98, 1.0))
    ax1.zaxis.set_pane_color((0.98, 0.98, 0.98, 1.0))
    ax1.set_title("1. Interplanetary Scale (Earth to Mars)", color='black', fontsize=12, pad=10, weight='bold')
    
    # Panel 2: Martian Local scale
    ax2 = fig.add_subplot(122, projection='3d')
    ax2.set_facecolor('white')
    ax2.xaxis.set_pane_color((0.98, 0.98, 0.98, 1.0))
    ax2.yaxis.set_pane_color((0.98, 0.98, 0.98, 1.0))
    ax2.zaxis.set_pane_color((0.98, 0.98, 0.98, 1.0))
    ax2.set_title("2. Close-up: Martian Satellite Orbit & Hit Check", color='black', fontsize=12, pad=10, weight='bold')
    
    # --- Initialize Heliocentric Artists ---
    # Static orbital segments
    ax1.plot(earth_track[:, 0], earth_track[:, 1], earth_track[:, 2], color=COLOR_EARTH, alpha=0.3, linestyle='--', label="Earth Orbit Segment")
    ax1.plot(mars_track[:, 0], mars_track[:, 1], mars_track[:, 2], color=COLOR_MARS, alpha=0.3, linestyle='--', label="Mars Orbit Segment")
    
    # Moving dots
    earth_dot, = ax1.plot([], [], [], 'o', color=COLOR_EARTH, markersize=8, markeredgecolor='black', label="Earth DSN")
    mars_dot, = ax1.plot([], [], [], 'o', color=COLOR_MARS, markersize=8, markeredgecolor='black', label="Mars Center")
    
    # Propagating laser pulse on global scale
    global_laser_line, = ax1.plot([], [], [], color=COLOR_PRIMARY, linewidth=2.0, linestyle=':', label="Laser Packet")
    
    # Bounds for heliocentric
    center_x = (np.mean(earth_track[:, 0]) + np.mean(mars_track[:, 0])) / 2.0
    center_y = (np.mean(earth_track[:, 1]) + np.mean(mars_track[:, 1])) / 2.0
    center_z = (np.mean(earth_track[:, 2]) + np.mean(mars_track[:, 2])) / 2.0
    span = np.max(np.abs(earth_track - mars_track)) * 0.6
    
    ax1.set_xlim(center_x - span, center_x + span)
    ax1.set_ylim(center_y - span, center_y + span)
    ax1.set_zlim(center_z - span, center_z + span)
    ax1.set_xlabel("SSB X (km)", fontsize=9, color='black')
    ax1.set_ylabel("SSB Y (km)", fontsize=9, color='black')
    ax1.legend(loc="upper left", frameon=True, facecolor='white', edgecolor='#e0e0e0', labelcolor='black', fontsize=8)
    
    # --- Initialize Martian Local Artists ---
    # Static Mars sphere
    u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
    x_mars = MARS_RADIUS_KM * np.cos(u) * np.sin(v)
    y_mars = MARS_RADIUS_KM * np.sin(u) * np.sin(v)
    z_mars = MARS_RADIUS_KM * np.cos(v)
    ax2.plot_surface(x_mars, y_mars, z_mars, color='#e2583e', alpha=0.3, edgecolor='#993300', linewidth=0.3)
    
    # Full satellite orbit path split into visible and occulted segments
    sat_full_pos = np.array([e["sat_pos_rel_mars_j2000"] for e in rx])
    
    def is_point_occulted(p, earth_dir):
        u_earth = earth_dir / np.linalg.norm(earth_dir)
        proj = np.dot(p, u_earth)
        if proj >= 0:
            return False
        d2 = np.dot(p, p) - proj**2
        return d2 < MARS_RADIUS_KM**2

    # Split using the start-state Earth pointing vector
    earth_dir_start = -np.array(tx_anim[0]["pointing_vector_j2000"])
    
    segments = []
    current_seg = [sat_full_pos[0]]
    current_occ = is_point_occulted(sat_full_pos[0], earth_dir_start)
    
    for p in sat_full_pos[1:]:
        occ = is_point_occulted(p, earth_dir_start)
        if occ == current_occ:
            current_seg.append(p)
        else:
            segments.append((np.array(current_seg), current_occ))
            current_seg = [p]
            current_occ = occ
    segments.append((np.array(current_seg), current_occ))
    
    for seg, occ in segments:
        if occ:
            # Faded dashed line for occulted part of orbit behind Mars from Earth
            ax2.plot(seg[:, 0], seg[:, 1], seg[:, 2], color='#d3d3d3', linewidth=1.0, linestyle='--', alpha=0.35)
        else:
            # Solid line for visible part of orbit
            ax2.plot(seg[:, 0], seg[:, 1], seg[:, 2], color=COLOR_SAT, linewidth=1.2, linestyle='-', alpha=0.35)
    
    # Dynamic satellite dot
    sat_dot, = ax2.plot([], [], [], 'o', color=COLOR_SAT, markersize=6, markeredgecolor='black', zorder=5, label="Mars Satellite")
    
    # Local incoming laser path
    local_laser_line, = ax2.plot([], [], [], color=COLOR_PRIMARY, linewidth=2.2, label="SPICE Point-Ahead (Hit)")
    local_naive_line, = ax2.plot([], [], [], color=COLOR_SECONDARY, linewidth=1.5, linestyle='--', label="Naive Tracking (Miss)")
    
    # Display annotations (Global figure text box placed at bottom-right)
    hud_text = fig.text(0.94, 0.02, "", family='monospace', fontsize=8.5, color='black',
                        ha='right', va='bottom',
                        bbox=dict(boxstyle="round,pad=0.6", facecolor='#fcfcfc', edgecolor='#d0d0d0', alpha=0.95))
    
    # Bounds for local Mars
    max_range = A_KM * 1.4
    ax2.set_xlim(-max_range, max_range)
    ax2.set_ylim(-max_range, max_range)
    ax2.set_zlim(max_range, -max_range)
    ax2.set_xlabel("Mars X (km)", fontsize=9, color='black')
    ax2.set_ylabel("Mars Y (km)", fontsize=9, color='black')
    ax2.legend(loc="lower left", frameon=True, facecolor='white', edgecolor='#e0e0e0', labelcolor='black', fontsize=8)
    
    # --- Animation Update Loop ---
    def update(frame):
        tx_f = tx_anim[frame]
        rx_f = rx_anim[frame]
        
        # 1. Update Heliocentric Scale
        earth_pos = np.array(tx_f["earth_pos_fire_j2000"])
        sat_pos_ssb = np.array(tx_f["sat_pos_rec_j2000"])
        
        earth_dot.set_data([earth_pos[0]], [earth_pos[1]])
        earth_dot.set_3d_properties([earth_pos[2]])
        
        mars_pos_ssb = sat_pos_ssb - np.array(rx_f["sat_pos_rel_mars_j2000"])
        mars_dot.set_data([mars_pos_ssb[0]], [mars_pos_ssb[1]])
        mars_dot.set_3d_properties([mars_pos_ssb[2]])
        
        # 2. Extract Occultation and Hit parameters earlier for logical gates
        is_occ = rx_f["is_occulted"]
        is_hit = rx_f["signal_captured"]

        # Animate laser pulse crossing SSB space ONLY if Earth can see the satellite (not occulted)
        if is_occ:
            global_laser_line.set_data([], [])
            global_laser_line.set_3d_properties([])
        else:
            global_laser_line.set_data([earth_pos[0], sat_pos_ssb[0]], [earth_pos[1], sat_pos_ssb[1]])
            global_laser_line.set_3d_properties([earth_pos[2], sat_pos_ssb[2]])
        
        # 3. Update Martian Local Scale
        sat_pos_local = np.array(rx_f["sat_pos_rel_mars_j2000"])
        sat_dot.set_data([sat_pos_local[0]], [sat_pos_local[1]])
        sat_dot.set_3d_properties([sat_pos_local[2]])
        if is_occ:
            sat_dot.set_alpha(0.15)
            sat_dot.set_color('#7f7f7f')  # faded grey when occulted
        else:
            sat_dot.set_alpha(1.0)
            sat_dot.set_color(COLOR_SAT)  # full color when visible
        
        if is_occ:
            local_laser_line.set_data([], [])
            local_laser_line.set_3d_properties([])
            local_naive_line.set_data([], [])
            local_naive_line.set_3d_properties([])
        else:
            # Laser incoming ray directions
            earth_dir = -np.array(tx_f["pointing_vector_j2000"])
            naive_dir = -np.array(tx_f["naive_pointing_vector_j2000"])
            beam_len = 10000.0  # km
            
            # Corrected beam path line (Strategy B)
            local_laser_line.set_data([sat_pos_local[0] - earth_dir[0]*beam_len, sat_pos_local[0]],
                                      [sat_pos_local[1] - earth_dir[1]*beam_len, sat_pos_local[1]])
            local_laser_line.set_3d_properties([sat_pos_local[2] - earth_dir[2]*beam_len, sat_pos_local[2]])
            
            # Naive path line (Strategy A)
            naive_target = sat_pos_local + (naive_dir - earth_dir) * d_sat_calc(tx_f)
            local_naive_line.set_data([naive_target[0] - naive_dir[0]*beam_len, naive_target[0] + naive_dir[0]*beam_len],
                                      [naive_target[1] - naive_dir[1]*beam_len, naive_target[1] + naive_dir[1]*beam_len])
            local_naive_line.set_3d_properties([naive_target[2] - naive_dir[2]*beam_len, naive_target[2] + naive_dir[2]*beam_len])
        
        # Row-by-row elements with static character lengths to prevent separator jitter
        # Row-by-row elements with static character lengths to prevent separator jitter
        # Column 1: Common Link and Space Medium
        lines1_0 = "  * LINK & SPACE MEDIUM"
        utc_str = rx_f['utc'][:-4]
        lines1_1 = f"    Target UTC:   {utc_str:<19}"
        dist_val = f"{tx_f['distance_km']:.1f} km"
        lines1_2 = f"    Link Range:   {dist_val:<19}"
        delay_val = f"{tx_f['light_time_sec']:.3f} s"
        lines1_3 = f"    One-Way Delay:{delay_val:<19}"
        lines1_4 = f"    Laser Medium: 905 nm Light"
        inc_val = f"{rx_f['incidence_angle_deg']:.2f} deg"
        lines1_5 = f"    Solar Ang/Inc:{inc_val:<18}"
        
        # Column 2: Earth Beacon Transmitter
        lines2_0 = "  * EARTH BEACON TRANSMITTER"
        lines2_1 = f"    Targeting:    Strategy B (SPICE)"
        b_offset_val = f"{rx_f['disp_corrected_km']*1e3:.2f} m"
        hit_val = "HIT" if is_hit else "MISS"
        lines2_2 = f"    Point-Ahead:  {b_offset_val:<9} ({hit_val:<4})"
        a_offset_val = f"{rx_f['disp_naive_km']:.1f} km"
        lines2_3 = f"    Naive Offset: {a_offset_val:<9} (MISS)"
        spot_val = f"{rx_f['beam_radius_km']:.2f} km"
        lines2_4 = f"    Spot Radius:  {spot_val:<18}"
        tx_occ_val = "YES (GATE OFF)" if is_occ else "NO (GATE ON)"
        lines2_5 = f"    Occultation:  {tx_occ_val:<18}"
        
        # Column 3: Satellite Photo Receiver
        lines3_0 = "  * SATELLITE PHOTO RECEIVER"
        fsm_val = rx_f['fsm_state']
        lines3_1 = f"    FSM State:    {fsm_val:<15}"
        occ_val = "YES (ECLIPSE)" if is_occ else "NO (LIGHT PASS)"
        lines3_2 = f"    Occultation:  {occ_val:<15}"
        p_val = rx_f['power_w']
        p_str = f"{p_val*1e6:.1f} uW" if p_val < 0.001 else (f"{p_val*1e3:.1f} mW" if p_val < 1.0 else f"{p_val:.2f} W")
        lines3_3 = f"    Power Gated:  {p_str:<15}"
        gate_val = "CLOSED (ACTIVE)" if fsm_val in ["ACTIVE_SESSION", "BOOT_RAIL"] else "OPEN (STANDBY)"
        lines3_4 = f"    MOSFET Switch:{gate_val:<15}"
        token_val = "WOB_KEY_VALID" if is_hit else ("NO_SIGNAL_OCC" if is_occ else "NO_BEACON_DET")
        lines3_5 = f"    Decoded Token:{token_val:<15}"
        
        # Combine columns side-by-side with mathematically guaranteed fixed widths
        row0 = f"{lines1_0:<38} │ {lines2_0:<40} │ {lines3_0:<36}"
        row1 = f"{lines1_1:<38} │ {lines2_1:<40} │ {lines3_1:<36}"
        row2 = f"{lines1_2:<38} │ {lines2_2:<40} │ {lines3_2:<36}"
        row3 = f"{lines1_3:<38} │ {lines2_3:<40} │ {lines3_3:<36}"
        row4 = f"{lines1_4:<38} │ {lines2_4:<40} │ {lines3_4:<36}"
        row5 = f"{lines1_5:<38} │ {lines2_5:<40} │ {lines3_5:<36}"
        
        divider = "─" * 120
        box_text = f"{row0}\n{divider}\n{row1}\n{row2}\n{row3}\n{row4}\n{row5}"
        
        hud_text.set_text(box_text)
        
        return earth_dot, mars_dot, global_laser_line, sat_dot, local_laser_line, local_naive_line, hud_text

    def d_sat_calc(tx_rec):
        return tx_rec["distance_km"]

    # Rotate perspective slowly for rich premium visual feel
    def animate_view(i):
        # Heliocentric view rotates slowly
        ax1.view_init(elev=15, azim=i*0.5)
        
        # Close-up Martian view is projected dynamically from Earth's viewpoint on Mars
        tx_f = tx_anim[i]
        pointing_vector = np.array(tx_f["pointing_vector_j2000"])
        earth_dir = -pointing_vector
        earth_dir = earth_dir / np.linalg.norm(earth_dir)
        elev_e = np.degrees(np.arcsin(earth_dir[2]))
        azim_e = np.degrees(np.arctan2(earth_dir[1], earth_dir[0]))
        ax2.view_init(elev=elev_e, azim=azim_e)
        
    def final_update(frame):
        animate_view(frame)
        return update(frame)

    print("Generating 3D trajectory animation frames...")
    ani = animation.FuncAnimation(fig, final_update, frames=num_frames, interval=100, blit=False)
    
    # Save as high-quality GIF
    os.makedirs(FIG_DIR, exist_ok=True)
    gif_path = os.path.join(FIG_DIR, "simulation_animation.gif")
    print(f"Saving animation to {gif_path} (this may take a few seconds)...")
    ani.save(gif_path, writer='pillow', fps=10)
    print("Animation saved successfully.")
    
    spice.clpool()

if __name__ == "__main__":
    generate_animation()
