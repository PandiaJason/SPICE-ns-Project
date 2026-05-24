"""
Configuration parameters for the Space-FL simulation.

Paper: "Resource-Constrained Federated Learning over Interplanetary Space Mesh Networks
        with Intermittent DTN Links"
"""
import os
import numpy as np

# ===================================================================
# Network & Orbital Simulation Parameters
# ===================================================================
NUM_SATELLITES = 5              # SmallSats (Sat A to Sat E)
MASTER_ORBITER_ID = "Master"    # Master orbiter receiving updates
TOTAL_STEPS = 120               # Total orbital simulation steps (time steps)
CONTACT_LIFETIME = 15           # Average visibility duration of a satellite to Master (in steps)
OCCLUSION_PROB = 0.6            # Probability of orbital occlusion (blocked link)

# ===================================================================
# Power & Energy Harvesting Model
# ===================================================================
BATTERY_CAPACITY_WH = 9.0       # CubeSat battery capacity in Watt-hours
INITIAL_BATTERY_PCT = 100.0     # Initial battery percentage for satellites
PRUNING_THRESHOLD_PCT = 30.0    # Battery percentage under which neural net pruning is triggered
CRITICAL_BATTERY_PCT = 10.0     # Battery percentage under which satellite goes to sleep (no training)

POWER_RECHARGE_W = 4.5         # Solar power recharge (when in sunlit side of orbit)
POWER_IDLE_W = 1.5              # Idle power consumption (basic avionics)
POWER_TRAINING_FULL_W = 8.5     # CPU power for training full neural network
POWER_TRAINING_PRUNED_W = 4.0   # CPU power for training pruned neural network (downscaled layers)
POWER_TX_W = 6.0                # Transmitting weights via DTN link

# ===================================================================
# Machine Learning Model Parameters
# ===================================================================
INPUT_DIM = 64                  # Dimensionality of synthetic Mars surface spectral features
NUM_CLASSES = 5                 # 5 surface feature classes (background, crater, dust_storm, water_ice, volcanic_vent)
HIDDEN_DIM_1 = 128              # Layer 1 hidden dimension (Full)
HIDDEN_DIM_2 = 64               # Layer 2 hidden dimension (Full)

PRUNED_HIDDEN_DIM_1 = 64        # Layer 1 hidden dimension when pruned
PRUNED_HIDDEN_DIM_2 = 32        # Layer 2 hidden dimension when pruned

BATCH_SIZE = 32
LOCAL_EPOCHS = 5
LEARNING_RATE = 0.03
FEDPROX_MU = 0.1                # FedProx proximal regularization parameter

# ===================================================================
# Asynchronous FL & DTN Parameters
# ===================================================================
STALENESS_BETA = 0.3            # Mathematical staleness decay exponent: alpha = (1 + tau)^(-beta)
DTN_MAX_DELAY = 24              # Max delay steps before a bundle is dropped due to TTL
SEED = 42

# ===================================================================
# Experiment Types
# ===================================================================
EXPERIMENTS = [
    {
        'label': 'FedAvg-Standard',
        'async_fl': False,
        'staleness_compensation': False,
        'pruning': False,
        'dtn_routing': False,
        'desc': 'Standard synchronous FedAvg (waits for all nodes, fails on intermittent links)'
    },
    {
        'label': 'FedProx-Standard',
        'async_fl': False,
        'staleness_compensation': False,
        'pruning': False,
        'dtn_routing': False,
        'desc': 'Synchronous FedProx with proximal regularization (waits for all nodes, fails on intermittent links)'
    },
    {
        'label': 'Asynchronous-FL-NoComp',
        'async_fl': True,
        'staleness_compensation': False,
        'pruning': False,
        'dtn_routing': True,
        'desc': 'Asynchronous FL without staleness compensation or local pruning'
    },
    {
        'label': 'DAFL-Proposed',
        'async_fl': True,
        'staleness_compensation': True,
        'pruning': True,
        'dtn_routing': True,
        'desc': 'Proposed DTN-Native Asynchronous Federated Learning (DAFL) with pruning & staleness compensation'
    }
]

# ===================================================================
# Paths
# ===================================================================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')
FIGURES_DIR = os.path.join(PROJECT_ROOT, 'figures')
PAPER_DIR = os.path.join(PROJECT_ROOT, 'paper')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

# Create necessary directories
for d in [RESULTS_DIR, FIGURES_DIR, PAPER_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)
