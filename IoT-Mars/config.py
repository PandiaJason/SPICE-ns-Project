# config.py
"""Centralized configuration parameters for Martian LoRaWAN Simulator."""

# --- PHYSICAL CONSTANTS & LORAWAN CONFIGURATIONS ---
C = 3e8  # Speed of light (m/s)
BOLTZMANN = 1.38e-23  # Boltzmann constant (J/K)

# LoRa SF thresholds (SNR in dB required to decode)
SF_THRESHOLDS = {
    7: -7.5,
    8: -10.0,
    9: -12.5,
    10: -15.0,
    11: -17.5,
    12: -20.0
}

# --- PROPAGATION MODEL PARAMETERS ---
EARTH_FC = 868e6  # 868 MHz
EARTH_TEMP = 290  # 17 °C (constant Earth standard)
EARTH_PATH_LOSS_EXP = 3.0  # Suburban path loss exponent
EARTH_SHADOWING_STD = 6.0  # Log-normal shadowing std in dB
EARTH_NOISE_FIGURE = 6.0  # Receiver noise figure in dB

MARS_FC = 868e6  # 868 MHz
MARS_PATH_LOSS_EXP = 3.5  # High path loss exponent due to poor surface reflections & NLOS
MARS_SHADOWING_STD = 8.0  # Increased shadowing due to dust and complex topography
MARS_NOISE_FIGURE = 7.0  # Harsh hardware environment

DUST_STORM_ATTENUATION = 0.15  # dB/km extra path loss
DUST_STORM_ANTENNA_LOSS = 4.0  # dB loss at both node & gateway due to dust layer coating

# --- GEOMETRY & CONSTELLATION ---
ORBIT_ALT_KM = 300
SAT_ANTENNA_GAIN = 6.0
SAT_NOISE_FIGURE = 4.0
GW_ANTENNA_GAIN_SURFACE = 2.15

# --- PROPOSED MARTIAN-OPTIMIZED MODEL PARAMETERS (433 MHz) ---
PROPOSED_FC = 433e6  # 433 MHz (UHF band)
PROPOSED_PATH_LOSS_EXP = 3.2  # Reduced diffraction losses
PROPOSED_DUST_ATTENUATION = 0.0375  # Rayleigh frequency-squared reduction
PROPOSED_NOISE_FIGURE = 3.5  # Space-grade low-noise amplifiers (LNAs)
PROPOSED_DUST_ANTENNA_LOSS = 0.5   # Residual mismatch of RF-transparent protective coating (low-loss tangent <0.01)
PROPOSED_SAT_ANTENNA_GAIN = 8.0  # Advanced satellite array gain
PROPOSED_THRESHOLD_BOOST = 3.0  # Demodulation boost from optimized channel coding

# --- SYSTEM & TRAFFIC PARAMETERS ---
AVG_TX_INTERVAL = 300.0  # seconds
PAYLOAD_BYTES = 20
DEFAULT_TX_POWER = 14.0  # dBm
DEFAULT_NODE_ANTENNA_GAIN = 0.0  # dBi
DEFAULT_BW = 125e3  # 125 kHz
