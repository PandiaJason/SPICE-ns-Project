"""
Turbo codec: RSC encoder, interleaver, BCJR (Max-Log-MAP) decoder,
and iterative turbo decoder with optional Dynamic Early Termination.
"""
import numpy as np
from simulation.config import (
    CONSTRAINT_LENGTH, MEMORY, NUM_STATES,
    FEEDBACK_POLY, FEEDFORWARD_POLY,
    MAX_ITERATIONS, DET_START_ITER, DET_DELTA,
)


# ===================================================================
# Trellis Construction
# ===================================================================
def build_trellis():
    """
    Build look-up tables for the 8-state RSC constituent encoder.

    Returns
    -------
    next_state : ndarray (NUM_STATES, 2)  – next_state[s, u]
    parity_out : ndarray (NUM_STATES, 2)  – parity bit for (s, u)
    """
    ns = np.zeros((NUM_STATES, 2), dtype=np.int32)
    po = np.zeros((NUM_STATES, 2), dtype=np.int32)

    for state in range(NUM_STATES):
        for u in range(2):
            # Extract register bits  (bit 0 = most recent)
            reg = [(state >> i) & 1 for i in range(MEMORY)]

            # Feedback: XOR of input with tapped register bits
            fb = u
            for i in range(MEMORY):
                if (FEEDBACK_POLY >> (i + 1)) & 1:
                    fb ^= reg[i]

            # Parity output via feedforward polynomial
            par = fb
            for i in range(MEMORY):
                if (FEEDFORWARD_POLY >> (i + 1)) & 1:
                    par ^= reg[i]

            # Shift register
            new_state = (fb << (MEMORY - 1)) | (state >> 1)
            ns[state, u] = new_state
            po[state, u] = par

    return ns, po


# Pre-build once at import time
_NEXT_STATE, _PARITY_OUT = build_trellis()


# ===================================================================
# Interleaver
# ===================================================================
def make_interleaver(N, seed=0):
    """Return a random permutation interleaver and its inverse."""
    rng = np.random.RandomState(seed)
    perm = rng.permutation(N)
    deperm = np.argsort(perm)
    return perm, deperm


# ===================================================================
# RSC Encoder
# ===================================================================
def rsc_encode(bits):
    """Encode a block with the RSC constituent encoder (start in state 0)."""
    N = len(bits)
    parity = np.zeros(N, dtype=np.int32)
    state = 0
    for k in range(N):
        u = int(bits[k])
        parity[k] = _PARITY_OUT[state, u]
        state = _NEXT_STATE[state, u]
    return parity


# ===================================================================
# Turbo Encoder
# ===================================================================
def turbo_encode(data, interleaver):
    """
    Rate-1/3 turbo encoder.

    Returns
    -------
    systematic, parity1, parity2 : ndarray of int (0/1)
    """
    parity1 = rsc_encode(data)
    parity2 = rsc_encode(data[interleaver])
    return data.copy(), parity1, parity2


# ===================================================================
# Puncturing Helpers
# ===================================================================
def apply_puncturing(systematic, parity1, parity2, pattern):
    """
    Puncture parity bits according to *pattern*.

    pattern : list of (keep_p1, keep_p2) tuples, cycled over bit index.

    Returns
    -------
    tx_bits : 1-D array of BPSK symbols (+1/-1)
    code_rate : effective code rate
    punct_mask1, punct_mask2 : bool arrays (True = transmitted)
    """
    N = len(systematic)
    mask1 = np.zeros(N, dtype=bool)
    mask2 = np.zeros(N, dtype=bool)
    period = len(pattern)
    for k in range(N):
        kp1, kp2 = pattern[k % period]
        mask1[k] = bool(kp1)
        mask2[k] = bool(kp2)

    # BPSK modulation: 0 -> +1, 1 -> -1
    bpsk = lambda arr: 1.0 - 2.0 * arr.astype(np.float64)

    tx_list = [bpsk(systematic)]
    if np.any(mask1):
        tx_list.append(bpsk(parity1[mask1]))
    if np.any(mask2):
        tx_list.append(bpsk(parity2[mask2]))

    tx_symbols = np.concatenate(tx_list)
    n_transmitted = N + int(mask1.sum()) + int(mask2.sum())
    code_rate = N / n_transmitted
    return tx_symbols, code_rate, mask1, mask2


def demux_received(rx, N, mask1, mask2, sigma):
    """
    Split received samples back into systematic / parity LLR arrays.
    Punctured positions get LLR = 0 (no information).
    """
    Lc = 2.0 / (sigma ** 2)  # channel reliability

    sys_rx = rx[:N]
    sys_llr = Lc * sys_rx

    par1_llr = np.zeros(N)
    par2_llr = np.zeros(N)

    offset = N
    n1 = int(mask1.sum())
    if n1 > 0:
        par1_llr[mask1] = Lc * rx[offset:offset + n1]
        offset += n1
    n2 = int(mask2.sum())
    if n2 > 0:
        par2_llr[mask2] = Lc * rx[offset:offset + n2]

    return sys_llr, par1_llr, par2_llr


