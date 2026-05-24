"""
Monte-Carlo BER/BLER simulation runner.

Usage (from project root):
    python run_simulation.py

Outputs per-experiment JSON files to results/
"""
import numpy as np
import json
import os
import time

from simulation.config import (
    BLOCK_SIZES, SNR_DB_RANGE, EXPERIMENTS,
    STATIC_PUNCT, ADAPTIVE_LOW_RATE_PUNCT,
    MAX_ITERATIONS, DET_START_ITER, DET_DELTA,
    MIN_BIT_ERRORS, MAX_FRAMES, MIN_FRAMES,
    BASE_SEED, RESULTS_DIR,
)
from simulation.channel import awgn_channel, middleton_channel, estimate_channel_state
from simulation.codec import (
    make_interleaver, turbo_encode, apply_puncturing, demux_received, turbo_decode,
)


# -------------------------------------------------------------------
# Puncture-pattern selector
# -------------------------------------------------------------------
def select_pattern(adaptive_punct, channel_quality):
    """
    Return the puncturing pattern (dict) for this frame.

    If adaptive_punct is True and channel quality is poor, fall back to
    the lower-rate pattern (more parity bits sent -> stronger protection).
    """
    if adaptive_punct and channel_quality < 0.5:
        return ADAPTIVE_LOW_RATE_PUNCT
    return STATIC_PUNCT


# -------------------------------------------------------------------
# Single SNR-point simulation
# -------------------------------------------------------------------
def simulate_point(snr_db, block_size, experiment, seed):
    """
    Run frames until MIN_BIT_ERRORS are accumulated or MAX_FRAMES reached.

    Returns a dict of aggregated metrics for this SNR point.
    """
    rng = np.random.RandomState(seed)
    np.random.seed(seed)

    N = block_size
    interleaver, deinterleaver = make_interleaver(N, seed=seed)
    channel_type   = experiment['channel']
    use_det        = experiment['det']
    use_adapt_punct = experiment['adaptive_punct']

    # Accumulators
    bit_errors  = 0
    frame_errors = 0
    total_bits  = 0
    total_frames = 0
    total_iters  = 0
    iter_hist    = []          # iterations used per frame
    ce_traces    = []          # CE curves (sampled, not all frames)

    frame_id = 0
    while (bit_errors < MIN_BIT_ERRORS and frame_id < MAX_FRAMES) or frame_id < MIN_FRAMES:
        frame_id += 1

        # --- Generate random info bits ---
        data = rng.randint(0, 2, size=N).astype(np.int32)

        # --- Encode ---
        systematic, parity1, parity2 = turbo_encode(data, interleaver)

        # --- Estimate channel quality using the systematic bits as a pilot ---
        sys_symbols = 1.0 - 2.0 * systematic
        # Transmit systematic bits through a temporary channel realization with nominal rate 0.5
        if channel_type == 'awgn':
            rx_sys, sigma_temp = awgn_channel(sys_symbols, snr_db, 0.5)
        else:
            rx_sys, sigma_temp = middleton_channel(sys_symbols, snr_db, 0.5)
        
        channel_quality_pilot = estimate_channel_state(rx_sys, sigma_temp)
        pattern_dict = select_pattern(use_adapt_punct, channel_quality_pilot)
        pattern = pattern_dict['pattern']

        # --- Puncture and modulate ---
        tx_symbols, code_rate, mask1, mask2 = apply_puncturing(
            systematic, parity1, parity2, pattern)

        # --- Transmit through channel ---
        if channel_type == 'awgn':
            rx_symbols, sigma = awgn_channel(tx_symbols, snr_db, code_rate)
        else:
            rx_symbols, sigma = middleton_channel(tx_symbols, snr_db, code_rate)

        # --- Adaptive puncturing: re-estimate channel quality from received block ---
        # Obtain updated pattern for *next* frame bookkeeping (affects DET threshold)
        channel_quality = estimate_channel_state(rx_symbols[:N], sigma)

        # --- Demodulate / demux ---
        sys_llr, par1_llr, par2_llr = demux_received(rx_symbols, N, mask1, mask2, sigma)

        # --- Turbo decode ---
        # Adjust DET threshold: under impulsive noise raise delta slightly to
        # terminate *earlier* (avoid wasted iterations on unrecoverable frames)
        det_thresh = DET_DELTA
        if use_adapt_punct and channel_quality < 0.4:
            det_thresh = DET_DELTA * 3.0   # relax convergence criterion

        decoded, n_iters, ce_hist = turbo_decode(
            sys_llr, par1_llr, par2_llr,
            interleaver, deinterleaver,
            max_iters=MAX_ITERATIONS,
            det_enabled=use_det,
            det_threshold=det_thresh,
            det_start=DET_START_ITER,
        )

        # --- Metrics ---
        errs = int(np.sum(decoded != data))
        bit_errors   += errs
        frame_errors += (1 if errs > 0 else 0)
        total_bits   += N
        total_frames += 1
        total_iters  += n_iters
        iter_hist.append(n_iters)
        if frame_id <= 30:          # store CE traces for first 30 frames
            ce_traces.append(ce_hist)

    # --- Summary ---
    ber  = bit_errors  / total_bits  if total_bits  > 0 else np.nan
    bler = frame_errors / total_frames if total_frames > 0 else np.nan
    mean_iters = total_iters / total_frames if total_frames > 0 else np.nan

    return {
        'snr_db':       snr_db,
        'block_size':   block_size,
        'experiment':   experiment['label'],
        'channel':      channel_type,
        'ber':          ber,
        'bler':         bler,
        'bit_errors':   bit_errors,
        'frame_errors': frame_errors,
        'total_bits':   total_bits,
        'total_frames': total_frames,
        'mean_iters':   mean_iters,
        'iter_hist':    iter_hist,
        'ce_traces':    ce_traces,
    }


# -------------------------------------------------------------------
# Main simulation loop
# -------------------------------------------------------------------
def run_all():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    for exp in EXPERIMENTS:
        label = exp['label']
        print(f"\n{'='*60}")
        print(f"  Experiment: {label}")
        print(f"{'='*60}")

        for block_size in BLOCK_SIZES:
            all_points = []
            fname = os.path.join(RESULTS_DIR, f"{label}_N{block_size}.json")

            for idx, snr_db in enumerate(SNR_DB_RANGE):
                seed = BASE_SEED + idx * 1000 + block_size
                t0 = time.time()
                result = simulate_point(snr_db, block_size, exp, seed)
                elapsed = time.time() - t0

                ber_str  = f"{result['ber']:.2e}"  if not np.isnan(result['ber'])  else "N/A"
                bler_str = f"{result['bler']:.3f}" if not np.isnan(result['bler']) else "N/A"
                print(f"  N={block_size}  Eb/N0={snr_db:+.1f} dB  "
                      f"BER={ber_str}  BLER={bler_str}  "
                      f"avgIter={result['mean_iters']:.1f}  "
                      f"frames={result['total_frames']}  ({elapsed:.1f}s)")

                all_points.append(result)

            with open(fname, 'w') as f:
                json.dump(all_points, f, indent=2)
            print(f"  -> Saved: {fname}")

    print("\nSimulation complete.")


if __name__ == '__main__':
    run_all()
