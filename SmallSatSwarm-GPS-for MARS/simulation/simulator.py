import os
import numpy as np
import parameters as p

def get_constellation_params(num_sats):
    """
    Returns the inclinations, directions, and mean anomaly offsets for a given swarm size.
    For N satellites, we use N/2 planes with 2 satellites each.
    """
    num_planes = num_sats // 2
    if num_sats == 4:
        inclinations = np.radians([30.0, 50.0])
        directions = ['asc', 'desc']
    elif num_sats == 6:
        inclinations = np.radians([30.0, 50.0, 70.0])
        directions = ['asc', 'desc', 'asc']
    elif num_sats == 8:
        inclinations = np.radians([30.0, 45.0, 60.0, 75.0])
        directions = ['asc', 'desc', 'asc', 'desc']
    else:
        # Fallback default
        inclinations = np.linspace(np.radians(30.0), np.radians(70.0), num_planes)
        directions = ['asc' if i % 2 == 0 else 'desc' for i in range(num_planes)]

    offsets = [np.radians(-2.5), np.radians(2.5)]
    sat_params = []
    
    # Calculate rover location in MCI at t_align to align the orbits
    v_E = p.v_rover_mag * np.cos(p.v_heading)
    v_N = p.v_rover_mag * np.sin(p.v_heading)
    lon_r_align = p.lon_r0 + (v_E * p.t_align) / (p.R_M * np.cos(p.lat_r0))
    lon_r_mci_align = lon_r_align + p.omega_M * p.t_align

    for inc_val, direction in zip(inclinations, directions):
        sin_u = np.sin(p.lat_r0) / np.sin(inc_val)
        u_base = np.arcsin(sin_u)
        if direction == 'desc':
            u_base = np.pi - u_base
            
        for offset in offsets:
            u = u_base + offset
            raan_val = lon_r_mci_align - np.arctan2(np.sin(u) * np.cos(inc_val), np.cos(u))
            M0 = u - p.n_o * p.t_align
            sat_params.append((inc_val, raan_val, M0))
            
    return sat_params

