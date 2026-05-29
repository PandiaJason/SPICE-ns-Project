import os
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

# Create data directories
data_dir = "/home/jason/SPICE-ns-Project/SMOPS2026/data"
mc_data_dir = os.path.join(data_dir, "monte_carlo")
os.makedirs(mc_data_dir, exist_ok=True)

def generate_eps_telemetry(seed=None, inject_anomalies=True):
    if seed is not None:
        np.random.seed(seed)
        
    # Orbit Parameters for Mars Low Orbit (MLO)
    # Average MLO orbit duration is ~110 minutes
    orbit_duration_mins = 110
    sample_interval_secs = 30
    samples_per_orbit = (orbit_duration_mins * 60) // sample_interval_secs  # 220 samples
    num_orbits = 32  # 15 train, 2 validation, 15 test
    total_samples = samples_per_orbit * num_orbits
    time_axis = np.arange(total_samples) * sample_interval_secs / 60.0  # Time in minutes
    
    # Generate Orbit Eclipse Masks (0 = Sunlit, 1 = Eclipse in Mars shadow)
    eclipse_duration = np.random.uniform(35.0, 40.0)
    eclipse_mask = (np.floor(time_axis / orbit_duration_mins) % 2 == 0) & \
                   ((time_axis % orbit_duration_mins) >= (orbit_duration_mins - eclipse_duration))
    eclipse_mask = eclipse_mask.astype(float)
    
    # -------------------------------------------------------------------------
    # 1. ELECTRICAL POWER SYSTEM (EPS) - Martian Irradiance (~43% of Earth)
    # -------------------------------------------------------------------------
    # Battery Voltage (V) - Cold stress makes battery chemistry operate lower
    volt_nominal = np.random.uniform(7.6, 7.8)
    volt_noise = np.random.uniform(0.003, 0.006)
    battery_voltage = np.zeros(total_samples)
    current_voltage = volt_nominal
    
    # Battery Net Discharge Current (A)
    battery_current = np.zeros(total_samples)
    
    # Battery State of Charge (SoC, 0-100%)
    battery_soc = np.zeros(total_samples)
    current_soc = np.random.uniform(80.0, 90.0)
    
    # Battery Pack Temperature (°C) - Martian orbit is colder
    temp_initial = np.random.uniform(-10.0, -5.0)
    temp_sun_coeff = np.random.uniform(0.016, 0.024)
    temp_eclipse_coeff = np.random.uniform(0.008, 0.012)
    battery_temp = np.zeros(total_samples)
    current_temp = temp_initial

    # Solar Currents for 6 faces: +X, -X, +Y, -Y, +Z, -Z (A)
    # Scaling factor: Earth solar flux (~1361 W/m2) -> Mars flux (~590 W/m2)
    solar_curr_xp = np.zeros(total_samples)
    solar_curr_xm = np.zeros(total_samples)
    solar_curr_yp = np.zeros(total_samples)
    solar_curr_ym = np.zeros(total_samples)
    solar_curr_zp = np.zeros(total_samples)
    solar_curr_zm = np.zeros(total_samples)
    
    # Regulated Lines draws (A)
    bus_curr_3v3 = np.zeros(total_samples)
    bus_curr_5v = np.zeros(total_samples)
    bus_curr_12v = np.zeros(total_samples)
    
    # -------------------------------------------------------------------------
    # 2. ATTITUDE DETERMINATION AND CONTROL (ADCS) - Weak Martian Crustal Fields
    # -------------------------------------------------------------------------
    # Magnetometer readings (micro-Tesla, sweeping localized weak crustal fields)
    mag_x = np.zeros(total_samples)
    mag_y = np.zeros(total_samples)
    mag_z = np.zeros(total_samples)
    
    # Gyroscope angular rates (deg/s)
    gyro_x = np.zeros(total_samples)
    gyro_y = np.zeros(total_samples)
    gyro_z = np.zeros(total_samples)
    
    # Reaction wheel speeds (RPM)
    rw_speed_x = np.zeros(total_samples)
    rw_speed_y = np.zeros(total_samples)
    rw_speed_z = np.zeros(total_samples)
    
    # Magnetorquer Current levels (A)
    mq_curr_x = np.zeros(total_samples)
    mq_curr_y = np.zeros(total_samples)
    mq_curr_z = np.zeros(total_samples)
    
    # -------------------------------------------------------------------------
    # 3. COMMAND AND DATA HANDLING (C&DH) / THERMAL
    # -------------------------------------------------------------------------
    cdh_cpu = np.zeros(total_samples)
    cdh_ram = np.zeros(total_samples)
    cdh_temp = np.zeros(total_samples)
    
    # -------------------------------------------------------------------------
    # 4. MISSION PAYLOAD - Mars Surface Rover Receiver & HMO Relay Uplink
    # -------------------------------------------------------------------------
    payload_temp = np.zeros(total_samples)
    edac_err = np.zeros(total_samples)
    comms_packet_drop = np.zeros(total_samples)
    
    # -------------------------------------------------------------------------
    # PHYSICAL DYNAMICS LOOP (Step by step simulation of Mars Orbit)
    # -------------------------------------------------------------------------
    spin_rate = 2 * np.pi / samples_per_orbit  # Tumbling slowly
    
    for i in range(total_samples):
        t = time_axis[i]
        angle = t * spin_rate
        
        # 1. Solar Face Currents (Calibrated for Mars 0.5A peak instead of 1.3A)
        if eclipse_mask[i] == 0:
            solar_max = np.random.uniform(0.45, 0.55)
            solar_curr_xp[i] = max(0, solar_max * np.sin(angle) + np.random.normal(0, 0.008))
            solar_curr_xm[i] = max(0, solar_max * np.sin(angle + np.pi) + np.random.normal(0, 0.008))
            solar_curr_yp[i] = max(0, solar_max * np.cos(angle) + np.random.normal(0, 0.008))
            solar_curr_ym[i] = max(0, solar_max * np.cos(angle + np.pi) + np.random.normal(0, 0.008))
            solar_curr_zp[i] = max(0, 0.12 * np.abs(np.sin(angle/4)) + np.random.normal(0, 0.003))
            solar_curr_zm[i] = max(0, 0.12 * np.abs(np.cos(angle/4)) + np.random.normal(0, 0.003))
        else:
            solar_curr_xp[i] = max(0, np.random.normal(0, 0.001))
            solar_curr_xm[i] = max(0, np.random.normal(0, 0.001))
            solar_curr_yp[i] = max(0, np.random.normal(0, 0.001))
            solar_curr_ym[i] = max(0, np.random.normal(0, 0.001))
            solar_curr_zp[i] = max(0, np.random.normal(0, 0.0005))
            solar_curr_zm[i] = max(0, np.random.normal(0, 0.0005))
            
        total_solar_gen = (solar_curr_xp[i] + solar_curr_xm[i] + 
                           solar_curr_yp[i] + solar_curr_ym[i] + 
                           solar_curr_zp[i] + solar_curr_zm[i])
        
        # 2. Regulated Lines and Base Draws
        bus_curr_3v3[i] = 0.12 + np.random.normal(0, 0.005)
        
        # S-Band receiver is turned on when flying over Martian surface assets (every 110 mins for 8 mins)
        surface_rx_active = 0.65 if (t % orbit_duration_mins >= 25 and t % orbit_duration_mins < 33) else 0.0
        bus_curr_5v[i] = 0.18 + surface_rx_active + np.random.normal(0, 0.008)
        
        # X-Band relay transmitter spikes when transmitting up to HMO mothership
        hmo_relay_active = 1.45 if (t % 220 >= 200 and t % 220 < 205) else 0.0
        bus_curr_12v[i] = 0.03 + hmo_relay_active + np.random.normal(0, 0.010)
        bus_curr_12v[i] = max(0.01, bus_curr_12v[i])
        
        # primary battery bus load
        total_load = bus_curr_3v3[i] * 3.3/8.0 + bus_curr_5v[i] * 5.0/8.0 + bus_curr_12v[i] * 12.0/8.0
        battery_current[i] = total_solar_gen - total_load
        
        # 3. Battery Voltage and SoC Dynamic updates
        net_current = battery_current[i]
        if net_current > 0:  # Charging
            current_voltage += net_current * 0.003 * (8.15 - current_voltage) + np.random.normal(0, volt_noise)
            current_soc += net_current * 0.015 * (100.0 - current_soc)
        else:  # Discharging
            current_voltage += net_current * 0.010 * (current_voltage - 6.6) + np.random.normal(0, volt_noise)
            current_soc += net_current * 0.025 * current_soc
            
        current_voltage = np.clip(current_voltage, 6.5, 8.20)
        current_soc = np.clip(current_soc, 30.0, 100.0)
        
        battery_voltage[i] = current_voltage
        battery_soc[i] = current_soc
        
        # 4. Thermal Pack heating / cooling dynamics (Mars orbits are cold)
        if eclipse_mask[i] == 0:  # Warming in Sun
            target_temp = 8.0 + 3.0 * np.sin(2 * np.pi * (i % samples_per_orbit) / samples_per_orbit) + 1.2 * total_load
            current_temp += (target_temp - current_temp) * temp_sun_coeff + np.random.normal(0, 0.03)
        else:  # Cooling in eclipse
            target_temp = -15.0 + 0.8 * total_load
            current_temp += (target_temp - current_temp) * temp_eclipse_coeff + np.random.normal(0, 0.03)
        battery_temp[i] = current_temp
        
        # 5. ADCS Kinematic sensor dynamics (Mars weak local fields: -2.5 to +2.5 uT)
        mag_x[i] = 2.2 * np.sin(angle) + np.random.normal(0, 0.03)
        mag_y[i] = 1.8 * np.cos(angle) + np.random.normal(0, 0.02)
        mag_z[i] = 0.9 * np.sin(angle / 2) + np.random.normal(0, 0.01)
        
        gyro_x[i] = np.random.normal(0.01, 0.003)
        gyro_y[i] = np.random.normal(-0.005, 0.003)
        gyro_z[i] = np.random.normal(0.02, 0.005)
        
        rw_speed_x[i] = 1500.0 + 50.0 * np.sin(angle) + np.random.normal(0, 5.0)
        rw_speed_y[i] = 1200.0 + 40.0 * np.cos(angle) + np.random.normal(0, 4.0)
        rw_speed_z[i] = 1800.0 + 60.0 * np.sin(angle/2) + np.random.normal(0, 6.0)
        
        mq_curr_x[i] = 0.02 * np.sin(angle * 2) + np.random.normal(0, 0.002)
        mq_curr_y[i] = -0.01 * np.cos(angle * 2) + np.random.normal(0, 0.001)
        mq_curr_z[i] = 0.03 * np.sin(angle) + np.random.normal(0, 0.002)
        
        # 6. C&DH Health and Temperatures
        cdh_cpu[i] = 10.0 + 75.0 * (hmo_relay_active / 1.45) + np.random.uniform(0, 4.0)
        cdh_ram[i] = 28.0 + 15.0 * (hmo_relay_active / 1.45) + np.random.uniform(0, 1.0)
        cdh_temp[i] = current_temp + 5.0 + 3.0 * (cdh_cpu[i] / 100.0) + np.random.normal(0, 0.04)
        
        # 7. Payload Thermal & flags (Martian radiation sweeps cause cosmic ray SEUs)
        payload_temp[i] = current_temp + 2.0 + 20.0 * (hmo_relay_active / 1.45) + np.random.normal(0, 0.05)
        # Mars lacks magnetosphere -> background cosmic radiation drops are continuous
        in_high_rad = (t % 220 >= 120 and t % 220 < 140)
        edac_err[i] = np.random.poisson(3.8 if in_high_rad else 0.25)
        comms_packet_drop[i] = np.random.poisson(4.5 if (hmo_relay_active > 0 and np.random.rand() > 0.8) else 0.05)
        
    # Split Indices
    train_samples = samples_per_orbit * 15       # First 15 Orbits for training
    val_samples = samples_per_orbit * 2         # Next 2 Orbits for validation calibration
    
    anomaly_labels = np.zeros(total_samples)
    anomaly_onsets = {}
    
    if inject_anomalies:
        # Anomaly 1: Battery Cell Micro-Short (Orbit 10 / 1st test orbit)
        anom1_onset = train_samples + val_samples + int(0.25 * samples_per_orbit)
        anom1_duration = int(0.4 * samples_per_orbit)
        battery_voltage[anom1_onset : anom1_onset + anom1_duration] -= 1.15 + \
            0.1 * np.sin(np.linspace(0, np.pi, anom1_duration))
        battery_temp[anom1_onset : anom1_onset + anom1_duration] += \
            np.linspace(0, 12.0, anom1_duration) + np.random.normal(0, 0.2, anom1_duration)
        anomaly_labels[anom1_onset : anom1_onset + anom1_duration] = 1.0
        anomaly_onsets['volt_drop'] = anom1_onset
        
        # Anomaly 2: Reaction Wheel Lubricant Lock / Tumbling (Orbit 11 / 2nd test orbit)
        anom2_onset = train_samples + val_samples + 1 * samples_per_orbit + int(0.3 * samples_per_orbit)
        anom2_duration = int(0.45 * samples_per_orbit)
        rw_speed_x[anom2_onset : anom2_onset + anom2_duration] *= np.linspace(1, 0.01, anom2_duration)
        gyro_x[anom2_onset : anom2_onset + anom2_duration] += \
            np.linspace(0, 6.5, anom2_duration) + np.random.normal(0, 0.1, anom2_duration)
        mq_curr_x[anom2_onset : anom2_onset + anom2_duration] = 0.45
        anomaly_labels[anom2_onset : anom2_onset + anom2_duration] = 1.0
        anomaly_onsets['wheel_lock'] = anom2_onset
        
        # Anomaly 3: CPU Bit Flip / Memory Leak (Orbit 12 / 3rd test orbit)
        anom3_onset = train_samples + val_samples + 2 * samples_per_orbit + int(0.4 * samples_per_orbit)
        anom3_duration = int(0.4 * samples_per_orbit)
        cdh_cpu[anom3_onset : anom3_onset + anom3_duration] = 99.8 + np.random.uniform(0, 0.2, anom3_duration)
        cdh_ram[anom3_onset : anom3_onset + anom3_duration] = np.clip(
            28.0 + np.linspace(0, 71.0, anom3_duration) + np.random.normal(0, 0.2, anom3_duration), 0, 100.0
        )
        cdh_temp[anom3_onset : anom3_onset + anom3_duration] += \
            np.linspace(0, 15.0, anom3_duration) + np.random.normal(0, 0.3, anom3_duration)
        anomaly_labels[anom3_onset : anom3_onset + anom3_duration] = 1.0
        anomaly_onsets['cpu_leak'] = anom3_onset
        
        # Anomaly 4: X-band Transmitter Heat Pipe Coolant Leak (Orbit 13 / 4th test orbit)
        anom4_onset = train_samples + val_samples + 3 * samples_per_orbit + int(0.38 * samples_per_orbit)
        anom4_duration = int(0.4 * samples_per_orbit)
        payload_temp[anom4_onset : anom4_onset + anom4_duration] += \
            np.linspace(0, 32.0, anom4_duration) + np.random.normal(0, 0.4, anom4_duration)
        anomaly_labels[anom4_onset : anom4_onset + anom4_duration] = 1.0
        anomaly_onsets['sensor_overheat'] = anom4_onset
        
        # Anomaly 5: ADCS Magnetorquer Coil Short Circuit & Sensor Bias (Orbit 14 / 5th test orbit)
        anom5_onset = train_samples + val_samples + 4 * samples_per_orbit + int(0.25 * samples_per_orbit)
        anom5_duration = int(0.4 * samples_per_orbit)
        mq_curr_z[anom5_onset : anom5_onset + anom5_duration] = 0.85 + np.random.normal(0, 0.01, anom5_duration)
        mag_z[anom5_onset : anom5_onset + anom5_duration] += 25.0  # Local magnetic field sensor offset
        anomaly_labels[anom5_onset : anom5_onset + anom5_duration] = 1.0
        anomaly_onsets['magnetorquer_short'] = anom5_onset
        
        # Anomaly 6: Local Dust Storm S-Band Uplink Attenuation (Orbit 15 / 6th test orbit)
        anom6_onset = train_samples + val_samples + 5 * samples_per_orbit + int(0.35 * samples_per_orbit)
        anom6_duration = int(0.4 * samples_per_orbit)
        comms_packet_drop[anom6_onset : anom6_onset + anom6_duration] = np.random.poisson(15.0, anom6_duration)
        anomaly_labels[anom6_onset : anom6_onset + anom6_duration] = 1.0
        anomaly_onsets['comms_drop'] = anom6_onset
        
    features = np.column_stack((
        battery_voltage, battery_soc, battery_temp, battery_current,
        solar_curr_xp, solar_curr_xm, solar_curr_yp, solar_curr_ym, solar_curr_zp, solar_curr_zm,
        bus_curr_3v3, bus_curr_5v, bus_curr_12v,
        mag_x, mag_y, mag_z, gyro_x, gyro_y, gyro_z,
        rw_speed_x, rw_speed_y, rw_speed_z,
        mq_curr_x, mq_curr_y, mq_curr_z,
        cdh_cpu, cdh_ram, cdh_temp, payload_temp,
        edac_err, comms_packet_drop
    ))
    
    # Split into sets
    X_train = features[:train_samples]
    X_val = features[train_samples : train_samples + val_samples]
    X_test = features[train_samples + val_samples:]
    y_test = anomaly_labels[train_samples + val_samples:]
    
    offset = train_samples + val_samples
    relative_onsets = {k: v - offset for k, v in anomaly_onsets.items()}
    
    return X_train, X_val, X_test, y_test, relative_onsets

