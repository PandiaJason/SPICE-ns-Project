#!/usr/bin/env python3
"""
ML-CGR Analysis & IEEE-Quality Figure Generator
================================================
Reads simulation output JSON and produces publication-ready figures/tables.

Usage:
    python analyze_results.py [--input results/] [--output figures/]
"""

import argparse, json, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib.gridspec as gridspec

# IEEE two-column figure widths (inches)
COL_W = 3.45
FULL_W = 7.16
DPI = 300

plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 8, 'axes.labelsize': 9, 'axes.titlesize': 9,
    'legend.fontsize': 7, 'xtick.labelsize': 7, 'ytick.labelsize': 7,
    'figure.dpi': DPI, 'savefig.dpi': DPI, 'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.02, 'lines.linewidth': 1.0,
    'axes.grid': True, 'grid.alpha': 0.3, 'grid.linewidth': 0.5,
})

COLORS = {'cgr': '#7F7F7F', 'mlcgr': '#1F77B4'}
LABELS = {'cgr': 'Standard CGR', 'mlcgr': 'Proposed ML-CGR'}
HATCHES = {'cgr': '', 'mlcgr': '//'}


def _f(v):
    return float(v)


def load_data(results_dir):
    with open(os.path.join(results_dir, 'simulation_results.json')) as f:
        agg = json.load(f)
    ts_path = os.path.join(results_dir, 'detailed_timeseries.json')
    ts = json.load(open(ts_path)) if os.path.exists(ts_path) else None
    return agg, ts


# ── Figure 1: Bundle Delivery Ratio Comparison ───────────────────────────
def fig_delivery_ratio(agg, out):
    stats = agg['aggregate_statistics']
    fig, ax = plt.subplots(figsize=(COL_W, 2.4))
    cats = ['Overall', 'Priority 1\n(Critical)', 'Priority 2\n(Normal)', 'Priority 3\n(Low)']
    keys = ['delivery_ratio', 'priority_1_delivery_ratio',
            'priority_2_delivery_ratio', 'priority_3_delivery_ratio']
    x = np.arange(len(cats)); w = 0.32
    for i, algo in enumerate(['cgr', 'mlcgr']):
        vals = [stats[algo][k]['mean'] * 100 for k in keys]
        errs = [stats[algo][k]['std'] * 100 for k in keys]
        ax.bar(x + (i - 0.5) * w, vals, w, yerr=errs,
               label=LABELS[algo], color=COLORS[algo],
               capsize=2, edgecolor='white', linewidth=0.5,
               hatch=HATCHES[algo], alpha=0.85)
    ax.set_ylabel('Bundle Delivery Ratio (%)')
    ax.set_xticks(x); ax.set_xticklabels(cats)
    ax.set_ylim(0, 115); ax.legend(loc='lower right')
    ax.yaxis.set_major_locator(MaxNLocator(6))
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'fig1_delivery_ratio.pdf'))
    fig.savefig(os.path.join(out, 'fig1_delivery_ratio.png'))
    plt.close(fig)
    print('  ✓ Fig 1: Delivery Ratio')


# ── Figure 2: SmallSat Battery SoC Over Time ─────────────────────────────
def fig_smallsat_energy(ts, out):
    if ts is None: return
    fig, ax = plt.subplots(figsize=(COL_W, 2.2))
    for algo in ['cgr', 'mlcgr']:
        log = ts[algo]['smallsat_energy_log']
        times = [_f(e[0]) / 3600 for e in log]
        socs = [_f(e[2]) * 100 for e in log]
        ax.plot(times, socs, color=COLORS[algo], label=LABELS[algo])
    ax.axhline(20, color='red', ls='--', lw=0.8, label='Critical (20%)')
    ax.axhline(35, color='orange', ls=':', lw=0.8, label='Warning (35%)')
    ax.set_xlabel('Time (hours)'); ax.set_ylabel('SmallSat Battery SoC (%)')
    ax.set_ylim(0, 100); ax.legend(loc='best', fontsize=6)
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'fig2_smallsat_soc.pdf'))
    fig.savefig(os.path.join(out, 'fig2_smallsat_soc.png'))
    plt.close(fig)
    print('  ✓ Fig 2: SmallSat SoC')


