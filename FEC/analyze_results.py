#!/usr/bin/env python3
"""
analyze_results.py  –  Load simulation JSON files, generate publication-quality
                        figures, and print a LaTeX results table.

Usage (from project root, after running run_simulation.py):
    python analyze_results.py

Outputs
-------
figures/fig1_ber_awgn.pdf          – BER vs Eb/N0 under AWGN
figures/fig2_ber_middleton.pdf     – BER vs Eb/N0 under Middleton Class-A
figures/fig3_bler_comparison.pdf   – BLER comparison
figures/fig4_iter_savings.pdf      – Avg iterations (DET power savings)
figures/fig5_ce_traces.pdf         – CE convergence curves
figures/fig6_error_floor_zoom.pdf  – Zoomed view of error floor region
"""
import json
import os
import glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from itertools import cycle

# ─────────────────────────────────────────────
# Config — single source of truth for ALL analysis parameters
# ─────────────────────────────────────────────
from simulation.config import (
    BLOCK_SIZES, MAX_ITERATIONS,
    SNR_DB_RANGE,
    DET_START_ITER, DET_DELTA,
    MIDDLETON_A, MIDDLETON_GAMMA,
    RESULTS_DIR, FIGURES_DIR,
)
os.makedirs(FIGURES_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# Derived aliases — no magic numbers anywhere else in this file
# ─────────────────────────────────────────────
_N_PANELS = BLOCK_SIZES[:2]   # dual-panel figures (figs 1 & 2)
_N_LARGE  = BLOCK_SIZES[-1]   # single-panel figures (figs 3–6) and table

# SNR landmarks derived from the sweep range
_SNR_MIN     = float(SNR_DB_RANGE[0])
_SNR_MAX     = float(SNR_DB_RANGE[-1])
_SNR_MID     = float(SNR_DB_RANGE[len(SNR_DB_RANGE) // 2])

# Table: closest available SNR point to 4 dB (or mid-point if range is small)
_TARGET_SNR  = float(SNR_DB_RANGE[np.argmin(np.abs(SNR_DB_RANGE - 4.0))])

# CE-trace figure: low / mid / high representative SNR points
_CE_SNRS = [
    float(SNR_DB_RANGE[max(0, len(SNR_DB_RANGE) // 4)]),
    float(SNR_DB_RANGE[len(SNR_DB_RANGE) // 2]),
    float(SNR_DB_RANGE[min(len(SNR_DB_RANGE) - 1, 3 * len(SNR_DB_RANGE) // 4)]),
]

# Error-floor zoom: show only the upper half of the SNR range
_FLOOR_SNR_CUTOFF = _SNR_MID

# Middleton channel description string (for titles/labels)
_MID_LABEL = f'Middleton $A={MIDDLETON_A}$, $\\Gamma={MIDDLETON_GAMMA}$'

# ─────────────────────────────────────────────
# Matplotlib style
# ─────────────────────────────────────────────
plt.rcParams.update({
    'font.family':      'serif',
    'font.serif':       ['Times New Roman', 'DejaVu Serif'],
    'font.size':        10,
    'axes.labelsize':   11,
    'axes.titlesize':   11,
    'legend.fontsize':  9,
    'xtick.labelsize':  9,
    'ytick.labelsize':  9,
    'lines.linewidth':  1.6,
    'lines.markersize': 5,
    'figure.dpi':       150,
    'savefig.dpi':      300,
    'savefig.bbox':     'tight',
    'axes.grid':        True,
    'grid.linestyle':   '--',
    'grid.alpha':       0.4,
})

# Colour / marker scheme (IEEE-friendly, distinguishable in B&W print)
STYLE_MAP = {
    'CCSDS-Static-AWGN':          {'color': '#1f77b4', 'marker': 'o',  'ls': '-',  'label': 'CCSDS Static (AWGN)'},
    'DET-Static-AWGN':             {'color': '#ff7f0e', 'marker': 's',  'ls': '--', 'label': 'DET Static (AWGN)'},
    'CCSDS-Static-Middleton':      {'color': '#d62728', 'marker': 'D',  'ls': '-',  'label': 'CCSDS Static (Middleton)'},
    'DET-Static-Middleton':        {'color': '#9467bd', 'marker': '^',  'ls': '--', 'label': 'DET Static (Middleton)'},
    'Proposed-Adaptive-Middleton': {'color': '#2ca02c', 'marker': '*',  'ls': '-',  'label': 'Proposed Adaptive DET (Middleton)'},
    'Proposed-Adaptive-AWGN':      {'color': '#8c564b', 'marker': 'P',  'ls': '--', 'label': 'Proposed Adaptive DET (AWGN)'},
}

# ─────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────
def load_results():
    """Return dict: {(label, block_size): list_of_point_dicts}"""
    data = {}
    for fpath in glob.glob(os.path.join(RESULTS_DIR, '*.json')):
        with open(fpath) as f:
            points = json.load(f)
        if points:
            label = points[0]['experiment']
            N     = points[0]['block_size']
            data[(label, N)] = points
    return data


def get_curve(data, label, N):
    """Extract (snr_arr, ber_arr, bler_arr, iter_arr) for a given key."""
    pts = data.get((label, N), [])
    if not pts:
        return None, None, None, None
    snr   = np.array([p['snr_db']    for p in pts])
    ber   = np.array([p['ber']       for p in pts], dtype=float)
    bler  = np.array([p['bler']      for p in pts], dtype=float)
    iters = np.array([p['mean_iters'] for p in pts], dtype=float)
    return snr, ber, bler, iters


# ─────────────────────────────────────────────
# Figure helpers
# ─────────────────────────────────────────────
def _ber_axis(ax, title):
    ax.set_yscale('log')
    ax.set_xlabel(r'$E_b/N_0$ (dB)')
    ax.set_ylabel('Bit Error Rate (BER)')
    ax.set_title(title)
    ax.set_ylim(1e-6, 1.0)
    ax.yaxis.set_major_locator(ticker.LogLocator(base=10, numticks=8))
    ax.legend(loc='lower left', framealpha=0.9)


def _bler_axis(ax, title):
    ax.set_yscale('log')
    ax.set_xlabel(r'$E_b/N_0$ (dB)')
    ax.set_ylabel('Block Error Rate (BLER)')
    ax.set_title(title)
    ax.set_ylim(1e-4, 1.0)
    ax.legend(loc='lower left', framealpha=0.9)


# ─────────────────────────────────────────────
# Figure 1 – BER vs Eb/N0 under AWGN
# ─────────────────────────────────────────────
def fig1_ber_awgn(data):
    AWGN_LABELS = ['CCSDS-Static-AWGN', 'DET-Static-AWGN', 'Proposed-Adaptive-AWGN']
    fig, axes = plt.subplots(1, 2, figsize=(7.16, 3.2), sharey=True)

    for ax, N in zip(axes, _N_PANELS):
        for label in AWGN_LABELS:
            snr, ber, _, _ = get_curve(data, label, N)
            if snr is None:
                continue
            st = STYLE_MAP[label]
            mask = ber > 0
            # Apply systematic x-jitter to make overlapping lines visible
            jitter = 0.0
            if 'Proposed' in label:
                jitter = 0.04
            elif 'DET' in label:
                jitter = 0.02
                
            x_plot = snr[mask] + jitter
            ax.semilogy(x_plot, ber[mask],
                        marker=st['marker'], ls=st['ls'], color=st['color'],
                        label=st['label'])
        ax.set_title(f'AWGN, N={N}')
        _ber_axis(ax, f'AWGN Channel, $N={N}$')

    axes[1].legend_.remove() if axes[1].get_legend() else None
    axes[0].legend(loc='lower left', fontsize=8, framealpha=0.9)
    fig.suptitle(r'BER vs $E_b/N_0$ – AWGN Baseline', fontsize=11, y=1.01)
    fig.tight_layout()
    out = os.path.join(FIGURES_DIR, 'fig1_ber_awgn.pdf')
    fig.savefig(out)
    plt.close(fig)
    print(f'  Saved: {out}')


# ─────────────────────────────────────────────
# Figure 2 – BER vs Eb/N0 under Middleton Class-A
# ─────────────────────────────────────────────
def fig2_ber_middleton(data):
    MID_LABELS = ['CCSDS-Static-Middleton', 'DET-Static-Middleton',
                  'Proposed-Adaptive-Middleton']
    fig, axes = plt.subplots(1, 2, figsize=(7.16, 3.2), sharey=True)

    for ax, N in zip(axes, _N_PANELS):
        for label in MID_LABELS:
            snr, ber, _, _ = get_curve(data, label, N)
            if snr is None:
                continue
            st = STYLE_MAP[label]
            mask = ber > 0
            
            # Apply systematic x-jitter to make overlapping lines visible
            jitter = 0.0
            if 'Proposed' in label:
                jitter = 0.04
            elif 'DET' in label:
                jitter = 0.02
                
            x_plot = snr[mask] + jitter
            ax.semilogy(x_plot, ber[mask],
                        marker=st['marker'], ls=st['ls'], color=st['color'],
                        label=st['label'])
        _ber_axis(ax, f'Middleton Class-A, $N={N}$')

    axes[1].get_legend().remove() if axes[1].get_legend() else None
    axes[0].legend(loc='lower left', fontsize=8, framealpha=0.9)
    fig.suptitle(rf'BER vs $E_b/N_0$ – {_MID_LABEL}', fontsize=11, y=1.01)
    fig.tight_layout()
    out = os.path.join(FIGURES_DIR, 'fig2_ber_middleton.pdf')
    fig.savefig(out)
    plt.close(fig)
    print(f'  Saved: {out}')


# ─────────────────────────────────────────────
# Figure 3 – BLER comparison (N=1024)
# ─────────────────────────────────────────────
def fig3_bler(data):
    LABELS = [
        'CCSDS-Static-AWGN',
        'DET-Static-AWGN',
        'Proposed-Adaptive-AWGN',
        'CCSDS-Static-Middleton',
        'DET-Static-Middleton',
        'Proposed-Adaptive-Middleton'
    ]
    N = _N_LARGE
    fig, ax = plt.subplots(figsize=(3.5, 3.2))
    for label in LABELS:
        snr, _, bler, _ = get_curve(data, label, N)
        if snr is None:
            continue
        st = STYLE_MAP[label]
        mask = bler > 0
        
        # Apply systematic x-jitter to make overlapping lines visible
        jitter = 0.0
        if 'Proposed' in label:
            jitter = 0.04
        elif 'DET-Static' in label:
            jitter = 0.02
            
        x_plot = snr[mask] + jitter
        ax.semilogy(x_plot, bler[mask],
                    marker=st['marker'], ls=st['ls'], color=st['color'],
                    label=st['label'])
    _bler_axis(ax, f'BLER Comparison ($N={N}$)')
    out = os.path.join(FIGURES_DIR, 'fig3_bler_comparison.pdf')
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f'  Saved: {out}')


# ─────────────────────────────────────────────
# Figure 4 – Avg iterations (power savings)
# ─────────────────────────────────────────────
def fig4_iter_savings(data):
    fig, axes = plt.subplots(1, 2, figsize=(7.16, 3.2), sharey=False)

    pairs = [
        ('AWGN',      [('CCSDS-Static-AWGN', 'No DET'),
                        ('DET-Static-AWGN',   'DET Only'),
                        ('Proposed-Adaptive-AWGN', 'Adaptive+DET')]),
        ('Middleton', [('CCSDS-Static-Middleton', 'No DET'),
                        ('DET-Static-Middleton',   'DET Only'),
                        ('Proposed-Adaptive-Middleton', 'Adaptive+DET')]),
    ]
    N = _N_LARGE

    for ax, (ch_name, entries) in zip(axes, pairs):
        for label, short_name in entries:
            snr, _, _, iters = get_curve(data, label, N)
            if snr is None:
                continue
            st = STYLE_MAP[label]
            # Add small x-jitter for Proposed-Adaptive-AWGN to make the overlapping line visible
            x_plot = snr + 0.04 if label == 'Proposed-Adaptive-AWGN' else snr
            ax.plot(x_plot, iters, marker=st['marker'], ls=st['ls'],
                    color=st['color'], label=short_name)
        ax.axhline(MAX_ITERATIONS, color='grey', ls=':', lw=1,
                   label=f'Max ({MAX_ITERATIONS} iters)')
        ax.set_xlabel(r'$E_b/N_0$ (dB)')
        ax.set_ylabel('Average Iterations per Frame')
        ax.set_title(f'{ch_name} Channel ($N={N}$)')
        ax.set_ylim(0, MAX_ITERATIONS + 2)
        ax.legend(fontsize=8, framealpha=0.9)

    fig.suptitle('Decoder Iteration Count – Power Savings via DET', fontsize=11, y=1.01)
    fig.tight_layout()
    out = os.path.join(FIGURES_DIR, 'fig4_iter_savings.pdf')
    fig.savefig(out)
    plt.close(fig)
    print(f'  Saved: {out}')


# ─────────────────────────────────────────────
# Figure 5 – Cross-Entropy convergence traces
# ─────────────────────────────────────────────
def fig5_ce_traces(data):
    """Plot CE vs iteration for 3 representative SNR points."""
    LABELS = ['DET-Static-Middleton', 'Proposed-Adaptive-Middleton']
    N = _N_LARGE
    TARGET_SNRS = _CE_SNRS

    fig, axes = plt.subplots(1, 3, figsize=(7.16, 3.0), sharey=True)
    for ax, snr_target in zip(axes, TARGET_SNRS):
        for label in LABELS:
            pts = data.get((label, N), [])
            # Find closest SNR point
            closest = min(pts, key=lambda p: abs(p['snr_db'] - snr_target), default=None)
            if closest is None or not closest.get('ce_traces'):
                continue
            # Average CE across stored frames
            traces = closest['ce_traces']
            max_len = max(len(t) for t in traces)
            padded = [t + [t[-1]] * (max_len - len(t)) for t in traces]
            mean_ce = np.mean(padded, axis=0)
            st = STYLE_MAP[label]
            ax.plot(range(1, len(mean_ce) + 1), mean_ce,
                    marker=st['marker'], ls=st['ls'], color=st['color'],
                    label=st['label'])
        ax.axhline(DET_DELTA, color='red', ls=':', lw=0.8,
                   label=f'$\\delta_{{CE}}={DET_DELTA}$')
        ax.axvline(DET_START_ITER, color='green', ls='--', lw=0.8,
                   label=f'DET start (iter {DET_START_ITER})')
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Cross-Entropy') if ax == axes[0] else None
        ax.set_title(f'$E_b/N_0 = {snr_target:.1f}$ dB')
        ax.legend(fontsize=7, framealpha=0.9)

    fig.suptitle(f'CE Convergence per Iteration (Middleton, $N={_N_LARGE}$)', fontsize=11, y=1.01)
    fig.tight_layout()
    out = os.path.join(FIGURES_DIR, 'fig5_ce_traces.pdf')
    fig.savefig(out)
    plt.close(fig)
    print(f'  Saved: {out}')


# ─────────────────────────────────────────────
# Figure 6 – Error floor zoom (high-SNR region)
# ─────────────────────────────────────────────
def fig6_error_floor_zoom(data):
    LABELS = ['CCSDS-Static-Middleton', 'DET-Static-Middleton',
              'Proposed-Adaptive-Middleton']
    N = _N_LARGE
    fig, ax = plt.subplots(figsize=(3.5, 3.2))
    for label in LABELS:
        snr, ber, _, _ = get_curve(data, label, N)
        if snr is None:
            continue
        st = STYLE_MAP[label]
        # Restrict to upper half of the SNR sweep range (error-floor region)
        mask = (snr >= _FLOOR_SNR_CUTOFF) & (ber > 0)
        if not mask.any():
            continue
        ax.semilogy(snr[mask], ber[mask],
                    marker=st['marker'], ls=st['ls'], color=st['color'],
                    label=st['label'])
    ax.set_xlabel(r'$E_b/N_0$ (dB)')
    ax.set_ylabel('BER')
    ax.set_title(f'Error Floor Region ($N={N}$, {_MID_LABEL})')
    ax.legend(fontsize=8, framealpha=0.9)
    ax.set_ylim(1e-6, 1e-1)
    fig.tight_layout()
    out = os.path.join(FIGURES_DIR, 'fig6_error_floor_zoom.pdf')
    fig.savefig(out)
    plt.close(fig)
    print(f'  Saved: {out}')


# ─────────────────────────────────────────────
# LaTeX summary table
# ─────────────────────────────────────────────
def print_latex_table(data):
    """Print a LaTeX table of key metrics at the closest SNR point to 4 dB."""
    N = _N_LARGE
    ALL_LABELS = list(STYLE_MAP.keys())

    rows = []
    for label in ALL_LABELS:
        pts = data.get((label, N), [])
        if not pts:
            continue
        closest = min(pts, key=lambda p: abs(p['snr_db'] - _TARGET_SNR))
        ber   = closest['ber']
        bler  = closest['bler']
        iters = closest['mean_iters']
        # Power saving vs static 12-iter baseline
        saving = 100.0 * (MAX_ITERATIONS - iters) / MAX_ITERATIONS
        rows.append((STYLE_MAP[label]['label'], ber, bler, iters, saving))

    print('\n% ──────────────────────────────────────────────────────────')
    print(f'% Table: Key metrics at Eb/N0 ≈ {_TARGET_SNR:.1f} dB, N = {_N_LARGE}')
    print('% ──────────────────────────────────────────────────────────')
    print(r'\begin{table}[t]')
    print(r'\centering')
    print(f'\\caption{{Performance metrics at $E_b/N_0 \\approx {_TARGET_SNR:.1f}$\\,dB ($N={_N_LARGE}$)}}')
    print(r'\label{tab:metrics}')
    print(r'\begin{tabular}{lcccc}')
    print(r'\toprule')
    print(r'Scheme & BER & BLER & Avg Iters & Power Saving (\%) \\')
    print(r'\midrule')
    for name, ber, bler, iters, saving in rows:
        ber_str  = f'{ber:.2e}'  if not np.isnan(ber)  else '--'
        bler_str = f'{bler:.3f}' if not np.isnan(bler) else '--'
        print(f'{name} & {ber_str} & {bler_str} & {iters:.1f} & {saving:.1f}\\\\')
    print(r'\bottomrule')
    print(r'\end{tabular}')
    print(r'\end{table}')


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    print('Loading results …')
    data = load_results()
    if not data:
        print(f'ERROR: No JSON files found in {RESULTS_DIR}.\n'
              f'Please run `python run_simulation.py` first.')
        return

    keys = sorted(data.keys())
    print(f'Found {len(keys)} result sets: {[k[0] for k in keys]}')

    print('\nGenerating figures …')
    fig1_ber_awgn(data)
    fig2_ber_middleton(data)
    fig3_bler(data)
    fig4_iter_savings(data)
    fig5_ce_traces(data)
    fig6_error_floor_zoom(data)

    print_latex_table(data)
    print('\nAnalysis complete.  Figures in:', FIGURES_DIR)


if __name__ == '__main__':
    main()
