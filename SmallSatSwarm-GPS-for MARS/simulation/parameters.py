import numpy as np

# Physical Constants
R_M = 3389500.0          # Radius of Mars (meters)
mu_M = 4.282837e13       # Mars gravitational parameter (m^3/s^2)
omega_M = 7.0776e-5      # Mars rotation rate (rad/s)
c = 299792458.0          # Speed of light (m/s)

# Simulation Timing
t_max = 86400.0          # 24-hour simulation (seconds)
dt = 10.0                # Time step (seconds)
t_storm = 43200.0        # Weather transition boundary (12.0 hours)

# Weather-dependent Measurement Noise (1-sigma)
sigma_24 = 2.0           # 2.4 GHz clear-weather noise (meters)
sigma_433 = 20.0         # 433 MHz dust-storm noise (meters)

# Target Ground Rover Configuration (Jezero Crater)
lat_r0 = np.radians(18.4)  # Initial latitude
lon_r0 = np.radians(77.5)  # Initial longitude
v_rover_mag = 0.1          # Rover velocity magnitude (m/s)
v_heading = np.radians(45.0) # Rover heading angle (North-East)

# Orbit Configuration
alt = 350000.0             # LMO altitude (meters)
r_o = R_M + alt            # Orbit radius (meters)
n_o = np.sqrt(mu_M / r_o**3) # Orbital mean motion (rad/s)

# Constellation Alignments (Targeting Jezero Crater at t = 12.0 hours)
t_align = 43200.0

# EKF Settings
pos_err_init = np.array([75.0, -50.0, 60.0])   # Initial position error (meters)
vel_err_init = np.array([-0.02, 0.01, 0.015])  # Initial velocity error (m/s)
clock_err_init = 100.0                         # Initial clock bias error (meters)

P_init_diag = np.array([100.0**2, 100.0**2, 100.0**2, 0.2**2, 0.2**2, 0.2**2, 200.0**2])

sigma_a = 0.001           # Kinematic process noise spectral density (m/s^1.5)
sigma_c = 0.01            # Clock process noise spectral density (m/s^0.5)

# Clock Drift parameters
b0 = 150.0                # Initial clock bias (meters)
clock_drift_rate = 0.005  # Constant clock drift rate (m/s)
sigma_clock_rw = 0.01     # Clock random walk noise spectral density (m/s^0.5)

# Parameter space to explore for sensitivity/performance analysis
swarm_size_options = [4, 6, 8]  # Different constellation sizes to compare
weather_modes = ['dual_band', 's_band_only']  # Weather mitigation fallback vs. S-band loss of lock