# ── Figure 3: Predicted LQI Distribution Over Time ───────────────────────
def fig_lqi_timeseries(ts, out):
    if ts is None: return
    fig, ax = plt.subplots(figsize=(COL_W, 2.2))
    ml_data = ts.get('mlcgr', {})
    decisions = ml_data.get('routing_decisions', [])
    if decisions:
        times = [_f(d['time']) / 3600 for d in decisions]
        lqis = [_f(d.get('predicted_lqi', 1.0)) for d in decisions]
        ax.scatter(times, lqis, s=4, alpha=0.5, color=COLORS['mlcgr'],
                   label='ML-CGR Predicted LQI')
        # Running average
        if len(times) > 10:
            win = max(1, len(times) // 20)
            from numpy.lib.stride_tricks import sliding_window_view
            lqi_arr = np.array(lqis)
            if len(lqi_arr) >= win:
                smooth = np.convolve(lqi_arr, np.ones(win)/win, mode='valid')
                t_smooth = times[win-1:][:len(smooth)]
                ax.plot(t_smooth, smooth, color='navy', lw=1.2,
                        label='Running mean')
    ax.axhline(0.75, color='green', ls='--', lw=0.8, label='Good (0.75)')
    ax.axhline(0.45, color='orange', ls='--', lw=0.8, label='Warn (0.45)')
    ax.axhline(0.20, color='red', ls='--', lw=0.8, label='Poor (0.20)')
    ax.set_xlabel('Time (hours)'); ax.set_ylabel('Predicted LQI')
    ax.set_ylim(0, 1.05); ax.legend(loc='lower right', fontsize=5)
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'fig3_lqi_timeseries.pdf'))
    fig.savefig(os.path.join(out, 'fig3_lqi_timeseries.png'))
    plt.close(fig)
    print('  ✓ Fig 3: LQI Time Series')


# ── Figure 4: Fragmentation Events Over Time ──────────────────────────────
def fig_fragmentation(ts, out):
    if ts is None: return
    ml_data = ts.get('mlcgr', {})
    events = ml_data.get('fragmentation_events', [])
    metrics = ml_data.get('metrics_timeseries', [])
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(COL_W, 4.0))

    if events:
        times = [_f(e['time']) / 3600 for e in events]
        lqis = [_f(e['predicted_lqi']) for e in events]
        n_frags = [_f(e['n_fragments']) for e in events]
        sc = ax1.scatter(times, lqis, c=n_frags, cmap='YlOrRd',
                         s=20, alpha=0.8, vmin=1, vmax=10)
        plt.colorbar(sc, ax=ax1, label='N fragments')
    ax1.axhline(0.75, color='green', ls='--', lw=0.8)
    ax1.axhline(0.45, color='orange', ls='--', lw=0.8)
    ax1.set_xlabel('Time (hours)'); ax1.set_ylabel('LQI at Fragmentation')
    ax1.set_title('(a) Fragmentation Events vs LQI')

    if metrics:
        times = [_f(m['time']) / 3600 for m in metrics]
        frags = [_f(m.get('fragments_created', 0)) for m in metrics]
        for algo in ['cgr', 'mlcgr']:
            m_data = ts.get(algo, {}).get('metrics_timeseries', [])
            if m_data:
                t = [_f(x['time']) / 3600 for x in m_data]
                d = [_f(x['bundles_delivered']) for x in m_data]
                ax2.plot(t, d, color=COLORS[algo], label=LABELS[algo])
    ax2.set_xlabel('Time (hours)'); ax2.set_ylabel('Cumulative Delivered')
    ax2.set_title('(b) Cumulative Bundle Delivery')
    ax2.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'fig4_fragmentation.pdf'))
    fig.savefig(os.path.join(out, 'fig4_fragmentation.png'))
    plt.close(fig)
    print('  ✓ Fig 4: Fragmentation Analysis')


# ── Figure 5: End-to-End Latency CDF ─────────────────────────────────────
def fig_latency_cdf(ts, out):
    if ts is None: return
    fig, ax = plt.subplots(figsize=(COL_W, 2.2))
    for algo in ['cgr', 'mlcgr']:
        decisions = ts.get(algo, {}).get('routing_decisions', [])
        if not decisions: continue
        latencies = sorted([_f(d.get('time', 0)) for d in decisions])
        y = np.arange(1, len(latencies) + 1) / len(latencies)
        ax.plot(np.array(latencies) / 3600, y,
                color=COLORS[algo], label=LABELS[algo])
    ax.set_xlabel('Time of Routing Decision (hours)')
    ax.set_ylabel('Cumulative Fraction')
    ax.legend(loc='lower right')
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'fig5_latency_cdf.pdf'))
    fig.savefig(os.path.join(out, 'fig5_latency_cdf.png'))
    plt.close(fig)
    print('  ✓ Fig 5: Latency CDF')


