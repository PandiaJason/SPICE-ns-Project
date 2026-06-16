import os
import numpy as np
import matplotlib.pyplot as plt
import simulator as sim
import parameters as p

# Ensure directories exist
os.makedirs('../paper', exist_ok=True)
os.makedirs('data', exist_ok=True)

# Configure matplotlib
plt.rcParams.update({
    'mathtext.fontset': 'stix',
    'font.family': 'STIXGeneral',
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 14,
    'legend.fontsize': 10,
    'axes.grid': True,
    'grid.linestyle': '--',
    'grid.alpha': 0.5
})

def calculate_metrics(res, weather_mode='dual_band'):
    time_steps = res['time_steps']
    pos_error_3d = res['pos_error_3d']
    visible_sats = res['visible_sats']
    gdop = res['gdop']
    
    # Active tracking windows
    clear_active_indices = np.where((time_steps < p.t_storm) & (visible_sats >= 4))[0]
    
    if weather_mode == 'dual_band':
        storm_active_indices = np.where((time_steps >= p.t_storm) & (visible_sats >= 4))[0]
        all_active_indices = np.where(visible_sats >= 4)[0]
    else:
        # S-band only loses lock during storm, so no storm active tracking
        storm_active_indices = np.array([], dtype=int)
        all_active_indices = clear_active_indices

    # 1. RMS Position Error
    rmse_clear = np.sqrt(np.mean(pos_error_3d[clear_active_indices]**2)) if len(clear_active_indices) > 0 else np.nan
    rmse_storm = np.sqrt(np.mean(pos_error_3d[storm_active_indices]**2)) if len(storm_active_indices) > 0 else np.nan
    
    # 2. Spherical Error Probable (SEP) (50% error radius during tracking)
    sep_val = np.percentile(pos_error_3d[all_active_indices], 50) if len(all_active_indices) > 0 else np.nan
    sep_95 = np.percentile(pos_error_3d[all_active_indices], 95) if len(all_active_indices) > 0 else np.nan
    
    # 3. Maximum Position Error during tracking
    max_err_active = np.max(pos_error_3d[all_active_indices]) if len(all_active_indices) > 0 else np.nan
    
    # 4. Availability (percentage of time with >= 4 visible sats and active tracking)
    # Total time of tracking / total simulation time
    availability = (len(all_active_indices) * p.dt / p.t_max) * 100.0
    
    # 5. Convergence Time (time from first visibility to position error < 10m)
    conv_time = np.nan
    if len(clear_active_indices) > 0:
        first_idx = clear_active_indices[0]
        # Look forward in time
        for idx in clear_active_indices:
            if pos_error_3d[idx] < 10.0:
                conv_time = (idx - first_idx) * p.dt
                break
                
    return {
        'rmse_clear': rmse_clear,
        'rmse_storm': rmse_storm,
        'sep': sep_val,
        'sep_95': sep_95,
        'max_err_active': max_err_active,
        'availability': availability,
        'conv_time': conv_time
    }

