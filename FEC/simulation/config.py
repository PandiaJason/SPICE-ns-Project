"""
Configuration parameters for the Adaptive Turbo Code deep-space simulation.

Paper: "A Dynamically Punctured Variable-Memory Turbo Code Optimization
        for Non-Gaussian Radiation Noise Channels in Deep Space"
"""
import numpy as np
import os

# ===================================================================
# RSC Constituent Encoder Parameters
# ===================================================================
CONSTRAINT_LENGTH = 4          # K = 4  -> 8-state trellis
MEMORY = CONSTRAINT_LENGTH - 1 # m = 3
NUM_STATES = 1 << MEMORY       # 8
# Generator polynomials (octal): feedback = 15, feedforward = 13
# Binary: g0 = 1111 (1+D+D^2+D^3), g1 = 1101 (1+D^2+D^3)
FEEDBACK_POLY  = 0o15   # 0b1101 = 13 decimal
FEEDFORWARD_POLY = 0o13 # 0b1011 = 11 decimal

# ===================================================================
# Simulation Sweep Parameters
# ===================================================================
# Fast mode  →  small N + coarse SNR grid keeps total wall-time < 5 min.
# Publication mode: BLOCK_SIZES = [256, 1024], step = 0.5, MAX_ITERATIONS = 12
BLOCK_SIZES  = [64, 256]                       # fast: 64/256  | pub: 256/1024
SNR_DB_RANGE = np.arange(-1.0, 7.0, 2.0)      # fast: 2 dB    | pub: 0.5 dB

# ===================================================================
# Decoder Settings
# ===================================================================
# Fast mode  →  6 iterations + early DET.
# Publication mode: MAX_ITERATIONS = 12, DET_START_ITER = 3
MAX_ITERATIONS = 6       # fast: 6   | pub: 12
DET_START_ITER = 2       # Begin DET checks after this iteration (fast: 2 | pub: 3)
DET_DELTA      = 0.005   # Cross-entropy convergence threshold

# ===================================================================
# Puncturing Patterns
# ===================================================================
# Static rate-1/2: keep all systematic, alternate parity1 / parity2
# pattern[i] = (keep_par1, keep_par2) for bit position i%2
STATIC_PUNCT = {
    'name': 'rate-1/2 static',
    'rate': 0.5,
    'pattern': [(1, 0), (0, 1)],  # even idx -> par1, odd idx -> par2
}
# Adaptive low-rate fallback: rate ≈ 1/3 (keep both parities)
ADAPTIVE_LOW_RATE_PUNCT = {
    'name': 'rate-1/3 adaptive',
    'rate': 1.0 / 3.0,
    'pattern': [(1, 1), (1, 1)],
}

# ===================================================================
# Channel Models
# ===================================================================
# Middleton Class-A impulsive noise parameters
MIDDLETON_A = 0.1        # Impulsive index (lower = burstier)
MIDDLETON_GAMMA = 0.01   # Gaussian-to-impulsive power ratio
MIDDLETON_M_TRUNC = 10   # Truncation for mixture sum

# ===================================================================
# Monte-Carlo Control
# ===================================================================
# Fast mode  →  fewer frames / lower error floor target.
# Publication mode: MIN_BIT_ERRORS = 100, MAX_FRAMES = 2000, MIN_FRAMES = 30
MIN_BIT_ERRORS = 50      # fast: 50   | pub: 100
MAX_FRAMES     = 200     # fast: 200  | pub: 2000
MIN_FRAMES     = 15      # fast: 15   | pub: 30
BASE_SEED      = 42

# ===================================================================
# Experiment Matrix
# ===================================================================
# Each experiment is a dict describing one BER-curve run
EXPERIMENTS = [
    # --- AWGN baselines ---
    {'label': 'CCSDS-Static-AWGN',
     'channel': 'awgn', 'puncture': 'static',
     'det': False, 'adaptive_punct': False},
    {'label': 'DET-Static-AWGN',
     'channel': 'awgn', 'puncture': 'static',
     'det': True,  'adaptive_punct': False},

    # --- Middleton Class-A baselines ---
    {'label': 'CCSDS-Static-Middleton',
     'channel': 'middleton', 'puncture': 'static',
     'det': False, 'adaptive_punct': False},
    {'label': 'DET-Static-Middleton',
     'channel': 'middleton', 'puncture': 'static',
     'det': True,  'adaptive_punct': False},

    # --- Proposed: Adaptive puncturing + DET under Middleton ---
    {'label': 'Proposed-Adaptive-Middleton',
     'channel': 'middleton', 'puncture': 'adaptive',
     'det': True,  'adaptive_punct': True},

    # --- Proposed under AWGN (sanity) ---
    {'label': 'Proposed-Adaptive-AWGN',
     'channel': 'awgn', 'puncture': 'adaptive',
     'det': True,  'adaptive_punct': True},
]

# ===================================================================
# Paths
# ===================================================================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR  = os.path.join(PROJECT_ROOT, 'results')
FIGURES_DIR  = os.path.join(PROJECT_ROOT, 'figures')
PAPER_DIR    = os.path.join(PROJECT_ROOT, 'paper')
