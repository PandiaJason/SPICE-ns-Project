"""
Configuration parameters for the ML-CGR (Machine Learning-Driven Predictive
Link-Quality Estimation for Proactive Bundle Fragmentation in Energy-Aware CGR)
simulation.

This module defines all network topology, orbital mechanics, traffic generation,
link-quality, and ML algorithm parameters used in the simulation of deep-space
DTN routing with proactive bundle fragmentation.
"""

import numpy as np
import os

# =============================================================================
# Simulation Parameters
# =============================================================================
SIM_DURATION = 86400        # 24 hours in seconds (~1 Martian sol)
TIME_STEP = 120              # Simulation time step (seconds)
RANDOM_SEED = 42
NUM_MONTE_CARLO_RUNS = 10   # Number of Monte Carlo iterations

# =============================================================================
# Node Definitions
# =============================================================================
ROVER = 0       # Mars Surface Rover
SMALLSAT = 1    # SmallSat Relay (3U CubeSat)
MRO = 2         # Mars Reconnaissance Orbiter
DSN = 3         # Deep Space Network (Earth)

NODE_NAMES = {
    ROVER: "Mars Rover",
    SMALLSAT: "SmallSat Relay",
    MRO: "MRO",
    DSN: "DSN Earth",
}

NODE_SPECS = {
    ROVER: {
        "battery_capacity_wh": 1200.0,
        "initial_soc": 0.90,
        "power_generation_w": 110.0,    # RTG (constant)
        "idle_power_w": 15.0,
        "tx_power_w": 25.0,
        "rx_power_w": 10.0,
        "buffer_capacity_mb": 4096.0,
        "is_ground": False,
    },
    SMALLSAT: {
        "battery_capacity_wh": 16.0,
        "initial_soc": 0.70,
        "power_generation_w": 8.0,      # Solar (average w/ eclipses)
        "idle_power_w": 1.8,
        "tx_power_w": 15.0,
        "rx_power_w": 5.0,
        "buffer_capacity_mb": 512.0,
        "is_ground": False,
    },
    MRO: {
        "battery_capacity_wh": 1120.0,
        "initial_soc": 0.85,
        "power_generation_w": 1000.0,
        "idle_power_w": 200.0,
        "tx_power_w": 100.0,
        "rx_power_w": 50.0,
        "buffer_capacity_mb": 8192.0,
        "is_ground": False,
    },
    DSN: {
        "battery_capacity_wh": 1e9,
        "initial_soc": 1.0,
        "power_generation_w": 1e6,
        "idle_power_w": 0.0,
        "tx_power_w": 0.0,
        "rx_power_w": 0.0,
        "buffer_capacity_mb": 1e9,
        "is_ground": True,
    },
}

# =============================================================================
# Orbital Mechanics (Synthetic SPICE Parameters)
# =============================================================================
MARS_RADIUS_KM = 3389.5
MARS_GM = 4.282837e13          # Mars gravitational parameter (m^3/s^2)
SMALLSAT_ALT_KM = 400.0
MRO_ALT_KM = 300.0

SMALLSAT_ORBIT_RADIUS_M = (MARS_RADIUS_KM + SMALLSAT_ALT_KM) * 1e3
MRO_ORBIT_RADIUS_M = (MARS_RADIUS_KM + MRO_ALT_KM) * 1e3

SMALLSAT_PERIOD_S = 2 * np.pi * np.sqrt(SMALLSAT_ORBIT_RADIUS_M**3 / MARS_GM)
MRO_PERIOD_S = 2 * np.pi * np.sqrt(MRO_ORBIT_RADIUS_M**3 / MARS_GM)

EARTH_MARS_AVG_DIST_KM = 225e6
OWLT_S = EARTH_MARS_AVG_DIST_KM / 299792.458   # One-way light time (~750 s)

# Eclipse model for SmallSat
ECLIPSE_FRACTION = 0.40

# =============================================================================
# Contact Plan Parameters
# =============================================================================
CONTACT_PARAMS = {
    (ROVER, SMALLSAT): {
        "data_rate_bps": 2e6,
        "avg_duration_s": 720,
        "std_duration_s": 120,
        "contacts_per_day": 14,
        "owlt_s": 0.0,
    },
    (ROVER, MRO): {
        "data_rate_bps": 2e6,
        "avg_duration_s": 720,
        "std_duration_s": 120,
        "contacts_per_day": 8,
        "owlt_s": 0.0,
    },
    (SMALLSAT, MRO): {
        "data_rate_bps": 1e6,
        "avg_duration_s": 300,
        "std_duration_s": 60,
        "contacts_per_day": 6,
        "owlt_s": 0.0,
    },
    (SMALLSAT, DSN): {
        "data_rate_bps": 5e5,
        "avg_duration_s": 1800,
        "std_duration_s": 300,
        "contacts_per_day": 4,
        "owlt_s": OWLT_S,
    },
    (MRO, DSN): {
        "data_rate_bps": 2e6,
        "avg_duration_s": 14400,
        "std_duration_s": 1800,
        "contacts_per_day": 3,
        "owlt_s": OWLT_S,
    },
}

