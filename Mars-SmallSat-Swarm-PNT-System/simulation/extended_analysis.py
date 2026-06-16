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
    lat_grid = np.linspace(18.4 - 8.0, 18.4 + 8.0, 80)
    lon_grid = np.linspace(77.5 - 8.0, 77.5 + 8.0, 80)
    
    sat_params = sim.get_constellation_params(6)
    t = p.t_align + 100.0  # Offset slightly by 100s from exact zenith alignment to avoid collinearity singularity
    theta_M = p.omega_M * t
    sat_pos_mcmf = []
    
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
            
            r_r_mcmf = p.R_M * np.array([
                np.cos(lat_r) * np.cos(lon_r),
                np.cos(lat_r) * np.sin(lon_r),
                np.sin(lat_r)
            ])
            n_r = r_r_mcmf / np.linalg.norm(r_r_mcmf)
            
            visible_indices = []
            for s in range(6):
                d_vec = sat_pos_mcmf[s] - r_r_mcmf
                d_norm = np.linalg.norm(d_vec)
                sin_el = np.dot(d_vec, n_r) / d_norm
                el = np.arcsin(np.clip(sin_el, -1.0, 1.0))
                if el > np.radians(10.0):
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
                
    np.savez('data/spatial_analysis.npz', lat_grid=lat_grid, lon_grid=lon_grid, gdop_map=gdop_map, visibility_map=visibility_map)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    X_lon, Y_lat = np.meshgrid(lon_grid, lat_grid)
    c1 = ax1.contourf(X_lon, Y_lat, visibility_map, levels=np.arange(0, 8) - 0.5, cmap='viridis', alpha=0.85)
    ax1.scatter(77.5, 18.4, color='red', marker='*', s=150, edgecolors='black', linewidth=1.2, label='Jezero Crater (Rover)')
    ax1.set_xlabel('Mars Longitude (deg East)')
    ax1.set_ylabel('Mars Latitude (deg North)')
    ax1.set_title('Swarm Visibility Footprint ($t = 12.0$ hours)')
    fig.colorbar(c1, ax=ax1, ticks=range(8), label='Visible Satellites')
    ax1.legend(loc='lower left')
    
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
    drift_rates = np.logspace(-3, 1, 9)
    peak_outage_errors = []
    post_sync_errors = []
    
    original_drift = p.clock_drift_rate
    
    for drift in drift_rates:
        print(f" Simulating drift rate: {drift:.4f} m/s...")
        p.clock_drift_rate = drift
        res = sim.run_simulation(num_sats=6, weather_mode='dual_band')
        pos_error_3d = res['pos_error_3d']
        time_steps = res['time_steps']
        
        outage_idx = np.where(time_steps < 11.9 * 3600.0)[0]
        peak_err = np.max(pos_error_3d[outage_idx])
        peak_outage_errors.append(peak_err)
        
        sync_idx = np.where((time_steps >= 12.1 * 3600.0) & (time_steps <= 13.0 * 3600.0))[0]
        post_err = np.mean(pos_error_3d[sync_idx])
        post_sync_errors.append(post_err)
        
    p.clock_drift_rate = original_drift
    np.savez('data/clock_sensitivity.npz', drift_rates=drift_rates, peak_outage_errors=peak_outage_errors, post_sync_errors=post_sync_errors)
    
    fig, ax = plt.subplots(figsize=(8, 5))
    stability = drift_rates / p.c
    
    ax.loglog(stability, peak_outage_errors, 'o-', color='#d62728', linewidth=2, label='Peak Error during Outage (23.8h)')
    ax.loglog(stability, post_sync_errors, 's--', color='#1f77b4', linewidth=1.5, label='Post-Convergence Active Error')
    ax.axhline(y=10.0, color='green', linestyle=':', label='Clear EKF Target (< 10m)')
    ax.axvspan(1e-13, 3e-11, alpha=0.1, color='green', label='Recommended (CSAC Stability)')
    ax.axvspan(3e-11, 1e-7, alpha=0.1, color='red', label='Unsuitable (High Outage Drift)')
    
    ax.set_xlabel(r'Clock Fractional Frequency Stability ($\sigma_y \approx \dot{b}/c$)')
    ax.set_ylabel('Rover 3D Position Error (meters)')
    ax.set_title('Rover Position Drift vs. Onboard Clock Stability')
    ax.set_xlim(stability[0]*0.5, stability[-1]*2.0)
    ax.set_ylim(0.1, max(peak_outage_errors)*5.0)
    ax.legend(loc='upper left')
    
    ax.text(2e-12, 5.0, 'CSAC Range', color='green', fontweight='bold', fontsize=9)
    ax.text(1e-9, 2000.0, 'Quartz/TCXO Range\n(EKF fails to converge\nduring short passes)', color='darkred', fontweight='bold', fontsize=9)
    
    plt.tight_layout()
    fig.savefig('../paper/clock_sensitivity.png', dpi=300, bbox_inches='tight')
    fig.savefig('clock_sensitivity.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Clock Sensitivity Analysis completed and plots saved.")

def run_clock_sync_simulation():
    print("Running Mothership Asymmetric Relational Sync (MARS) Dynamic Simulation...")
    np.random.seed(42)
    time_steps = np.arange(0, p.t_max + p.dt, p.dt)
    n_steps = len(time_steps)
    
    inc_s = np.radians(30.0)
    raan_s = np.radians(45.0)
    r_s_mag = p.R_M + 350000.0
    n_s = np.sqrt(p.mu_M / r_s_mag**3)
    
    inc_m = np.radians(25.0)
    raan_m = np.radians(30.0)
    r_m_mag = p.R_M + 2000000.0
    n_m = np.sqrt(p.mu_M / r_m_mag**3)
    
    pos_s = np.zeros((n_steps, 3))
    pos_m = np.zeros((n_steps, 3))
    
    for k, t in enumerate(time_steps):
        M_s = n_s * t
        x_s_orb = r_s_mag * np.cos(M_s)
        y_s_orb = r_s_mag * np.sin(M_s)
        pos_s[k] = [
            x_s_orb * np.cos(raan_s) - y_s_orb * np.sin(raan_s) * np.cos(inc_s),
            x_s_orb * np.sin(raan_s) + y_s_orb * np.cos(raan_s) * np.cos(inc_s),
            y_s_orb * np.sin(inc_s)
        ]
        
        M_m = n_m * t
        x_m_orb = r_m_mag * np.cos(M_m)
        y_m_orb = r_m_mag * np.sin(M_m)
        pos_m[k] = [
            x_m_orb * np.cos(raan_m) - y_m_orb * np.sin(raan_m) * np.cos(inc_m),
            x_m_orb * np.sin(raan_m) + y_m_orb * np.cos(raan_m) * np.cos(inc_m),
            y_m_orb * np.sin(inc_m)
        ]
        
    d = pos_m - pos_s
    d_norm_sq = np.sum(d**2, axis=1)
    t_proj = -np.sum(pos_s * d, axis=1) / d_norm_sq
    t_proj_clipped = np.clip(t_proj, 0.0, 1.0)
    closest_points = pos_s + t_proj_clipped[:, np.newaxis] * d
    closest_dist = np.linalg.norm(closest_points, axis=1)
    los_visible = (closest_dist > p.R_M)
    
    clock_bias = 100.0 / p.c
    clock_drift = p.clock_drift_rate / p.c
    
    sigma_b_s = 3e-11
    sigma_d_s = 1e-13
    sigma_meas = 0.3e-9 
    
    bias_history = np.zeros(n_steps)
    drift_history = np.zeros(n_steps)
    
    last_correction_time = -9999.0
    
    for k, t in enumerate(time_steps):
        if k > 0:
            w_b = np.random.normal(0, sigma_b_s * np.sqrt(p.dt))
            w_d = np.random.normal(0, sigma_d_s * np.sqrt(p.dt))
            clock_bias += clock_drift * p.dt + w_b
            clock_drift += w_d
            
        if los_visible[k]:
            measured_bias = clock_bias + np.random.normal(0, sigma_meas)
            delta_bias = measured_bias
            clock_bias -= delta_bias
            
            if t - last_correction_time >= 60.0:
                if last_correction_time >= 0:
                    dt_cal = t - last_correction_time
                    clock_drift -= delta_bias / dt_cal
                last_correction_time = t
                
        bias_history[k] = clock_bias
        drift_history[k] = clock_drift
        
    bias_ns = bias_history * 1e9
    np.savez('data/clock_sync_analysis.npz', time_steps=time_steps, bias_ns=bias_ns, los_visible=los_visible)
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5.5))
    
    ax1.plot(time_steps / 3600.0, bias_ns, color='#1f77b4', linewidth=1.2, label='SmallSat Clock Bias')
    vis_diff = np.diff(los_visible.astype(int))
    change_indices = np.where(vis_diff != 0)[0]
    
    start_t = 0.0
    for idx in change_indices:
        end_t = time_steps[idx+1] / 3600.0
        if los_visible[idx]:
            ax1.axvspan(start_t, end_t, alpha=0.12, color='green')
        else:
            ax1.axvspan(start_t, end_t, alpha=0.12, color='red')
        start_t = end_t
    if los_visible[-1]:
        ax1.axvspan(start_t, time_steps[-1]/3600.0, alpha=0.12, color='green')
    else:
        ax1.axvspan(start_t, time_steps[-1]/3600.0, alpha=0.12, color='red')
        
    ax1.axvspan(0, 0, alpha=0.12, color='green', label='Mothership Visible (MARS Active)')
    ax1.axvspan(0, 0, alpha=0.12, color='red', label='Mothership Blocked (CSAC Free Drift)')
    
    ax1.set_xlabel('Elapsed Time (hours)')
    ax1.set_ylabel('Clock Bias Offset (ns)')
    ax1.set_title('(a) CSAC Clock Bias Over 24-Hour Sol')
    ax1.legend(loc='upper right', fontsize=10.5)
    
    transition_idx = np.where(vis_diff == 1)[0]
    if len(transition_idx) > 0:
        t_trans = time_steps[transition_idx[0]]
        zoom_start = max(0, int((t_trans - 600) / p.dt))
        zoom_end = min(n_steps - 1, int((t_trans + 900) / p.dt))
        
        ax2.plot(time_steps[zoom_start:zoom_end] / 60.0, bias_ns[zoom_start:zoom_end], 'o-', color='#1f77b4', markersize=3, label='SmallSat Clock Bias')
        ax2.axvline(x=t_trans / 60.0, color='red', linestyle='--', label='MARS Protocol Activation')
        
        ax2.axvspan(time_steps[zoom_start]/60.0, t_trans/60.0, alpha=0.12, color='red', label='Outage (Free Drift)')
        ax2.axvspan(t_trans/60.0, time_steps[zoom_end]/60.0, alpha=0.12, color='green', label='Active Sync (MARS)')
        
        ax2.set_xlabel('Elapsed Time (minutes)')
        ax2.set_ylabel('Clock Bias Offset (ns)')
        ax2.set_title('(b) Lock Convergence Detail')
        ax2.legend(loc='upper right', fontsize=10.5)
    else:
        ax2.text(0.5, 0.5, 'No transition found', ha='center', va='center')
        
    active_bias = bias_ns[los_visible]
    steady_active = active_bias[np.abs(active_bias) < 3.0]
    
    ax3.hist(steady_active, bins=40, density=True, color='#2ca02c', alpha=0.75, edgecolor='black', linewidth=0.5)
    mu_fit, std_fit = np.mean(steady_active), np.std(steady_active)
    x_pdf = np.linspace(-3.0, 3.0, 100)
    pdf = 1.0 / (std_fit * np.sqrt(2 * np.pi)) * np.exp(-0.5 * ((x_pdf - mu_fit) / std_fit)**2)
    ax3.plot(x_pdf, pdf, 'r-', linewidth=1.5, label=fr'Gaussian Fit ($\mu={mu_fit:.3f}$ ns, $\sigma={std_fit:.3f}$ ns)')
    
    ax3.set_xlabel('Residual Sync Error (ns)')
    ax3.set_ylabel('Probability Density')
    ax3.set_title('(c) Steady-State Residual Error')
    ax3.legend(loc='upper right', fontsize=10.5)
    
    plt.tight_layout()
    fig.savefig('../paper/mars_sync_simulation.png', dpi=300, bbox_inches='tight')
    fig.savefig('mars_sync_simulation.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Mothership Asymmetric Relational Sync (MARS) Dynamic Simulation completed and plots saved as 1x3 (a), (b), and (c).")

def run_power_simulation():
    print("Running SmallSat Power Budget and Battery SoC Simulation...")
    np.random.seed(42)
    time_steps = np.arange(0, p.t_max + p.dt, p.dt)
    n_steps = len(time_steps)
    
    inc_s = np.radians(30.0)
    raan_s = np.radians(45.0)
    r_s_mag = p.R_M + 350000.0
    n_s = np.sqrt(p.mu_M / r_s_mag**3)
    
    sun_vec = np.array([1.0, 0.0, 0.0])
    
    lat_r = np.radians(18.4)
    lon_r = np.radians(77.5)
    
    pos_s = np.zeros((n_steps, 3))
    is_eclipse = np.zeros(n_steps, dtype=bool)
    is_rover_visible = np.zeros(n_steps, dtype=bool)
    
    for k, t in enumerate(time_steps):
        M_s = n_s * t
        x_s_orb = r_s_mag * np.cos(M_s)
        y_s_orb = r_s_mag * np.sin(M_s)
        pos_s[k] = [
            x_s_orb * np.cos(raan_s) - y_s_orb * np.sin(raan_s) * np.cos(inc_s),
            x_s_orb * np.sin(raan_s) + y_s_orb * np.cos(raan_s) * np.cos(inc_s),
            y_s_orb * np.sin(inc_s)
        ]
        
        s_dot_r = np.dot(pos_s[k], sun_vec)
        if s_dot_r < 0:
            perp_dist = np.linalg.norm(pos_s[k] - s_dot_r * sun_vec)
            if perp_dist < p.R_M:
                is_eclipse[k] = True
                
        theta_M = p.omega_M * t
        r_r_mcmf = p.R_M * np.array([
            np.cos(lat_r) * np.cos(lon_r),
            np.cos(lat_r) * np.sin(lon_r),
            np.sin(lat_r)
        ])
        
        pos_r_mci = np.array([
            r_r_mcmf[0] * np.cos(theta_M) - r_r_mcmf[1] * np.sin(theta_M),
            r_r_mcmf[0] * np.sin(theta_M) + r_r_mcmf[1] * np.cos(theta_M),
            r_r_mcmf[2]
        ])
        
        d_vec = pos_s[k] - pos_r_mci
        d_norm = np.linalg.norm(d_vec)
        n_r = pos_r_mci / np.linalg.norm(pos_r_mci)
        sin_el = np.dot(d_vec, n_r) / d_norm
        el = np.arcsin(np.clip(sin_el, -1.0, 1.0))
        if el > np.radians(10.0):
            is_rover_visible[k] = True
            
    P_gen_sun = 22.0
    P_bus = 5.0
    P_sdr_tx = 8.0
    P_sdr_rx = 1.5
    
    P_gen = np.where(is_eclipse, 0.0, P_gen_sun)
    P_cons = np.where(is_rover_visible, P_bus + P_sdr_tx, P_bus + P_sdr_rx)
    
    batt_capacity_wh = 80.0
    soc_history = np.zeros(n_steps)
    energy = batt_capacity_wh
    
    for k in range(n_steps):
        net_power = P_gen[k] - P_cons[k]
        energy += (net_power * p.dt) / 3600.0
        energy = np.clip(energy, 0.0, batt_capacity_wh)
        soc_history[k] = (energy / batt_capacity_wh) * 100.0
        
    np.savez('data/power_analysis.npz', time_steps=time_steps, P_gen=P_gen, P_cons=P_cons, soc=soc_history, is_eclipse=is_eclipse, is_rover_visible=is_rover_visible)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    
    ax1.plot(time_steps / 3600.0, P_gen, color='#2ca02c', linewidth=1.5, label=r'Solar Power Generation ($P_{\mathrm{gen}}$)')
    ax1.plot(time_steps / 3600.0, P_cons, color='#d62728', linewidth=1.5, label=r'Payload + Bus Consumption ($P_{\mathrm{cons}}$)')
    ax1.set_xlabel('Elapsed Time (hours)')
    ax1.set_ylabel('Power (Watts)')
    ax1.set_title('(a) SmallSat Power Generation and Consumption Profile')
    
    ec_diff = np.diff(is_eclipse.astype(int))
    ec_change = np.where(ec_diff != 0)[0]
    
    start_t = 0.0
    for idx in ec_change:
        end_t = time_steps[idx+1] / 3600.0
        if is_eclipse[idx]:
            ax1.axvspan(start_t, end_t, alpha=0.15, color='gray')
        start_t = end_t
    if is_eclipse[-1]:
        ax1.axvspan(start_t, time_steps[-1]/3600.0, alpha=0.15, color='gray')
        
    ax2.plot(time_steps / 3600.0, soc_history, color='#1f77b4', linewidth=2, label='Battery State of Charge (SoC)')
    ax2.axhline(y=60.0, color='orange', linestyle='--', label='Minimum Safe SoC Threshold (60%)')
    ax2.set_xlabel('Elapsed Time (hours)')
    ax2.set_ylabel('Battery SoC (%)')
    ax2.set_ylim(40, 105)
    ax2.set_title('(b) Onboard Battery State of Charge (SoC) over 24-Hour Sol')
    ax2.legend(loc='lower left')
    
    start_t = 0.0
    for idx in ec_change:
        end_t = time_steps[idx+1] / 3600.0
        if is_eclipse[idx]:
            ax2.axvspan(start_t, end_t, alpha=0.15, color='gray')
        start_t = end_t
    if is_eclipse[-1]:
        ax2.axvspan(start_t, time_steps[-1]/3600.0, alpha=0.15, color='gray')
        
    ax1.axvspan(0, 0, alpha=0.15, color='gray', label='Mars Eclipse (No Generation)')
    ax1.legend(loc='upper right')
    
    plt.tight_layout()
    fig.savefig('../paper/power_budget_simulation.png', dpi=300, bbox_inches='tight')
    fig.savefig('power_budget_simulation.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("SmallSat Power Budget and Battery SoC Simulation completed and plots saved as 1x2 (a) and (b).")

if __name__ == '__main__':
    run_spatial_gdop_analysis()
    run_clock_sensitivity_analysis()
    run_clock_sync_simulation()
    run_power_simulation()