# Generate and save Monte Carlo trial datasets
num_trials = 50
print(f"--- Generating {num_trials} Mars MLO Rover-Relay Datasets (6 Subsystem Anomalies) ---")

for trial in range(1, num_trials + 1):
    run_seed = 1000 + trial
    X_train, X_val, X_test, y_test, onsets = generate_eps_telemetry(seed=run_seed, inject_anomalies=True)
    
    # Save trial data as an archive
    trial_path = os.path.join(mc_data_dir, f"trial_{trial}.npz")
    np.savez(trial_path, 
             X_train=X_train, 
             X_val=X_val, 
             X_test=X_test, 
             y_test=y_test,
             volt_drop_onset=onsets.get('volt_drop', -1),
             wheel_lock_onset=onsets.get('wheel_lock', -1),
             cpu_leak_onset=onsets.get('cpu_leak', -1),
             sensor_overheat_onset=onsets.get('sensor_overheat', -1),
             magnetorquer_short_onset=onsets.get('magnetorquer_short', -1),
             comms_drop_onset=onsets.get('comms_drop', -1))

# Generate and save a fixed representative dataset for plotting (using seed 1001)
print("--- Generating Representative Trial Dataset ---")
X_train_rep, X_val_rep, X_test_rep, y_test_rep, onsets_rep = generate_eps_telemetry(seed=1001, inject_anomalies=True)
np.savez(os.path.join(data_dir, "representative.npz"),
         X_train=X_train_rep,
         X_val=X_val_rep,
         X_test=X_test_rep,
         y_test=y_test_rep,
         volt_drop_onset=onsets_rep.get('volt_drop', -1),
         wheel_lock_onset=onsets_rep.get('wheel_lock', -1),
         cpu_leak_onset=onsets_rep.get('cpu_leak', -1),
         sensor_overheat_onset=onsets_rep.get('sensor_overheat', -1),
         magnetorquer_short_onset=onsets_rep.get('magnetorquer_short', -1),
         comms_drop_onset=onsets_rep.get('comms_drop', -1))

print("Synthetic data generation complete. All 6-anomaly datasets successfully created.")