# =============================================================================
# Traffic Generation
# =============================================================================
TRAFFIC_PROFILES = [
    {
        "name": "Scientific Image",
        "source": ROVER,
        "destination": DSN,
        "priority": 2,
        "size_range_mb": (15.0, 90.0),
        "interval_range_s": (2000, 4000),
    },
    {
        "name": "Critical Telemetry",
        "source": ROVER,
        "destination": DSN,
        "priority": 1,
        "size_range_mb": (1.0, 5.0),
        "interval_range_s": (1000, 2000),
    },
    {
        "name": "Housekeeping Data",
        "source": ROVER,
        "destination": DSN,
        "priority": 3,
        "size_range_mb": (0.2, 2.0),
        "interval_range_s": (500, 1000),
    },
]

# =============================================================================
# Link Quality Model Parameters
# =============================================================================
# Link Quality Index (LQI) thresholds
LQI_GOOD_THRESHOLD = 0.75       # LQI >= 0.75: high-quality link, no fragmentation
LQI_WARN_THRESHOLD = 0.45       # LQI in [0.45, 0.75): moderate quality
LQI_POOR_THRESHOLD = 0.20       # LQI < 0.45: poor quality, aggressive fragmentation

# Link-quality degradation model parameters
# Simulates realistic path loss, Doppler, and link margin variability
LINK_QUALITY_PARAMS = {
    (ROVER, SMALLSAT): {
        "base_lqi": 0.85,           # High base quality (UHF proximity)
        "eclipse_degradation": 0.30, # LQI drop during eclipse
        "doppler_variance": 0.08,    # Doppler-induced variance
        "range_rate_factor": 0.12,   # Range-rate induced LQI shift
    },
    (ROVER, MRO): {
        "base_lqi": 0.80,
        "eclipse_degradation": 0.25,
        "doppler_variance": 0.06,
        "range_rate_factor": 0.10,
    },
    (SMALLSAT, MRO): {
        "base_lqi": 0.78,
        "eclipse_degradation": 0.20,
        "doppler_variance": 0.10,
        "range_rate_factor": 0.15,
    },
    (SMALLSAT, DSN): {
        "base_lqi": 0.60,           # Lower LQI: long deep-space link
        "eclipse_degradation": 0.35,
        "doppler_variance": 0.12,
        "range_rate_factor": 0.08,
    },
    (MRO, DSN): {
        "base_lqi": 0.72,           # X-band deep-space link
        "eclipse_degradation": 0.28,
        "doppler_variance": 0.07,
        "range_rate_factor": 0.09,
    },
}

# =============================================================================
# Proactive Bundle Fragmentation Parameters
# =============================================================================
# Fragment size is selected adaptively based on predicted LQI
FRAG_SIZE_GOOD_MB = 40.0        # Fragment size for good links (MB)
FRAG_SIZE_WARN_MB = 15.0        # Fragment size for moderate links (MB)
FRAG_SIZE_POOR_MB = 4.0         # Fragment size for poor links (MB)
MIN_FRAGMENT_SIZE_MB = 0.5      # Minimum fragment size (MB)

# Fragmentation is only applied when bundle size exceeds this threshold
FRAG_TRIGGER_SIZE_MB = 5.0

# =============================================================================
# ML Model Parameters (Random Forest Link Quality Predictor)
# =============================================================================
ML_FEATURES = [
    "elevation_deg",        # Satellite elevation angle (degrees)
    "range_rate_km_s",      # Range rate (km/s)
    "soc_relay",            # Relay battery state of charge [0, 1]
    "eclipse_flag",         # Eclipse status [0/1]
    "contact_duration_s",   # Remaining contact duration (seconds)
    "time_of_day_norm",     # Normalized time in Martian sol [0, 1]
    "buffer_util_relay",    # Relay buffer utilization [0, 1]
]
ML_N_ESTIMATORS = 50        # Number of trees in Random Forest
ML_MAX_DEPTH = 8            # Maximum tree depth
ML_TRAINING_WINDOW = 200    # Number of past observations for online training
ML_RETRAIN_INTERVAL = 1800  # Retrain model every N seconds (0.5 hour)
ML_WARMUP_SAMPLES = 30      # Minimum samples before using ML predictions

# =============================================================================
# Energy-Awareness Parameters (inherited from ECGR)
# =============================================================================
ALPHA_BASE = 1.5    # Delay weight
BETA_BASE = 0.8     # Energy weight
GAMMA_BASE = 0.8    # Buffer weight

PRIORITY_WEIGHTS = {
    1: {"alpha": 2.5, "beta": 0.3, "gamma": 0.3},     # Critical
    2: {"alpha": 1.2, "beta": 1.0, "gamma": 1.0},     # Normal
    3: {"alpha": 0.5, "beta": 1.8, "gamma": 1.8},     # Low priority
}

ENERGY_CRITICAL_THRESHOLD = 0.20
ENERGY_WARNING_THRESHOLD = 0.35
BUFFER_WARNING_THRESHOLD = 0.65

# =============================================================================
# Output Paths
# =============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIGURES_DIR = os.path.join(BASE_DIR, "figures")
