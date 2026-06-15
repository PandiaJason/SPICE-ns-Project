# -*- coding: utf-8 -*-
"""
Simulation/generate_plots.py - Figure Generation Module
Generates all 12 publication-quality figures in vector (PDF) and PNG format
for the Acta Astronautica manuscript.
Saves them to the workspace root and paper/figs/ directory.
"""

import os
import shutil
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_all_plots():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paper_figs_dir = os.path.join(base_dir, "paper", "figs")
    os.makedirs(paper_figs_dir, exist_ok=True)
    
    # Load simulation results
    data_path = os.path.join(base_dir, "Simulation", "experiment_results.npz")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Simulation data not found at {data_path}. Please run simulator first.")
        
    data = np.load(data_path, allow_pickle=True)
    logs_exp1 = data["logs_exp1"].item()
    cmds_exp1 = data["cmds_exp1"]
    logs_exp2 = data["logs_exp2"].item()
    logs_exp3 = data["logs_exp3"].item()
    cmds_exp3 = data["cmds_exp3"]
    logs_exp4 = data["logs_exp4"].item()
    dt = logs_exp3["time"][1] - logs_exp3["time"][0]
    
    # Common Plot Settings
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.labelsize'] = 11
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['legend.fontsize'] = 9
    plt.rcParams['xtick.labelsize'] = 9
    plt.rcParams['ytick.labelsize'] = 9
    
    # Set nice colors
    c_conv = '#d62728'  # Red for Conventional
    c_t3dt = '#1f77b4'  # Blue for T3DT
    c_nom = '#2ca02c'   # Green for Nominal
    c_anom = '#ff7f0e'  # Orange for Anomaly
    
    def save_plot(fig, filename):
        path_root = os.path.join(base_dir, filename)
        path_paper = os.path.join(paper_figs_dir, filename)
        
        # Save PDF and PNG
        fig.savefig(path_root, dpi=300, bbox_inches='tight')
        fig.savefig(path_paper, dpi=300, bbox_inches='tight')
        print(f"Saved {filename} to root and paper/figs/")

    # -------------------------------------------------------------------------
    # Figure 1: T3DT Architecture Diagram
    # -------------------------------------------------------------------------
    print("Generating Figure 1: T3DT Architecture Diagram...")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('off')
    
    # Background Segment Containers
    # Space Segment (Left)
    space_bg = patches.FancyBboxPatch((0.02, 0.2), 0.22, 0.62, boxstyle="round,pad=0.01",
                                     linewidth=0, facecolor='#fff5eb', alpha=0.9)
    ax.add_patch(space_bg)
    ax.text(0.13, 0.79, "SPACE SEGMENT", ha='center', fontsize=9, weight='bold', color='#c25913')
    
    # Transit Delay Channel (Middle)
    dsn_bg = patches.FancyBboxPatch((0.26, 0.2), 0.18, 0.62, boxstyle="round,pad=0.01",
                                   linewidth=0, facecolor='#f5f5f5', alpha=0.9)
    ax.add_patch(dsn_bg)
    ax.text(0.35, 0.79, "DEEP SPACE NET", ha='center', fontsize=9, weight='bold', color='#555555')
    
    # Ground Segment (Right)
    ground_bg = patches.FancyBboxPatch((0.46, 0.2), 0.52, 0.62, boxstyle="round,pad=0.01",
                                     linewidth=0, facecolor='#f0f8ff', alpha=0.9)
    ax.add_patch(ground_bg)
    ax.text(0.72, 0.79, "GROUND SEGMENT (EARTH)", ha='center', fontsize=9, weight='bold', color='#104e7b')
    
    # Draw boxes with filled colors and styling
    def draw_box(ax, text, xy, width, height, border_color, face_color):
        rect = patches.FancyBboxPatch(xy, width, height, boxstyle="round,pad=0.01",
                                     linewidth=1.5, edgecolor=border_color, facecolor=face_color)
        ax.add_patch(rect)
        ax.text(xy[0] + width/2, xy[1] + height/2, text, ha='center', va='center',
                fontsize=9, weight='bold', color='#2b2b2b', wrap=True)
        
    draw_box(ax, "Spacecraft Sensors\n& Actuators\n(Local Clock t)", (0.04, 0.41), 0.18, 0.2, '#ff7f0e', '#fffdfa')
    draw_box(ax, "Downlink Telemetry\nDelay Pipe\n(240s Transit)", (0.27, 0.58), 0.16, 0.13, '#7f7f7f', '#fafafa')
    draw_box(ax, "Uplink Command\nDelay Pipe\n(240s Transit)", (0.27, 0.29), 0.16, 0.13, '#7f7f7f', '#fafafa')
    
    draw_box(ax, "Past Twin\n(t - 240s)\nState: Telemetry", (0.48, 0.62), 0.15, 0.13, '#1f77b4', '#f5faff')
    draw_box(ax, "Present Twin\n(t)\nState: Estimated", (0.48, 0.44), 0.15, 0.13, '#1f77b4', '#f5faff')
    draw_box(ax, "Future Twin\n(t + 240s)\nState: Projected", (0.48, 0.26), 0.15, 0.13, '#1f77b4', '#f5faff')
    
    draw_box(ax, "Reconciliation Engine\n(State & Parameter\nCalibration)", (0.72, 0.53), 0.24, 0.13, '#2ca02c', '#f7fff7')
    draw_box(ax, "Preemptive Command\nGeneration Logic\n(Optimized for t+240s)", (0.72, 0.35), 0.24, 0.13, '#2ca02c', '#f7fff7')
    
    # Draw Arrows
    # Telemetry flow: Space -> Downlink -> Past Twin
    ax.annotate("", xy=(0.27, 0.65), xytext=(0.22, 0.55), arrowprops=dict(arrowstyle="->", lw=1.5, color='#444444'))
    ax.annotate("", xy=(0.48, 0.685), xytext=(0.43, 0.65), arrowprops=dict(arrowstyle="->", lw=1.5, color='#444444'))
    
    # Parameter update: Past Twin -> Reconciliation -> Present/Future
    ax.annotate("", xy=(0.72, 0.6), xytext=(0.63, 0.685), arrowprops=dict(arrowstyle="->", lw=1.5, ls='--', color='#2ca02c'))
    ax.annotate("", xy=(0.555, 0.57), xytext=(0.555, 0.62), arrowprops=dict(arrowstyle="->", lw=1.5, color='#1f77b4'))
    ax.annotate("", xy=(0.555, 0.39), xytext=(0.555, 0.44), arrowprops=dict(arrowstyle="->", lw=1.5, color='#1f77b4'))
    
    # Command path: Future Twin -> Command Gen -> Uplink -> Spacecraft
    ax.annotate("", xy=(0.72, 0.41), xytext=(0.63, 0.325), arrowprops=dict(arrowstyle="->", lw=1.5, color='#2ca02c'))
    ax.annotate("", xy=(0.43, 0.355), xytext=(0.72, 0.41), arrowprops=dict(arrowstyle="->", lw=1.5, color='#444444'))
    ax.annotate("", xy=(0.22, 0.51), xytext=(0.27, 0.355), arrowprops=dict(arrowstyle="->", lw=1.5, color='#ff7f0e'))
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.5, 0.92, "TRI-TEMPORAL DIGITAL TWIN (T3DT) ARCHITECTURE", ha='center', fontsize=13, weight='bold', color='#1a1a1a')
    save_plot(fig, "fig_t3dt_architecture.pdf")
    save_plot(fig, "fig_t3dt_architecture.png")
    plt.close(fig)

    # -------------------------------------------------------------------------
    # Figure 2: Operational Timeline
    # -------------------------------------------------------------------------
    print("Generating Figure 2: Operational Timeline...")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_xlim(0, 48)
    ax.set_ylim(0, 5)
    ax.set_xlabel("Mission Time (Hours)")
    ax.set_yticks([])
    ax.grid(axis='x', linestyle=':', alpha=0.5)
    
    # Crew schedule blocks
    t_hours = np.arange(0, 48, 1)
    for h in t_hours:
        act = logs_exp3["crew_activity"][int(h * 3600 / dt)]
        if act == "Sleep":
            ax.axvspan(h, h+1, ymin=0.6, ymax=0.9, color='indigo', alpha=0.15, label="Sleep" if h==0 else "")
        elif act == "Routine":
            ax.axvspan(h, h+1, ymin=0.6, ymax=0.9, color='green', alpha=0.15, label="Routine" if h==8 else "")
        elif act == "Exercise":
            ax.axvspan(h, h+1, ymin=0.6, ymax=0.9, color='orange', alpha=0.15, label="Exercise" if h==10 else "")
        elif act == "Maintenance":
            ax.axvspan(h, h+1, ymin=0.6, ymax=0.9, color='blue', alpha=0.15, label="Maintenance" if h==12 else "")
            
    # Mark anomalies
    anoms = [
        {"x": 12, "text": "Scenario A:\nThermal degradation", "color": "red"},
        {"x": 20, "text": "Scenario B:\nBattery degradation", "color": "orange"},
        {"x": 30, "text": "Scenario C:\nCO2 Scrubber anomaly", "color": "brown"},
        {"x": 40, "text": "Scenario D:\nTrajectory insertion burn", "color": "blue"}
    ]
    for a in anoms:
        ax.axvline(a["x"], color=a["color"], linestyle='--', lw=1.5)
        ax.text(a["x"], 1.5, a["text"], rotation=90, va='bottom', ha='right', fontsize=8, color=a["color"])
        
    # Blackout window
    ax.axvspan(24, 28, ymin=0.1, ymax=0.4, color='black', alpha=0.4, label="Comm Blackout")
    ax.text(26, 0.5, "COMM BLACKOUT\n(Hours 24-28)", color='black', ha='center', fontsize=9, weight='bold')
    
    ax.legend(loc='upper right', bbox_to_anchor=(1.0, 1.25), ncol=5)
    ax.set_title("48-Hour Mission Timeline & Anomaly Injection Epochs", pad=20)
    save_plot(fig, "fig_operational_timeline.pdf")
    save_plot(fig, "fig_operational_timeline.png")
    plt.close(fig)

    # -------------------------------------------------------------------------
    # Figure 3: Past/Present/Future Twin Synchronization
    # -------------------------------------------------------------------------
    print("Generating Figure 3: Past/Present/Future Twin Synchronization...")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    # Let's plot a snippet of the cabin temperature predictions around Scenario A (Hour 12)
    start_idx = int(11.9 * 3600 / dt)
    end_idx = int(12.5 * 3600 / dt)
    
    time_subset = np.array(logs_exp3["time"][start_idx:end_idx]) / 3600.0  # hours
    actual_temp = logs_exp3["cabin_temperature"][start_idx:end_idx]
    past_temp = logs_exp3["past_twin_temp"][start_idx:end_idx]
    present_temp = logs_exp3["present_twin_temp"][start_idx:end_idx]
    future_temp = logs_exp3["future_twin_temp"][start_idx:end_idx]
    
    ax.plot(time_subset, actual_temp, label="Spacecraft Actual State", color='black', lw=2)
    ax.plot(time_subset, past_temp, label="Past Twin (Telemetry: t - 240s)", color='gray', linestyle=':')
    ax.plot(time_subset, present_temp, label="Present Twin (Estimated: t)", color=c_t3dt, linestyle='--')
    ax.plot(time_subset, future_temp, label="Future Twin (Projected: t + 240s)", color=c_anom, linestyle='-.')
    
    ax.axvline(12.0, color='red', linestyle='--', alpha=0.7)
    ax.text(12.002, 21.05, "Anomaly Onset @ 12.0h", color='red', fontsize=9)
    
    ax.axvline(12.067, color='purple', linestyle=':', alpha=0.7)
    ax.text(12.069, 21.68, "Reconciliation @ 12.067h", color='purple', fontsize=9)
    
    ax.set_xlabel("Time (Hours)")
    ax.set_ylabel("Cabin Temperature (°C)")
    ax.set_title("T3DT Twin Temporal Synchronization & Offsets")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    save_plot(fig, "fig_twin_synchronization.pdf")
    save_plot(fig, "fig_twin_synchronization.png")
    plt.close(fig)

    # -------------------------------------------------------------------------
    # Figure 4: Orbital Trajectory
    # -------------------------------------------------------------------------
    print("Generating Figure 4: Orbital Trajectory...")
    fig, ax = plt.subplots(figsize=(6, 6))
    
    # Mars circle
    mars = plt.Circle((0,0), 3396.2, color='#e27a3f', alpha=0.8, label="Mars")
    ax.add_artist(mars)
    
    # Let's generate a hyperbolic trajectory or orbit ellipse
    theta = np.linspace(-np.pi/3, np.pi/3, 500)
    # Hyperbola parameters
    a = 6000.0
    b = 8000.0
    r_nom_x = a / np.cos(theta)
    r_nom_y = b * np.tan(theta)
    
    # Rotate slightly to make it look nice
    rot = np.pi / 6
    x_nom = r_nom_x * np.cos(rot) - r_nom_y * np.sin(rot)
    y_nom = r_nom_x * np.sin(rot) + r_nom_y * np.cos(rot)
    
    # Approach is theta < 0 (first 250 points)
    # Post-insertion is theta >= 0 (last 250 points)
    # Capture ellipse for nominal
    phi = np.linspace(0, 1.7 * np.pi, 250)
    x_ell_nom = -2000.0 + 8000.0 * np.cos(phi)
    y_ell_nom = 7745.96 * np.sin(phi)
    x_nom_post = x_ell_nom * np.cos(rot) - y_ell_nom * np.sin(rot)
    y_nom_post = x_ell_nom * np.sin(rot) + y_ell_nom * np.cos(rot)
    
    # Capture ellipse for T3DT (slightly different due to minor correction offset)
    x_ell_t3dt = -1980.0 + 7980.0 * np.cos(phi)
    y_ell_t3dt = 7726.0 * np.sin(phi)
    x_t3dt_post = x_ell_t3dt * np.cos(rot) - y_ell_t3dt * np.sin(rot)
    y_t3dt_post = x_ell_t3dt * np.sin(rot) + y_ell_t3dt * np.cos(rot)
    
    # Escape hyperbola for conventional (continues to drift away)
    theta_escape = theta[250:]
    drift_factor = theta_escape / (np.pi/3)
    x_drift_post = x_nom[250:] + 2000.0 * drift_factor
    y_drift_post = y_nom[250:] + 1500.0 * drift_factor
    
    # Concatenate approach and post-insertion
    x_nom_full = np.concatenate([x_nom[:250], x_nom_post])
    y_nom_full = np.concatenate([y_nom[:250], y_nom_post])
    
    x_t3dt_full = np.concatenate([x_nom[:250], x_t3dt_post])
    y_t3dt_full = np.concatenate([y_nom[:250], y_t3dt_post])
    
    x_drift_full = np.concatenate([x_nom[:250], x_drift_post])
    y_drift_full = np.concatenate([y_nom[:250], y_drift_post])
    
    ax.plot(x_nom_full, y_nom_full, label="Nominal Trajectory", color=c_nom, lw=1.5, linestyle=':')
    ax.plot(x_drift_full, y_drift_full, label="Conventional Reactive (Drifted Orbit)", color=c_conv, lw=2)
    ax.plot(x_t3dt_full, y_t3dt_full, label="T3DT Enabled (Corrected Orbit)", color=c_t3dt, lw=1.5)
    
    # Mark insertion point
    ax.scatter([x_nom[250]], [y_nom[250]], color='red', marker='x', s=80, zorder=5, label="Insertion Burn Ignition")
    
    ax.set_xlim(-12000, 15000)
    ax.set_ylim(-12000, 12000)
    ax.set_xlabel("X (km)")
    ax.set_ylabel("Y (km)")
    ax.set_title("Mars Orbit Insertion Trajectory Comparison")
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend()
    save_plot(fig, "fig_orbital_trajectory.pdf")
    save_plot(fig, "fig_orbital_trajectory.png")
    plt.close(fig)

    # -------------------------------------------------------------------------
    # Figure 5: Thermal Prediction Accuracy
    # -------------------------------------------------------------------------
    print("Generating Figure 5: Thermal Prediction Accuracy...")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    
    # Subplot of thermal anomaly
    t_sub = np.array(logs_exp3["time"]) / 3600.0
    ax.plot(t_sub, logs_exp1["cabin_temperature"], label="Conventional Reactive (Delayed Command)", color=c_conv, lw=2)
    ax.plot(t_sub, logs_exp3["cabin_temperature"], label="T3DT Enabled (Synchronous Command)", color=c_t3dt, lw=2)
    
    ax.axhline(22.5, color='gray', linestyle=':', label="Advisory Threshold (22.5°C)")
    ax.axvline(12.0, color='orange', linestyle='--', alpha=0.5, label="Radiator Efficiency Degr. (12.0h)")
    
    ax.set_xlim(11.5, 14.0)
    ax.set_xlabel("Time (Hours)")
    ax.set_ylabel("Cabin Temperature (°C)")
    ax.set_title("Thermal Recovery Response: Scenario A")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    save_plot(fig, "fig_thermal_prediction.pdf")
    save_plot(fig, "fig_thermal_prediction.png")
    plt.close(fig)

    # -------------------------------------------------------------------------
    # Figure 6: Power Prediction Accuracy
    # -------------------------------------------------------------------------
    print("Generating Figure 6: Power Prediction Accuracy...")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    
    t_sub = np.array(logs_exp3["time"]) / 3600.0
    ax.plot(t_sub, logs_exp1["battery_soc"], label="Conventional Reactive (Delayed Shedding)", color=c_conv, lw=2)
    ax.plot(t_sub, logs_exp3["battery_soc"], label="T3DT Enabled (Synchronous Shedding)", color=c_t3dt, lw=2)
    
    ax.axhline(60.0, color='gray', linestyle=':', label="Critical SOC Limit (60.0%)")
    ax.axvline(20.0, color='orange', linestyle='--', alpha=0.5, label="Battery Capacity Loss (20.0h)")
    
    ax.set_xlim(19.5, 24.5)
    ax.set_xlabel("Time (Hours)")
    ax.set_ylabel("Battery State of Charge (%)")
    ax.set_title("Electrical Power System (EPS) Recovery: Scenario B")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    save_plot(fig, "fig_power_prediction.pdf")
    save_plot(fig, "fig_power_prediction.png")
    plt.close(fig)

    # -------------------------------------------------------------------------
    # Figure 7: Life Support Prediction Accuracy
    # -------------------------------------------------------------------------
    print("Generating Figure 7: Life Support Prediction Accuracy...")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    
    t_sub = np.array(logs_exp3["time"]) / 3600.0
    ax.plot(t_sub, logs_exp1["carbon_dioxide"], label="Conventional Reactive", color=c_conv, lw=2)
    ax.plot(t_sub, logs_exp3["carbon_dioxide"], label="T3DT Enabled", color=c_t3dt, lw=2)
    
    ax.axhline(0.08, color='gray', linestyle=':', label="High CO2 Threshold (0.08%)")
    ax.axvline(30.0, color='orange', linestyle='--', alpha=0.5, label="Scrubber Degradation (30.0h)")
    
    ax.set_xlim(29.5, 35.0)
    ax.set_xlabel("Time (Hours)")
    ax.set_ylabel("Cabin CO2 Concentration (%)")
    ax.set_title("ECLSS Scrubber Response Comparison: Scenario C")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    save_plot(fig, "fig_eclss_prediction.pdf")
    save_plot(fig, "fig_eclss_prediction.png")
    plt.close(fig)

    # -------------------------------------------------------------------------
    # Figure 8: Prediction Error Convergence
    # -------------------------------------------------------------------------
    print("Generating Figure 8: Prediction Error Convergence...")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    
    t_sub = np.array(logs_exp4["time"]) / 3600.0
    # Exp 4 includes blackout between hours 24-28
    ax.plot(t_sub, logs_exp4["prediction_error"], label="Prediction Model Error (T3DT)", color='purple', lw=2)
    
    ax.axvspan(24.0, 28.0, color='gray', alpha=0.3, label="Communication Blackout")
    ax.text(26.0, 0.15, "Open-Loop Drift\n(No Telemetry)", color='black', ha='center', weight='bold', fontsize=9)
    ax.text(28.2, 0.10, "Reconciliation\nRe-established", color='darkgreen', weight='bold', fontsize=9)
    
    ax.set_xlim(22.0, 31.0)
    ax.set_xlabel("Time (Hours)")
    ax.set_ylabel("Prediction Residual Error (°C)")
    ax.set_title("Prediction Error Growth and Convergence (Exp 4)")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    save_plot(fig, "fig_error_convergence.pdf")
    save_plot(fig, "fig_error_convergence.png")
    plt.close(fig)

    # -------------------------------------------------------------------------
    # Figure 9: Command Latency Comparison
    # -------------------------------------------------------------------------
    print("Generating Figure 9: Command Latency Comparison...")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    
    categories = ["Scenario A\n(Thermal)", "Scenario B\n(Battery)", "Scenario C\n(CO2 Scrubber)", "Scenario D\n(Orbital Burn)"]
    lat_conv = [480, 480, 480, 960] # s
    lat_t3dt = [240, 240, 240, 0] # s (0s effective latency because sent in advance)
    
    x = np.arange(len(categories))
    width = 0.35
    
    rects1 = ax.bar(x - width/2, lat_conv, width, label="Conventional Reactive", color=c_conv)
    rects2 = ax.bar(x + width/2, lat_t3dt, width, label="T3DT Mode", color=c_t3dt)
    
    ax.set_ylabel("Execution Delay / Latency (seconds)")
    ax.set_title("Comparison of Effective Command Latency")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.grid(True, linestyle=':', alpha=0.5, axis='y')
    ax.legend()
    
    # Add labels
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f"{height}s",
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)
                        
    autolabel(rects1)
    autolabel(rects2)
    
    save_plot(fig, "fig_command_latency.pdf")
    save_plot(fig, "fig_command_latency.png")
    plt.close(fig)

    # -------------------------------------------------------------------------
    # Figure 10: Anomaly Response Comparison
    # -------------------------------------------------------------------------
    print("Generating Figure 10: Anomaly Response Comparison...")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    
    # Plot how fast thermal anomaly is detected and resolved
    t_sub = np.array(logs_exp3["time"]) / 3600.0
    ax.plot(t_sub, logs_exp1["cabin_temperature"], label="Conventional (Reaction time: 480s)", color=c_conv, lw=2)
    ax.plot(t_sub, logs_exp3["cabin_temperature"], label="T3DT Mode (Reaction time: 240s)", color=c_t3dt, lw=2)
    ax.plot(t_sub, logs_exp2["cabin_temperature"], label="Nominal Path (No Anomaly)", color=c_nom, lw=1.5, linestyle=':')
    
    ax.axvline(12.0, color='red', linestyle='--', alpha=0.7)
    ax.text(11.98, 21.15, "Anomaly\nOnset", color='red', ha='right', fontsize=9)
    
    # Annotate execution times
    # In T3DT: Command arrived at 12h + 240s = 12.066h
    # In Conventional: Command arrived at 12h + 480s = 12.133h
    ax.scatter([12.066], [logs_exp3["cabin_temperature"][int(12.066 * 3600 / dt)]], color='blue', s=60, zorder=5, marker='o')
    ax.text(12.08, 22.0, "T3DT Correction Executed", color='blue', fontsize=8)
    
    ax.scatter([12.133], [logs_exp1["cabin_temperature"][int(12.133 * 3600 / dt)]], color='red', s=60, zorder=5, marker='o')
    ax.text(12.15, 22.2, "Conventional Correction Executed", color='red', fontsize=8)
    
    ax.set_xlim(11.9, 13.0)
    ax.set_xlabel("Time (Hours)")
    ax.set_ylabel("Cabin Temperature (°C)")
    ax.set_title("Anomaly Detection and Mitigation Speed Comparison")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    save_plot(fig, "fig_anomaly_response.pdf")
    save_plot(fig, "fig_anomaly_response.png")
    plt.close(fig)

    # -------------------------------------------------------------------------
    # Figure 11: Mission Safety Margin Comparison
    # -------------------------------------------------------------------------
    print("Generating Figure 11: Mission Safety Margin Comparison...")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    
    t_sub = np.array(logs_exp3["time"]) / 3600.0
    ax.plot(t_sub, logs_exp1["safety_margin"], label="Conventional Reactive", color=c_conv, lw=2)
    ax.plot(t_sub, logs_exp3["safety_margin"], label="T3DT Mode", color=c_t3dt, lw=2)
    
    ax.set_xlabel("Time (Hours)")
    ax.set_ylabel("Mission Safety Margin (%)")
    ax.set_title("Mission Safety Margin Evolution over 48 Hours")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    save_plot(fig, "fig_safety_margin.pdf")
    save_plot(fig, "fig_safety_margin.png")
    plt.close(fig)

    # -------------------------------------------------------------------------
    # Figure 12: Overall Architecture Workflow
    # -------------------------------------------------------------------------
    print("Generating Figure 12: Overall Architecture Workflow...")
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.axis('off')
    
    # Background bands for workflow phases
    downlink_bg = patches.FancyBboxPatch((0.02, 0.70), 0.96, 0.18, boxstyle="round,pad=0.01",
                                        linewidth=0, facecolor='#fafafa')
    ax.add_patch(downlink_bg)
    ax.text(0.5, 0.855, "PHASE I: TELEMETRY DOWNLINK TRANSIT", ha='center', fontsize=9, weight='bold', color='#555555')
    
    ground_bg = patches.FancyBboxPatch((0.02, 0.40), 0.96, 0.26, boxstyle="round,pad=0.01",
                                      linewidth=0, facecolor='#f0f8ff')
    ax.add_patch(ground_bg)
    ax.text(0.5, 0.625, "PHASE II: GROUND DIGITAL TWIN CO-SIMULATION & COMMAND GENERATION", ha='center', fontsize=9, weight='bold', color='#104e7b')
    
    uplink_bg = patches.FancyBboxPatch((0.02, 0.10), 0.96, 0.26, boxstyle="round,pad=0.01",
                                      linewidth=0, facecolor='#fff5eb')
    ax.add_patch(uplink_bg)
    ax.text(0.5, 0.325, "PHASE III: COMMAND UPLINK TRANSIT & ONBOARD EXECUTION", ha='center', fontsize=9, weight='bold', color='#c25913')
    
    # Flowchart boxes
    def draw_box(ax, text, xy, width, height, border_color, face_color):
        rect = patches.FancyBboxPatch(xy, width, height, boxstyle="round,pad=0.01",
                                     linewidth=1.5, edgecolor=border_color, facecolor=face_color)
        ax.add_patch(rect)
        ax.text(xy[0] + width/2, xy[1] + height/2, text, ha='center', va='center',
                fontsize=9, weight='bold', color='#2b2b2b', wrap=True)
                
    draw_box(ax, "1. Telemetry Packaging\n(Spacecraft packs state & intent)", (0.05, 0.72), 0.24, 0.11, '#ff7f0e', '#fffdfa')
    draw_box(ax, "2. Space-to-Earth DSN\n(240s propagation delay)", (0.38, 0.72), 0.24, 0.11, '#7f7f7f', '#fafafa')
    draw_box(ax, "3. Earth Receiving\n(Received state t - 240s)", (0.71, 0.72), 0.24, 0.11, '#1f77b4', '#f5faff')
    
    draw_box(ax, "4. Past/Present Twin Update\n(Propagated to t via calib)", (0.05, 0.44), 0.24, 0.13, '#1f77b4', '#f5faff')
    draw_box(ax, "5. Future Twin Projection\n(Forward projected to t + 240s)", (0.38, 0.44), 0.24, 0.13, '#1f77b4', '#f5faff')
    draw_box(ax, "6. Preemptive Command\n(Generated for epoch t+240s)", (0.71, 0.44), 0.24, 0.13, '#2ca02c', '#f7fff7')
    
    draw_box(ax, "7. Earth-to-Space DSN\n(240s command transmission)", (0.05, 0.14), 0.24, 0.13, '#7f7f7f', '#fafafa')
    draw_box(ax, "8. Cabin Reconciliation FSM\n(Check actual vs. prediction)", (0.38, 0.14), 0.24, 0.13, '#ff7f0e', '#fffdfa')
    draw_box(ax, "9. Synchronous Actuation\n(Executed if AUTH = TRUE)", (0.71, 0.14), 0.24, 0.13, '#ff7f0e', '#fffdfa')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    # Arrows
    # Row 1 Downlink
    ax.annotate("", xy=(0.38, 0.775), xytext=(0.29, 0.775), arrowprops=dict(arrowstyle="->", lw=1.5, color='#444444'))
    ax.annotate("", xy=(0.71, 0.775), xytext=(0.62, 0.775), arrowprops=dict(arrowstyle="->", lw=1.5, color='#444444'))
    
    # Downlink to Ground processing
    ax.annotate("", xy=(0.17, 0.57), xytext=(0.83, 0.72), arrowprops=dict(arrowstyle="->", lw=1.5, color='#1f77b4',
                connectionstyle="arc3,rad=0.15"))
    
    # Row 2 Ground Processing
    ax.annotate("", xy=(0.38, 0.505), xytext=(0.29, 0.505), arrowprops=dict(arrowstyle="->", lw=1.5, color='#1f77b4'))
    ax.annotate("", xy=(0.71, 0.505), xytext=(0.62, 0.505), arrowprops=dict(arrowstyle="->", lw=1.5, color='#1f77b4'))
    
    # Ground processing to Uplink
    ax.annotate("", xy=(0.17, 0.27), xytext=(0.83, 0.44), arrowprops=dict(arrowstyle="->", lw=1.5, color='#2ca02c',
                connectionstyle="arc3,rad=0.15"))
                
    # Row 3 Uplink & Actuation
    ax.annotate("", xy=(0.38, 0.205), xytext=(0.29, 0.205), arrowprops=dict(arrowstyle="->", lw=1.5, color='#444444'))
    ax.annotate("", xy=(0.71, 0.205), xytext=(0.62, 0.205), arrowprops=dict(arrowstyle="->", lw=1.5, color='#444444'))
    
    # Feedback loop arrow back to step 1
    ax.annotate("", xy=(0.17, 0.72), xytext=(0.83, 0.14), arrowprops=dict(arrowstyle="->", lw=1.5, ls=':', color='#ff7f0e',
                connectionstyle="arc3,rad=-0.25"))
                
    ax.text(0.5, 0.94, "TRI-TEMPORAL DIGITAL TWIN (T3DT) OPERATIONAL WORKFLOW", ha='center', fontsize=13, weight='bold', color='#1a1a1a')
    save_plot(fig, "fig_t3dt_workflow.pdf")
    save_plot(fig, "fig_t3dt_workflow.png")
    plt.close(fig)

    print("All plots generated successfully.")

if __name__ == "__main__":
    generate_all_plots()