# ── Figure 6: Drop Reasons Stacked Bar ───────────────────────────────────
def fig_drop_reasons(agg, out):
    fig, ax = plt.subplots(figsize=(COL_W, 2.2))
    runs_cgr = agg['per_run_cgr']
    runs_mlcgr = agg['per_run_mlcgr']
    reasons = set()
    for r in runs_cgr + runs_mlcgr:
        reasons.update(r.get('drop_reasons', {}).keys())
    reasons = sorted(reasons) if reasons else ['none']
    x = np.arange(2); w = 0.5
    bot = [0, 0]
    cmap = plt.cm.Set2
    for i, reason in enumerate(reasons):
        cgr_v = np.mean([r.get('drop_reasons', {}).get(reason, 0) for r in runs_cgr])
        ml_v = np.mean([r.get('drop_reasons', {}).get(reason, 0) for r in runs_mlcgr])
        label = reason.replace('_', ' ').title()
        ax.bar(0, cgr_v, w, bottom=bot[0], color=cmap(i), label=label, edgecolor='white')
        ax.bar(1, ml_v, w, bottom=bot[1], color=cmap(i), edgecolor='white')
        bot[0] += cgr_v; bot[1] += ml_v
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Standard CGR', 'Proposed ML-CGR'])
    ax.set_ylabel('Average Dropped Bundles')
    ax.legend(loc='upper right', fontsize=6)
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'fig6_drop_reasons.pdf'))
    fig.savefig(os.path.join(out, 'fig6_drop_reasons.png'))
    plt.close(fig)
    print('  ✓ Fig 6: Drop Reasons')


# ── Figure 7: SmallSat Buffer Utilization ────────────────────────────────
def fig_smallsat_buffer(ts, out):
    if ts is None: return
    fig, ax = plt.subplots(figsize=(COL_W, 2.2))
    for algo in ['cgr', 'mlcgr']:
        log = ts[algo]['smallsat_buffer_log']
        times = [_f(e[0]) / 3600 for e in log]
        util = [_f(e[2]) * 100 for e in log]
        ax.plot(times, util, color=COLORS[algo], label=LABELS[algo])
    ax.axhline(70, color='orange', ls='--', lw=0.8, label='Warning (70%)')
    ax.set_xlabel('Time (hours)'); ax.set_ylabel('Buffer Utilization (%)')
    ax.set_ylim(0, 105); ax.legend(loc='best')
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'fig7_smallsat_buffer.pdf'))
    fig.savefig(os.path.join(out, 'fig7_smallsat_buffer.png'))
    plt.close(fig)
    print('  ✓ Fig 7: SmallSat Buffer')


# ── Figure 8: Network Topology ───────────────────────────────────────────
def fig_network_topology(out):
    fig, ax = plt.subplots(figsize=(COL_W, 2.8))
    ax.set_xlim(-0.5, 4.5); ax.set_ylim(-0.5, 3.5)
    ax.set_aspect('equal'); ax.axis('off')
    nodes = {
        'Mars Rover':      (0.5, 0.5),
        'SmallSat\nRelay': (1.5, 2.5),
        'MRO':             (3.0, 2.5),
        'DSN\n(Earth)':    (4.0, 0.5),
    }
    colors_n = ['#8B4513', '#1F77B4', '#2CA02C', '#D62728']
    for i, (name, (x, y)) in enumerate(nodes.items()):
        circle = plt.Circle((x, y), 0.48, color=colors_n[i], alpha=1.0, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y, name, ha='center', va='center', fontsize=6,
                color='white', fontweight='bold', zorder=4)
    edges = [
        ((0.5, 0.5), (1.5, 2.5), 'UHF 2Mbps', (0.75, 1.6), 'right'),
        ((0.5, 0.5), (3.0, 2.5), 'UHF 2Mbps', (1.75, 1.2), 'center'),
        ((1.5, 2.5), (3.0, 2.5), 'ISL 1Mbps', (2.25, 2.9), 'center'),
        ((1.5, 2.5), (4.0, 0.5), 'X 0.1Mbps', (2.75, 1.2), 'center'),
        ((3.0, 2.5), (4.0, 0.5), 'X 2Mbps',   (3.75, 1.6), 'left'),
    ]
    for (x1, y1), (x2, y2), label, (lx, ly), ha in edges:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='#555', lw=1.2), zorder=1)
        ax.text(lx, ly, label, ha=ha, va='center', fontsize=5,
                color='#333', style='italic', zorder=2)
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'fig8_topology.pdf'))
    fig.savefig(os.path.join(out, 'fig8_topology.png'))
    plt.close(fig)
    print('  ✓ Fig 8: Topology')


