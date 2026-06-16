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

def run_spatial_gdop_analysis():
    print("Running Spatial GDOP Footprint Analysis...")
    # Define grid around Jezero Crater (18.4 N, 77.5 E)
    lat_grid = np.linspace(18.4 - 8.0, 18.4 + 8.0, 80)
    lon_grid = np.linspace(77.5 - 8.0, 77.5 + 8.0, 80)
    
    # 6-satellite configuration params
    sat_params = sim.get_constellation_params(6)
    
    # Calculate satellite positions at t_align (12.0 hours)
    t = p.t_align
    theta_M = p.omega_M * t
    sat_pos_mcmf = []
    sat_clock_bias = np.zeros(len(sat_params)) # Assume perfect sync for geometry
    
    for s, (inc_val, raan_val, M0) in enumerate(sat_params):
        M = M0 + p.n_o * t
        x_orb = p.r_o * np.cos(M)
        y_orb = p.r_o * np.sin(M)
        
        x_mci = x_orb * np.cos(raan_val) - y_orb * np.sin(raan_val) * np.cos(inc_val)
        y_mci = x_orb * np.sin(raan_val) + y_orb * np.cos(raan_val) * np.cos(inc_val)
        z_mci = y_orb * np.sin(inc_val)
        
        pos_mcmf = np.array([
            x_mci * np.cos(theta_M) + y_mci * np.sin(theta_M),
            -x_mci * np.sin(theta_M) + y_mci * np.cos(theta_M),
            z_mci
        ])
        sat_pos_mcmf.append(pos_mcmf)
    
    gdop_map = np.zeros((len(lat_grid), len(lon_grid)))
    visibility_map = np.zeros((len(lat_grid), len(lon_grid)))
    
    for i, lat_deg in enumerate(lat_grid):
        for j, lon_deg in enumerate(lon_grid):
            lat_r = np.radians(lat_deg)
            lon_r = np.radians(lon_deg)
            
            # Rover position in MCMF
            r_r_mcmf = p.R_M * np.array([
                np.cos(lat_r) * np.cos(lon_r),
                np.cos(lat_r) * np.sin(lon_r),
                np.sin(lat_r)
            ])
            n_r = r_r_mcmf / np.linalg.norm(r_r_mcmf)
            
            # Determine visibility and geometry
            visible_indices = []
            for s in range(6):
                d_vec = sat_pos_mcmf[s] - r_r_mcmf
                d_norm = np.linalg.norm(d_vec)
                sin_el = np.dot(d_vec, n_r) / d_norm
                el = np.arcsin(np.clip(sin_el, -1.0, 1.0))
                if el > np.radians(10.0): # 10 deg elevation mask
                    visible_indices.append(s)
            
            n_visible = len(visible_indices)
            visibility_map[i, j] = n_visible
            
            if n_visible >= 4:
                A_gdop = np.zeros((n_visible, 4))
                for idx, s in enumerate(visible_indices):
                    d_est = np.linalg.norm(sat_pos_mcmf[s] - r_r_mcmf)
                    A_gdop[idx, 0] = -(sat_pos_mcmf[s][0] - r_r_mcmf[0]) / d_est
                    A_gdop[idx, 1] = -(sat_pos_mcmf[s][1] - r_r_mcmf[1]) / d_est
                    A_gdop[idx, 2] = -(sat_pos_mcmf[s][2] - r_r_mcmf[2]) / d_est
                    A_gdop[idx, 3] = 1.0
                try:
                    Q_dop = np.linalg.inv(A_gdop.T @ A_gdop)
                    gdop_val = np.sqrt(np.trace(Q_dop))
                    gdop_map[i, j] = gdop_val if gdop_val < 50.0 else np.nan
                except np.linalg.LinAlgError:
                    gdop_map[i, j] = np.nan
            else:
                gdop_map[i, j] = np.nan
                
    # Save the spatial data
    np.savez('data/spatial_analysis.npz', lat_grid=lat_grid, lon_grid=lon_grid, gdop_map=gdop_map, visibility_map=visibility_map)
    
    # Plotting
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Visibility Heatmap
    X_lon, Y_lat = np.meshgrid(lon_grid, lat_grid)
    c1 = ax1.contourf(X_lon, Y_lat, visibility_map, levels=np.arange(0, 8) - 0.5, cmap='viridis', alpha=0.85)
    ax1.scatter(77.5, 18.4, color='red', marker='*', s=150, edgecolors='black', linewidth=1.2, label='Jezero Crater (Rover)')
    ax1.set_xlabel('Mars Longitude (deg East)')
    ax1.set_ylabel('Mars Latitude (deg North)')
    ax1.set_title('Swarm Visibility Footprint ($t = 12.0$ hours)')
    fig.colorbar(c1, ax=ax1, ticks=range(8), label='Visible Satellites')
    ax1.legend(loc='lower left')
    
    # GDOP Heatmap (masked where < 4 sats visible)
    masked_gdop = np.copy(gdop_map)
    c2 = ax2.contourf(X_lon, Y_lat, masked_gdop, levels=np.linspace(2, 25, 47), cmap='plasma_r', extend='max')
    ax2.contour(X_lon, Y_lat, masked_gdop, levels=[5.0, 10.0, 15.0, 20.0], colors='white', linewidths=0.8, linestyles='--')
    ax2.scatter(77.5, 18.4, color='red', marker='*', s=150, edgecolors='black', linewidth=1.2, label='Jezero Crater (Rover)')
    ax2.set_xlabel('Mars Longitude (deg East)')
    ax2.set_ylabel('Mars Latitude (deg North)')
    ax2.set_title('Geometric Dilution of Precision (GDOP) Map')
    fig.colorbar(c2, ax=ax2, label='GDOP Value')
    ax2.legend(loc='lower left')
    
    plt.tight_layout()
    fig.savefig('../paper/gdop_heatmap.png', dpi=300, bbox_inches='tight')
    fig.savefig('gdop_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Spatial GDOP Footprint Analysis completed and plots saved.")

def run_clock_sensitivity_analysis():
    print("Running Clock Stability Sensitivity Analysis...")
    # Define range of clock drift rates to sweep (in m/s of range drift)
    # 0.001 m/s (~3e-12 s/s) is high-end CSAC
    # 0.005 m/s (~1.6e-11 s/s) is our baseline CSAC
    # 0.05 m/s (~1.6e-10 s/s) is standard TCXO
    # 0.5 m/s (~1.6e-9 s/s) is low-end TCXO/high-end Quartz
    # 5.0 m/s (~1.6e-8 s/s) is standard Quartz
    drift_rates = np.logspace(-3, 1, 9)
    peak_outage_errors = []
    post_sync_errors = []
    
    # Save original drift rate
    original_drift = p.clock_drift_rate
    
    for drift in drift_rates:
        print(f" Simulating drift rate: {drift:.4f} m/s...")
        p.clock_drift_rate = drift
        # Run 6-satellite dual-band simulation
        res = sim.run_simulation(num_sats=6, weather_mode='dual_band')
        
        # Calculate errors
        pos_error_3d = res['pos_error_3d']
        time_steps = res['time_steps']
        
        # Peak error during outage (before t = 11.9 hours)
        outage_idx = np.where(time_steps < 11.9 * 3600.0)[0]
        peak_err = np.max(pos_error_3d[outage_idx])
        peak_outage_errors.append(peak_err)
        
        # Post-sync error (after tracking starts, take average error from t = 12.1 to 13.0 hours)
        sync_idx = np.where((time_steps >= 12.1 * 3600.0) & (time_steps <= 13.0 * 3600.0))[0]
        post_err = np.mean(pos_error_3d[sync_idx])
        post_sync_errors.append(post_err)
        
    # Restore original drift rate
    p.clock_drift_rate = original_drift
    
    # Save results
    np.savez('data/clock_sensitivity.npz', drift_rates=drift_rates, peak_outage_errors=peak_outage_errors, post_sync_errors=post_sync_errors)
    
    # Plotting
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Convert drift rates to standard fractional frequency stability (y = drift_rate / c)
    stability = drift_rates / p.c
    
    ax.loglog(stability, peak_outage_errors, 'o-', color='#d62728', linewidth=2, label='Peak Error during Outage (23.8h)')
    ax.loglog(stability, post_sync_errors, 's--', color='#1f77b4', linewidth=1.5, label='Post-Convergence Active Error')
    
    # Reference thresholds
    ax.axhline(y=10.0, color='green', linestyle=':', label='Clear EKF Target (< 10m)')
    
    # Shading recommended operational region (CSAC class stability < 3e-11)
    ax.axvspan(1e-13, 3e-11, alpha=0.1, color='green', label='Recommended (CSAC Stability)')
    ax.axvspan(3e-11, 1e-7, alpha=0.1, color='red', label='Unsuitable (High Outage Drift)')
    
    ax.set_xlabel(r'Clock Fractional Frequency Stability ($\sigma_y \approx \dot{b}/c$)')
    ax.set_ylabel('Rover 3D Position Error (meters)')
    ax.set_title('Rover Position Drift vs. Onboard Clock Stability')
    ax.set_xlim(stability[0]*0.5, stability[-1]*2.0)
    ax.set_ylim(0.1, max(peak_outage_errors)*5.0)
    ax.legend(loc='upper left')
    
    # Add annotations
    ax.text(2e-12, 5.0, 'CSAC Range', color='green', fontweight='bold', fontsize=9)
    ax.text(1e-9, 2000.0, 'Quartz/TCXO Range\n(EKF fails to converge\nduring short passes)', color='darkred', fontweight='bold', fontsize=9)
    
    plt.tight_layout()
    fig.savefig('../paper/clock_sensitivity.png', dpi=300, bbox_inches='tight')
    fig.savefig('clock_sensitivity.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Clock Sensitivity Analysis completed and plots saved.")

if __name__ == '__main__':
    run_spatial_gdop_analysis()
    run_clock_sensitivity_analysis()