# ===================================================================
# BCJR  (Max-Log-MAP) Decoder
# ===================================================================
# ── Precomputed trellis arrays for vectorised BCJR ────────────────────────────
# Shape (NUM_STATES, 2) – index [s, u] gives next state / parity-bit-BPSK-value
_NS  = _NEXT_STATE.astype(np.int32)
_PBP = (1.0 - 2.0 * _PARITY_OUT).astype(np.float64)   # parity BPSK: +1/-1
_UBP = np.array([1.0, -1.0], dtype=np.float64)          # input  BPSK: u=0→+1


def _bcjr_decode(sys_llr, par_llr, apriori):
    """
    Vectorised Max-Log-MAP BCJR on a single RSC trellis.

    All state×input operations are numpy array ops; only the time-step
    loop remains in Python, giving ~20-50× speedup over the naive version.

    Returns extrinsic LLRs (ndarray, length N).
    """
    N = len(sys_llr)
    S = NUM_STATES
    NEG_INF = -1e30

    # ── Precompute per-time-step scalars ──────────────────────────────
    sys_part = 0.5 * (sys_llr + apriori)   # (N,)  — half-channel-reliability
    par_part = 0.5 * par_llr               # (N,)

    # gamma[k, s, u] = sys_part[k]*UBP[u] + par_part[k]*PBP[s,u]
    # Compute lazily inside the loops to avoid allocating (N,S,2) upfront.

    # ── Forward metrics α ─────────────────────────────────────────────
    alpha = np.full((N + 1, S), NEG_INF)
    alpha[0, 0] = 0.0

    for k in range(N):
        # gamma_k shape (S, 2): branch metrics for all (s, u) at step k
        gamma_k = sys_part[k] * _UBP + par_part[k] * _PBP   # broadcast → (S,2)
        candidates = alpha[k, :, np.newaxis] + gamma_k        # (S, 2)

        alpha_new = np.full(S, NEG_INF)
        np.maximum.at(alpha_new, _NS[:, 0], candidates[:, 0])
        np.maximum.at(alpha_new, _NS[:, 1], candidates[:, 1])
        alpha[k + 1] = alpha_new

    # ── Backward metrics β ────────────────────────────────────────────
    beta = np.full((N + 1, S), NEG_INF)
    beta[N, :] = 0.0   # no tail bits → free boundary

    for k in range(N - 1, -1, -1):
        gamma_k  = sys_part[k] * _UBP + par_part[k] * _PBP   # (S, 2)
        # beta[k+1] at the destination states for each (s,u): shape (S, 2)
        beta_dst = beta[k + 1][_NS]                            # (S, 2)
        beta[k]  = (gamma_k + beta_dst).max(axis=1)            # (S,)

    # ── Extrinsic LLR ─────────────────────────────────────────────────
    # joint[k, s, u] = alpha[k,s] + gamma[k,s,u] + beta[k+1, NS[s,u]]
    sys_p2 = sys_part[:, np.newaxis, np.newaxis]   # (N,1,1)
    par_p2 = par_part[:, np.newaxis, np.newaxis]   # (N,1,1)

    # gamma_all shape (N, S, 2)
    gamma_all = sys_p2 * _UBP + par_p2 * _PBP     # broadcast (N,S,2)

    alpha_k   = alpha[:-1, :, np.newaxis]          # (N, S, 1)
    beta_next = beta[1:][:, _NS]                   # (N, S, 2)

    joint = alpha_k + gamma_all + beta_next         # (N, S, 2)

    max_u0 = joint[:, :, 0].max(axis=1)            # (N,)  u=0
    max_u1 = joint[:, :, 1].max(axis=1)            # (N,)  u=1

    ext = (max_u0 - max_u1) - sys_llr - apriori
    return ext


# ===================================================================
# Iterative Turbo Decoder
# ===================================================================
def turbo_decode(sys_llr, par1_llr, par2_llr,
                 interleaver, deinterleaver,
                 max_iters=MAX_ITERATIONS,
                 det_enabled=False,
                 det_threshold=DET_DELTA,
                 det_start=DET_START_ITER):
    """
    Iterative turbo decoder with optional Dynamic Early Termination.

    Returns
    -------
    decoded   : ndarray of int (0/1)
    n_iters   : int – actual iterations executed
    ce_hist   : list of cross-entropy values per iteration
    """
    N = len(sys_llr)
    apriori1 = np.zeros(N)
    ce_hist = []
    prev_ce = 1e30
    total_llr = np.zeros(N)

    for it in range(max_iters):
        # Decoder 1 (original order)
        ext1 = _bcjr_decode(sys_llr, par1_llr, apriori1)
        apriori2 = ext1[interleaver]

        # Decoder 2 (interleaved order)
        ext2 = _bcjr_decode(sys_llr[interleaver], par2_llr, apriori2)
        apriori1 = ext2[deinterleaver]

        # Combined LLR
        total_llr = sys_llr + ext1 + apriori1

        # Cross-entropy for DET
        mag = np.clip(np.abs(total_llr), 0, 50)
        prob = 1.0 / (1.0 + np.exp(-mag))
        ce = -np.mean(np.log(prob + 1e-15))
        ce_hist.append(ce)

        if det_enabled and it >= det_start:
            if abs(prev_ce - ce) < det_threshold:
                break
        prev_ce = ce

    decoded = (total_llr < 0).astype(np.int32)
    return decoded, it + 1, ce_hist