# ── Figure 9: ML Model Convergence ───────────────────────────────────────
def fig_ml_convergence(agg, ts, out):
    """Show how avg predicted LQI evolves across Monte Carlo runs."""
    runs_ml = agg.get('per_run_mlcgr', [])
    if not runs_ml:
        return
    lqis = [r.get('avg_predicted_lqi', 1.0) for r in runs_ml]
    fig, ax = plt.subplots(figsize=(COL_W, 2.0))
    ax.plot(range(1, len(lqis) + 1), lqis, 'o-',
            color=COLORS['mlcgr'], markersize=5, label='Avg Predicted LQI')
    ax.axhline(np.mean(lqis), color='gray', ls='--', lw=0.8,
               label=f'Mean = {np.mean(lqis):.3f}')
    ax.set_xlabel('Monte Carlo Run'); ax.set_ylabel('Avg Predicted LQI')
    ax.set_ylim(0, 1.1); ax.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'fig9_ml_convergence.pdf'))
    fig.savefig(os.path.join(out, 'fig9_ml_convergence.png'))
    plt.close(fig)
    print('  ✓ Fig 9: ML Convergence')


# ── Table I: Simulation Parameters ───────────────────────────────────────
def gen_table_params(out):
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from simulation.config import NODE_SPECS, SIM_DURATION, NUM_MONTE_CARLO_RUNS, OWLT_S
        ss = NODE_SPECS[1]; mro = NODE_SPECS[2]
        rows = [
            ('Simulation Duration', f'{SIM_DURATION:,} s ({SIM_DURATION/3600:.1f} h)'),
            ('SmallSat Battery', f'{ss["battery_capacity_wh"]:.1f} Wh'),
            ('SmallSat Solar Power', f'{ss["power_generation_w"]:.1f} W (avg)'),
            ('SmallSat Buffer', f'{int(ss["buffer_capacity_mb"])} MB'),
            ('SmallSat Tx Power', f'{ss["tx_power_w"]:.1f} W'),
            ('MRO Battery', f'{mro["battery_capacity_wh"]:.1f} Wh'),
            ('MRO Buffer', f'{int(mro["buffer_capacity_mb"])} MB'),
            ('Rover-SmallSat Rate', '2 Mbps (UHF)'),
            ('MRO-DSN Rate', '2 Mbps (X-band)'),
            ('Earth-Mars OWLT', f'~{int(OWLT_S)} s'),
            ('Monte Carlo Runs', str(NUM_MONTE_CARLO_RUNS)),
            ('ML Model', 'Random Forest (50 trees)'),
            ('ML Retrain Interval', '1800 s'),
        ]
    except Exception:
        rows = [('Simulation Duration', '86,400 s (24 h)')]

    tex = '\\begin{table}[t]\n\\centering\n\\caption{Simulation Parameters}\n'
    tex += '\\label{tab:params}\n\\begin{tabular}{ll}\n\\hline\n'
    tex += '\\textbf{Parameter} & \\textbf{Value} \\\\\n\\hline\n'
    for p, v in rows:
        tex += f'{p} & {v} \\\\\n'
    tex += '\\hline\n\\end{tabular}\n\\end{table}\n'
    with open(os.path.join(out, 'table1_params.tex'), 'w') as f:
        f.write(tex)
    print('  ✓ Table I: Parameters')