def main():
    configurations = [
        (4, 'dual_band'),
        (6, 'dual_band'),
        (8, 'dual_band'),
        (6, 's_band_only')
    ]
    
    all_results = {}
    metrics_summary = {}
    
    for num_sats, mode in configurations:
        cfg_name = f"Sats_{num_sats}_{mode}"
        print(f"\nRunning simulation: {cfg_name}...")
        res = sim.run_simulation(num_sats=num_sats, weather_mode=mode)
        all_results[cfg_name] = res
        metrics_summary[cfg_name] = calculate_metrics(res, weather_mode=mode)
        
    print("\n" + "="*80)
    print("                     SIMULATION PERFORMANCE COMPARISON")
    print("="*80)
    print(f"{'Configuration':<25} | {'Clear RMS (m)':<13} | {'Storm RMS (m)':<13} | {'SEP (50%) (m)':<13} | {'Availability (%)':<16} | {'Conv. Time (s)':<14}")
    print("-"*106)
    for name, m in metrics_summary.items():
        print(f"{name:<25} | {m['rmse_clear']:13.3f} | {m['rmse_storm']:13.3f} | {m['sep']:13.3f} | {m['availability']:15.2f}% | {m['conv_time']:14.1f}")
    print("="*80)

    # ----------------------------------------------------
    # GENERATE PLOT 1: 3D Constellation & Rover Path (6 Sats Dual Band)
    # ----------------------------------------------------
    res_6_db = all_results['Sats_6_dual_band']
    time_steps = res_6_db['time_steps']
    
    fig1 = plt.figure(figsize=(10, 8))
    ax3d = fig1.add_subplot(111, projection='3d')
    
    # Mars sphere
    u_grid = np.linspace(0, 2 * np.pi, 100)
    v_grid = np.linspace(0, np.pi, 100)
    x_mars = p.R_M / 1000.0 * np.outer(np.cos(u_grid), np.sin(v_grid))
    y_mars = p.R_M / 1000.0 * np.outer(np.sin(u_grid), np.sin(v_grid))
    z_mars = p.R_M / 1000.0 * np.outer(np.ones(np.size(u_grid)), np.cos(v_grid))
    ax3d.plot_surface(x_mars, y_mars, z_mars, color='#d87040', alpha=0.15, edgecolor='#a04020', linewidth=0.1)
    
    # Find alignment index (t = 12.0 hours)
    idx_align = int(p.t_align / p.dt)

    # Orbits in MCI
    colors = ['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c', '#98df8a']
    sat_pos_mci = res_6_db['sat_pos_mci']
    n_sats = sat_pos_mci.shape[1]
    for s in range(n_sats):
        # Orbit line (slightly faded)
        ax3d.plot(sat_pos_mci[:, s, 0] / 1000.0, sat_pos_mci[:, s, 1] / 1000.0, sat_pos_mci[:, s, 2] / 1000.0, 
                  color=colors[s % len(colors)], alpha=0.4, linewidth=1.0)
        # SmallSat represented as a sphere/marker (spread out visually along the orbit)
        vis_idx = (idx_align + (s - n_sats//2) * 50) % len(res_6_db['time_steps'])
        ax3d.scatter(sat_pos_mci[vis_idx, s, 0] / 1000.0, sat_pos_mci[vis_idx, s, 1] / 1000.0, sat_pos_mci[vis_idx, s, 2] / 1000.0, 
                     color=colors[s % len(colors)], marker='o', s=60, edgecolors='black', label=f'SmallSat {s+1}', zorder=5)
        
    # Mothership Orbit trace (Higher Alt circular orbit)
    r_mothership = (p.R_M + 2000000.0) / 1000.0 # 2000 km altitude in km
    inc_mothership = np.radians(25.0)
    raan_mothership = np.radians(30.0)
    theta_trace = np.linspace(0, 2*np.pi, 200)
    x_m_orb = r_mothership * np.cos(theta_trace)
    y_m_orb = r_mothership * np.sin(theta_trace)
    x_m_mci = x_m_orb * np.cos(raan_mothership) - y_m_orb * np.sin(raan_mothership) * np.cos(inc_mothership)
    y_m_mci = x_m_orb * np.sin(raan_mothership) + y_m_orb * np.cos(raan_mothership) * np.cos(inc_mothership)
    z_m_mci = y_m_orb * np.sin(inc_mothership)
    ax3d.plot(x_m_mci, y_m_mci, z_m_mci, color='purple', linestyle='--', alpha=0.4, linewidth=1.2)

    # Mothership represented as a larger sphere/marker on its orbit
    n_mothership = np.sqrt(p.mu_M / (p.R_M + 2000000.0)**3)
    theta_m_align = n_mothership * p.t_align
    x_m_align = r_mothership * np.cos(theta_m_align)
    y_m_align = r_mothership * np.sin(theta_m_align)
    x_m_mci_sat = x_m_align * np.cos(raan_mothership) - y_m_align * np.sin(raan_mothership) * np.cos(inc_mothership)
    y_m_mci_sat = x_m_align * np.sin(raan_mothership) + y_m_align * np.cos(raan_mothership) * np.cos(inc_mothership)
    z_m_mci_sat = y_m_align * np.sin(inc_mothership)
    ax3d.scatter(x_m_mci_sat, y_m_mci_sat, z_m_mci_sat, color='purple', marker='D', s=80, edgecolors='black', label='Mothership', zorder=6)

    # Rover MCI trajectory (wraps around due to Mars rotation)
    true_rover_pos_mci = res_6_db['true_rover_pos_mci']
    ax3d.plot(true_rover_pos_mci[:, 0] / 1000.0, true_rover_pos_mci[:, 1] / 1000.0, true_rover_pos_mci[:, 2] / 1000.0, 
              color='red', linewidth=1.5, label='Rover Path (MCI)', alpha=0.7)
    
    # Draw Rover position
    ax3d.scatter(true_rover_pos_mci[idx_align, 0] / 1000.0, true_rover_pos_mci[idx_align, 1] / 1000.0, true_rover_pos_mci[idx_align, 2] / 1000.0, 
                 color='red', marker='*', s=130, label='Rover (Jezero Crater)', edgecolors='black', zorder=10)

    # Add IoT Sensor Nodes on Mars surface around Rover
    np.random.seed(42) # Seed for repeatable randomized grid layout
    n_nodes = 8
    lat_offsets = np.random.uniform(-12.0, 12.0, n_nodes)
    lon_offsets = np.random.uniform(-12.0, 12.0, n_nodes)
    for i in range(n_nodes):
        lat_iot = p.lat_r0 + np.radians(lat_offsets[i])
        # Adjust longitude for rover motion and rotation at t_align
        v_E = p.v_rover_mag * np.cos(p.v_heading)
        lon_r_align = p.lon_r0 + (v_E * p.t_align) / (p.R_M * np.cos(p.lat_r0))
        lon_iot = lon_r_align + np.radians(lon_offsets[i])
        lon_iot_mci = lon_iot + p.omega_M * p.t_align
        
        pos_iot_mci = p.R_M * np.array([
            np.cos(lat_iot) * np.cos(lon_iot_mci),
            np.cos(lat_iot) * np.sin(lon_iot_mci),
            np.sin(lat_iot)
        ])
        ax3d.scatter(pos_iot_mci[0] / 1000.0, pos_iot_mci[1] / 1000.0, pos_iot_mci[2] / 1000.0, 
                     color='#2ca02c', marker='^', s=45, edgecolors='black', 
                     label='IoT Sensor Node' if i == 0 else "", zorder=9)
    
    ax3d.set_xlabel('Mars-Centered Inertial X (km)')
    ax3d.set_ylabel('Mars-Centered Inertial Y (km)')
    ax3d.set_zlabel('Mars-Centered Inertial Z (km)')
    ax3d.set_title('3D Constellation & Rover Orbit Trajectory Map (MCI)')
    
    max_range = (p.R_M + 2000000.0) / 1000.0 * 1.05
    ax3d.set_xlim(-max_range, max_range)
    ax3d.set_ylim(-max_range, max_range)
    ax3d.set_zlim(-max_range, max_range)
    ax3d.legend(loc='upper right', bbox_to_anchor=(1.15, 0.95))
    plt.tight_layout()
    fig1.savefig('../paper/orbit_3d.png', dpi=300, bbox_inches='tight')
    fig1.savefig('orbit_3d.png', dpi=300, bbox_inches='tight')
    plt.close(fig1)

    # ----------------------------------------------------
    # GENERATE PLOT 2: GDOP and Satellite Visibility (6 Sats Dual Band)
    # ----------------------------------------------------
    fig2, (ax_vis, ax_gdop) = plt.subplots(2, 1, sharex=True, figsize=(10, 6))
    
    visible_sats_6 = res_6_db['visible_sats']
    gdop_6 = res_6_db['gdop']
    pdop_6 = res_6_db['pdop']
    
    # Visibility step plot
    ax_vis.step(time_steps / 3600.0, visible_sats_6, where='mid', color='#2ca02c', linewidth=2)
    ax_vis.set_ylabel('Visible Beacons ($m$)')
    ax_vis.set_title('Satellite Swarm Visibility & GDOP over Martian Sol')
    ax_vis.set_ylim(-0.5, 6.5)
    ax_vis.set_yticks(range(7))
    ax_vis.axvline(x=p.t_storm / 3600.0, color='red', linestyle=':', label='Dust Storm Onset')
    ax_vis.legend(loc='upper right')
    
    # GDOP plot
    plot_gdop = np.copy(gdop_6)
    plot_pdop = np.copy(pdop_6)
    plot_gdop[plot_gdop > 100.0] = np.nan
    plot_pdop[plot_pdop > 100.0] = np.nan
    
    ax_gdop.plot(time_steps / 3600.0, plot_gdop, color='#1f77b4', linewidth=2, label='GDOP')
    ax_gdop.plot(time_steps / 3600.0, plot_pdop, color='#ff7f0e', linestyle='--', linewidth=1.5, label='PDOP')
    ax_gdop.set_xlabel('Elapsed Time (hours)')
    ax_gdop.set_ylabel('DOP Value')
    ax_gdop.set_ylim(0, 25)
    ax_gdop.axvline(x=p.t_storm / 3600.0, color='red', linestyle=':')
    ax_gdop.legend(loc='upper right')
    
    plt.tight_layout()
    fig2.savefig('../paper/gdop_visibility.png', dpi=300, bbox_inches='tight')
    fig2.savefig('gdop_visibility.png', dpi=300, bbox_inches='tight')
    plt.close(fig2)

    # ----------------------------------------------------
    # GENERATE PLOT 3: Positioning Error (Dual-Band Fallback vs. S-Band Loss of Lock)
    # ----------------------------------------------------
    res_6_sband = all_results['Sats_6_s_band_only']
    
    fig3, ax_err = plt.subplots(figsize=(10, 5))
    
    # Dual band error & uncertainty
    ax_err.plot(time_steps / 3600.0, res_6_db['pos_error_3d'], color='#d62728', linewidth=2, label='True 3D Error (Dual-Band Fallback)')
    ax_err.plot(time_steps / 3600.0, res_6_db['pos_uncertainty_3d'], color='#1f77b4', linestyle='--', linewidth=1.5, label='EKF $1\\sigma$ Uncertainty (Dual-Band)')
    
    # S-band only error (shows tracking loss and drift during storm)
    ax_err.plot(time_steps / 3600.0, res_6_sband['pos_error_3d'], color='black', linestyle=':', linewidth=1.5, label='True 3D Error (S-Band Only)')
    
    ax_err.axvline(x=p.t_storm / 3600.0, color='black', linestyle=':', linewidth=1.5)
    
    # Shading regions
    ax_err.axvspan(0, p.t_storm / 3600.0, alpha=0.07, color='green', label='Clear Weather (2.4 GHz)')
    ax_err.axvspan(p.t_storm / 3600.0, p.t_max / 3600.0, alpha=0.07, color='orange', label='Dust Storm (433 MHz Fallback)')
    
    ax_err.text(p.t_storm / 3600.0 - 0.5, 12.0, '2.4 GHz Band\n(Precision Tracking)', 
                ha='right', va='center', color='green', fontsize=9, fontweight='bold')
    ax_err.text(p.t_storm / 3600.0 + 0.5, 12.0, '433 MHz Fallback\n(Sandstorm Mitigation)', 
                ha='left', va='center', color='darkorange', fontsize=9, fontweight='bold')

    ax_err.set_yscale('log')
    ax_err.set_xlabel('Elapsed Time (hours)')
    ax_err.set_ylabel('3D Position Error / Uncertainty (m)')
    ax_err.set_title('Rover Positioning Accuracy: Dual-Band Fallback vs. S-Band Only')
    ax_err.set_ylim(0.5, 10000.0)
    ax_err.legend(loc='lower left')
    
    plt.tight_layout()
    fig3.savefig('../paper/positioning_error.png', dpi=300, bbox_inches='tight')
    fig3.savefig('positioning_error.png', dpi=300, bbox_inches='tight')
    plt.close(fig3)

    # ----------------------------------------------------
    # GENERATE PLOT 4: Performance Comparison across Configurations (4, 6, 8 Sats)
    # ----------------------------------------------------
    fig4, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # 1. Position RMSE Comparison
    sizes = [4, 6, 8]
    rmse_clear_vals = [metrics_summary[f'Sats_{s}_dual_band']['rmse_clear'] for s in sizes]
    rmse_storm_vals = [metrics_summary[f'Sats_{s}_dual_band']['rmse_storm'] for s in sizes]
    
    x = np.arange(len(sizes))
    width = 0.35
    
    rects1 = ax1.bar(x - width/2, rmse_clear_vals, width, label='Clear (2.4 GHz)', color='#1f77b4')
    rects2 = ax1.bar(x + width/2, rmse_storm_vals, width, label='Storm (433 MHz)', color='#ff7f0e')
    
    ax1.set_ylabel('Position RMS Error (m)')
    ax1.set_xlabel('Swarm Size (Number of SmallSats)')
    ax1.set_title('Positioning Accuracy vs Swarm Size')
    ax1.set_xticks(x)
    ax1.set_xticklabels([str(s) for s in sizes])
    ax1.legend()
    
    # Add values on top of bars
    for rect in rects1:
        height = rect.get_height()
        ax1.annotate(f'{height:.2f}m',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)
    for rect in rects2:
        height = rect.get_height()
        ax1.annotate(f'{height:.2f}m',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

    # 2. Availability Comparison
    avail_vals = [metrics_summary[f'Sats_{s}_dual_band']['availability'] for s in sizes]
    rects3 = ax2.bar(x, avail_vals, width*1.5, color='#2ca02c', alpha=0.85)
    ax2.set_ylabel('Constellation Availability (%)')
    ax2.set_xlabel('Swarm Size (Number of SmallSats)')
    ax2.set_title('Tracking Availability vs Swarm Size')
    ax2.set_xticks(x)
    ax2.set_xticklabels([str(s) for s in sizes])
    ax2.set_ylim(0, 5.0) # We have short passes, so percentage is small
    
    for rect in rects3:
        height = rect.get_height()
        ax2.annotate(f'{height:.2f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)
                    
    plt.tight_layout()
    fig4.savefig('../paper/performance_comparison.png', dpi=300, bbox_inches='tight')
    fig4.savefig('performance_comparison.png', dpi=300, bbox_inches='tight')
    plt.close(fig4)

    # Write summary metrics to simulation/data/metrics_summary.txt
    with open('data/metrics_summary.txt', 'w') as f:
        f.write("Configuration | Clear RMS (m) | Storm RMS (m) | SEP (m) | R95 (m) | Availability (%) | Conv. Time (s)\n")
        f.write("-" * 90 + "\n")
        for name, m in metrics_summary.items():
            f.write(f"{name} | {m['rmse_clear']:.3f} | {m['rmse_storm']:.3f} | {m['sep']:.3f} | {m['sep_95']:.3f} | {m['availability']:.3f} | {m['conv_time']:.1f}\n")
    print("\nMetrics summary saved to data/metrics_summary.txt")

if __name__ == '__main__':
    main()