def run_simulation(num_sats=6, weather_mode='dual_band'):
    """
    Runs the EKF surface localization simulation.
    Returns a dictionary of trajectories, estimates, error metrics, and visibility data.
    """
    time_steps = np.arange(0, p.t_max + p.dt, p.dt)
    n_steps = len(time_steps)
    
    sat_params = get_constellation_params(num_sats)
    n_sats = len(sat_params)
    
    # 1. Rover True Trajectory
    true_rover_pos_mcmf = np.zeros((n_steps, 3))
    true_rover_vel_mcmf = np.zeros((n_steps, 3))
    true_rover_pos_mci = np.zeros((n_steps, 3))
    true_rover_clock_bias = np.zeros(n_steps)
    
    v_E = p.v_rover_mag * np.cos(p.v_heading)
    v_N = p.v_rover_mag * np.sin(p.v_heading)
    
    b_true = p.b0
    np.random.seed(42) # Seed for reproducibility of comparisons
    
    for k, t in enumerate(time_steps):
        lat_r = p.lat_r0 + (v_N * t) / p.R_M
        lon_r = p.lon_r0 + (v_E * t) / (p.R_M * np.cos(lat_r))
        
        r_r_mcmf = p.R_M * np.array([
            np.cos(lat_r) * np.cos(lon_r),
            np.cos(lat_r) * np.sin(lon_r),
            np.sin(lat_r)
        ])
        true_rover_pos_mcmf[k] = r_r_mcmf
        
        v_r_mcmf = np.array([
            -p.R_M * np.sin(lat_r) * (v_N/p.R_M) * np.cos(lon_r) - p.R_M * np.cos(lat_r) * np.sin(lon_r) * (v_E / (p.R_M*np.cos(lat_r))),
            -p.R_M * np.sin(lat_r) * (v_N/p.R_M) * np.sin(lon_r) + p.R_M * np.cos(lat_r) * np.cos(lon_r) * (v_E / (p.R_M*np.cos(lat_r))),
            p.R_M * np.cos(lat_r) * (v_N/p.R_M)
        ])
        true_rover_vel_mcmf[k] = v_r_mcmf
        
        lon_r_mci = lon_r + p.omega_M * t
        true_rover_pos_mci[k] = p.R_M * np.array([
            np.cos(lat_r) * np.cos(lon_r_mci),
            np.cos(lat_r) * np.sin(lon_r_mci),
            np.sin(lat_r)
        ])
        
        if k > 0:
            b_true += p.clock_drift_rate * p.dt + np.random.normal(0, p.sigma_clock_rw * np.sqrt(p.dt))
        true_rover_clock_bias[k] = b_true

    # 2. Satellite Orbit Propagation
    sat_pos_mcmf = np.zeros((n_steps, n_sats, 3))
    sat_pos_mci = np.zeros((n_steps, n_sats, 3))
    sat_clock_bias = np.random.normal(0, 0.3, size=n_sats)

    for k, t in enumerate(time_steps):
        theta_M = p.omega_M * t
        for s, (inc_val, raan_val, M0) in enumerate(sat_params):
            M = M0 + p.n_o * t
            x_orb = p.r_o * np.cos(M)
            y_orb = p.r_o * np.sin(M)
            
            x_mci = x_orb * np.cos(raan_val) - y_orb * np.sin(raan_val) * np.cos(inc_val)
            y_mci = x_orb * np.sin(raan_val) + y_orb * np.cos(raan_val) * np.cos(inc_val)
            z_mci = y_orb * np.sin(inc_val)
            sat_pos_mci[k, s] = [x_mci, y_mci, z_mci]
            
            sat_pos_mcmf[k, s] = [
                x_mci * np.cos(theta_M) + y_mci * np.sin(theta_M),
                -x_mci * np.sin(theta_M) + y_mci * np.cos(theta_M),
                z_mci
            ]

    # 3. Extended Kalman Filter (EKF)
    x_est = np.zeros(7)
    x_est[0:3] = true_rover_pos_mcmf[0] + p.pos_err_init
    x_est[3:6] = true_rover_vel_mcmf[0] + p.vel_err_init
    x_est[6] = true_rover_clock_bias[0] + p.clock_err_init

    P = np.diag(p.P_init_diag)
    
    est_state_history = np.zeros((n_steps, 7))
    cov_history = np.zeros((n_steps, 7))
    visible_sats_history = np.zeros(n_steps)
    gdop_history = np.zeros(n_steps)
    pdop_history = np.zeros(n_steps)

    for k, t in enumerate(time_steps):
        is_storm = (t >= p.t_storm)
        
        # Decide measurement noise std and active tracking status
        if is_storm:
            if weather_mode == 'dual_band':
                meas_noise_std = p.sigma_433 # Fallback active
                is_tracking_active = True
            else:
                meas_noise_std = None       # S-band only: loss of lock
                is_tracking_active = False
        else:
            meas_noise_std = p.sigma_24      # Clear S-band
            is_tracking_active = True
            
        # Prediction
        if k > 0:
            F = np.eye(7)
            F[0:3, 3:6] = np.eye(3) * p.dt
            x_est = F @ x_est
            
            Q = np.zeros((7, 7))
            Q_pv = np.zeros((6, 6))
            Q_pv[0:3, 0:3] = (p.dt**3 / 3.0) * np.eye(3)
            Q_pv[0:3, 3:6] = (p.dt**2 / 2.0) * np.eye(3)
            Q_pv[3:6, 0:3] = (p.dt**2 / 2.0) * np.eye(3)
            Q_pv[3:6, 3:6] = p.dt * np.eye(3)
            Q_pv *= p.sigma_a**2
            
            Q[0:6, 0:6] = Q_pv
            Q[6, 6] = (p.sigma_c**2) * p.dt
            P = F @ P @ F.T + Q

        # Visibility
        visible_indices = []
        r_rover_true = true_rover_pos_mcmf[k]
        n_r = r_rover_true / np.linalg.norm(r_rover_true)
        
        for s in range(n_sats):
            d_vec = sat_pos_mcmf[k, s] - r_rover_true
            d_norm = np.linalg.norm(d_vec)
            sin_el = np.dot(d_vec, n_r) / d_norm
            el = np.arcsin(np.clip(sin_el, -1.0, 1.0))
            if el > np.radians(10.0):
                visible_indices.append(s)
                
        n_visible = len(visible_indices)
        visible_sats_history[k] = n_visible

        # Measurement Update (Only if tracking is active and satellites are visible)
        if n_visible > 0 and is_tracking_active:
            z = np.zeros(n_visible)
            z_pred = np.zeros(n_visible)
            H = np.zeros((n_visible, 7))
            R = np.eye(n_visible) * (meas_noise_std**2)
            A_gdop = np.zeros((n_visible, 4))
            
            for idx, s in enumerate(visible_indices):
                d_true = np.linalg.norm(sat_pos_mcmf[k, s] - r_rover_true)
                noise = np.random.normal(0, meas_noise_std)
                z[idx] = d_true + true_rover_clock_bias[k] - sat_clock_bias[s] + noise
                
                d_est = np.linalg.norm(sat_pos_mcmf[k, s] - x_est[0:3])
                z_pred[idx] = d_est + x_est[6] - sat_clock_bias[s]
                
                ax = -(sat_pos_mcmf[k, s][0] - x_est[0]) / d_est
                ay = -(sat_pos_mcmf[k, s][1] - x_est[1]) / d_est
                az = -(sat_pos_mcmf[k, s][2] - x_est[2]) / d_est
                
                H[idx, 0] = ax
                H[idx, 1] = ay
                H[idx, 2] = az
                H[idx, 6] = 1.0
                
                A_gdop[idx, 0] = ax
                A_gdop[idx, 1] = ay
                A_gdop[idx, 2] = az
                A_gdop[idx, 3] = 1.0

            y = z - z_pred
            S = H @ P @ H.T + R
            K = P @ H.T @ np.linalg.inv(S)
            
            x_est = x_est + K @ y
            P = (np.eye(7) - K @ H) @ P
            
            if n_visible >= 4:
                try:
                    Q_dop = np.linalg.inv(A_gdop.T @ A_gdop)
                    gdop_history[k] = np.sqrt(np.trace(Q_dop))
                    pdop_history[k] = np.sqrt(Q_dop[0,0] + Q_dop[1,1] + Q_dop[2,2])
                except np.linalg.LinAlgError:
                    gdop_history[k] = np.nan
                    pdop_history[k] = np.nan
            else:
                gdop_history[k] = np.nan
                pdop_history[k] = np.nan
        else:
            gdop_history[k] = np.nan
            pdop_history[k] = np.nan

        est_state_history[k] = x_est
        cov_history[k] = np.sqrt(np.diag(P))

    # Error Calculations
    pos_error_3d = np.linalg.norm(true_rover_pos_mcmf - est_state_history[:, 0:3], axis=1)
    pos_uncertainty_3d = np.sqrt(cov_history[:, 0]**2 + cov_history[:, 1]**2 + cov_history[:, 2]**2)

    # Pack results
    results = {
        'time_steps': time_steps,
        'true_rover_pos_mcmf': true_rover_pos_mcmf,
        'true_rover_pos_mci': true_rover_pos_mci,
        'true_rover_clock_bias': true_rover_clock_bias,
        'est_state': est_state_history,
        'cov': cov_history,
        'visible_sats': visible_sats_history,
        'gdop': gdop_history,
        'pdop': pdop_history,
        'pos_error_3d': pos_error_3d,
        'pos_uncertainty_3d': pos_uncertainty_3d,
        'sat_pos_mci': sat_pos_mci
    }

    # Save to data directory
    os.makedirs('data', exist_ok=True)
    filename = f"data/sim_sats_{num_sats}_mode_{weather_mode}.npz"
    np.savez(filename, **results)
    print(f"Simulation saved to {filename}")
    
    return results
