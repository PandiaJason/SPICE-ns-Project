"""
Channel models for deep-space turbo-code simulation.

Implements:
  1. AWGN channel
  2. Middleton Class-A impulsive noise channel (cosmic radiation bursts)
  3. Channel-state estimator used by the adaptive puncturing mechanism
"""
import numpy as np
from scipy.special import factorial
from simulation.config import MIDDLETON_A, MIDDLETON_GAMMA, MIDDLETON_M_TRUNC


# ===================================================================
# AWGN Channel
# ===================================================================
def awgn_channel(tx_symbols, snr_db, code_rate):
    """
    Add AWGN noise to BPSK symbols.

    Parameters
    ----------
    tx_symbols : ndarray  – transmitted BPSK symbols (+1 / -1)
    snr_db     : float    – Eb/N0 in dB
    code_rate  : float    – overall code rate (e.g. 1/2 or 1/3)

    Returns
    -------
    rx_symbols : ndarray  – received noisy symbols
    sigma      : float    – noise standard deviation
    """
    EbN0_lin = 10.0 ** (snr_db / 10.0)
    # For BPSK: Es/N0 = Eb/N0 * code_rate, sigma^2 = 1/(2*Es/N0)
    sigma = np.sqrt(1.0 / (2.0 * code_rate * EbN0_lin))
    noise = np.random.randn(len(tx_symbols)) * sigma
    return tx_symbols + noise, sigma


# ===================================================================
# Middleton Class-A Impulsive Noise Channel
# ===================================================================
def middleton_class_a_noise(n_samples, sigma_total, A=MIDDLETON_A,
                            Gamma=MIDDLETON_GAMMA, M_trunc=MIDDLETON_M_TRUNC):
    """
    Generate Middleton Class-A impulsive noise samples.

    The noise PDF is a Poisson-weighted mixture of Gaussians:
        p(x) = sum_{m=0}^{inf} w_m * N(0, sigma_m^2)
    where
        w_m     = exp(-A) * A^m / m!
        sigma_m^2 = sigma^2 * (m/A + Gamma) / (1 + Gamma)

    Parameters
    ----------
    n_samples   : int
    sigma_total : float  – total noise std dev (matches AWGN sigma for
                           same Eb/N0 so that average power is comparable)
    A           : float  – impulsive index (small -> more impulsive)
    Gamma       : float  – Gaussian-to-impulsive power ratio
    M_trunc     : int    – truncation order for the mixture

    Returns
    -------
    noise : ndarray of shape (n_samples,)
    """
    sigma2_total = sigma_total ** 2

    # Draw mixture component for each sample
    m_vals = np.random.poisson(lam=A, size=n_samples)
    m_vals = np.clip(m_vals, 0, M_trunc)

    # Variance for each component
    sigma2_m = sigma2_total * (m_vals / A + Gamma) / (1.0 + Gamma)
    sigma_m = np.sqrt(sigma2_m)

    noise = np.random.randn(n_samples) * sigma_m
    return noise


def middleton_channel(tx_symbols, snr_db, code_rate,
                      A=MIDDLETON_A, Gamma=MIDDLETON_GAMMA):
    """
    Transmit BPSK symbols through a Middleton Class-A channel.

    Returns
    -------
    rx_symbols : ndarray
    sigma      : float   – *nominal* AWGN-equivalent sigma (used for LLR)
    """
    EbN0_lin = 10.0 ** (snr_db / 10.0)
    sigma = np.sqrt(1.0 / (2.0 * code_rate * EbN0_lin))
    noise = middleton_class_a_noise(len(tx_symbols), sigma, A, Gamma)
    return tx_symbols + noise, sigma


# ===================================================================
# Channel State Estimator (for adaptive puncturing)
# ===================================================================
def estimate_channel_state(rx_block, sigma):
    """
    Estimate the instantaneous channel quality of a received block.

    Uses the empirical kurtosis of the decision-directed noise estimate
    as a proxy for impulsiveness. Pure Gaussian noise has kurtosis ≈ 3;
    impulsive noise produces kurtosis >> 3.

    Returns
    -------
    quality : float in (0, 1]  – 1.0 = clean AWGN, lower = worse
    """
    if len(rx_block) < 4:
        return 1.0
    # Subtract hard decisions to get decision-directed noise estimate
    noise_est = rx_block - np.sign(rx_block)
    centred = noise_est - np.mean(noise_est)
    var = np.var(centred)
    if var < 1e-12:
        return 1.0
    kurtosis = np.mean(centred ** 4) / (var ** 2)
    # Map kurtosis to quality:  3 -> 1.0,  >= 20 -> ~0.0
    quality = np.clip(3.0 / kurtosis, 0.01, 1.0)
    return float(quality)