# ── Table II: Comparative Results ────────────────────────────────────────
def gen_table_results(agg, out):
    s = agg['aggregate_statistics']

    def fmts(algo, key, scale=1, prec=1):
        m = s[algo][key]['mean'] * scale
        sd = s[algo][key]['std'] * scale
        return f'{m:.{prec}f} $\\pm$ {sd:.{prec}f}'

    rows = [
        ('Bundle Delivery Ratio (\\%)', 'delivery_ratio', 100, 1),
        ('Avg. Latency (s)', 'avg_latency_s', 1, 0),
        ('95th-pct. Latency (s)', 'p95_latency_s', 1, 0),
        ('Dropped Bundles', 'dropped', 1, 1),
        ('SmallSat Min SoC (\\%)', 'smallsat_min_soc', 100, 1),
        ('SmallSat Avg SoC (\\%)', 'smallsat_avg_soc', 100, 1),
        ('Time Below 20\\% SoC (\\%)', 'smallsat_below_20pct', 100, 1),
        ('Data Delivered (MB)', 'data_delivered_mb', 1, 0),
        ('Fragmentation Events', 'n_fragmentation_events', 1, 0),
        ('Avg Predicted LQI', 'avg_predicted_lqi', 1, 3),
    ]

    tex = '\\begin{table*}[t]\n\\centering\n'
    tex += '\\caption{Comparative Performance: Standard CGR vs.\\ Proposed ML-CGR}\n'
    tex += '\\label{tab:results}\n'
    tex += '\\begin{tabular*}{\\textwidth}{@{\\extracolsep{\\fill}}lll}\n\\hline\n'
    tex += '\\textbf{Metric} & \\textbf{CGR} & \\textbf{Proposed ML-CGR} \\\\\n\\hline\n'
    for label, key, scale, prec in rows:
        if key not in s['cgr']:
            continue
        tex += f'{label} & {fmts("cgr", key, scale, prec)} & {fmts("mlcgr", key, scale, prec)} \\\\\n'
    tex += '\\hline\n\\end{tabular*}\n\\end{table*}\n'
    with open(os.path.join(out, 'table2_results.tex'), 'w') as f:
        f.write(tex)
    print('  ✓ Table II: Results')


# ── Table III: Per-Priority Results ──────────────────────────────────────
def gen_table_priority(agg, out):
    s = agg['aggregate_statistics']
    tex = '\\begin{table}[t]\n\\centering\n'
    tex += '\\caption{Per-Priority Bundle Delivery Ratio (\\%)}\n'
    tex += '\\label{tab:priority}\n\\begin{tabular}{llll}\n\\hline\n'
    tex += '\\textbf{Algorithm} & \\textbf{Critical} & \\textbf{Normal} & \\textbf{Low} \\\\\n\\hline\n'
    for algo in ['cgr', 'mlcgr']:
        name = 'CGR' if algo == 'cgr' else 'Proposed ML-CGR'
        vals = []
        for p in [1, 2, 3]:
            k = f'priority_{p}_delivery_ratio'
            m = s[algo][k]['mean'] * 100
            sd = s[algo][k]['std'] * 100
            vals.append(f'{m:.1f} $\\pm$ {sd:.1f}')
        tex += f'{name} & {vals[0]} & {vals[1]} & {vals[2]} \\\\\n'
    tex += '\\hline\n\\end{tabular}\n\\end{table}\n'
    with open(os.path.join(out, 'table3_priority.tex'), 'w') as f:
        f.write(tex)
    print('  ✓ Table III: Priority')


def main():
    parser = argparse.ArgumentParser(description='ML-CGR Analysis & Figure Generator')
    parser.add_argument('--input', default='results', help='Results directory')
    parser.add_argument('--output', default='figures', help='Output directory')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    print('\n' + '=' * 60)
    print('  ML-CGR Analysis — Publication Figure Generator')
    print('=' * 60)

    agg, ts = load_data(args.input)

    print('\nGenerating figures...')
    fig_delivery_ratio(agg, args.output)
    fig_smallsat_energy(ts, args.output)
    fig_lqi_timeseries(ts, args.output)
    fig_fragmentation(ts, args.output)
    fig_latency_cdf(ts, args.output)
    fig_drop_reasons(agg, args.output)
    fig_smallsat_buffer(ts, args.output)
    fig_network_topology(args.output)
    fig_ml_convergence(agg, ts, args.output)

    print('\nGenerating LaTeX tables...')
    gen_table_params(args.output)
    gen_table_results(agg, args.output)
    gen_table_priority(agg, args.output)

    print(f'\n  All outputs saved to {args.output}/')
    print('=' * 60)


if __name__ == '__main__':
    main()
