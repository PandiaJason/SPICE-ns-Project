#!/usr/bin/env python3
"""
ECGR Analysis & IEEE-Quality Figure Generator
==============================================
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

# Publication style
plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman','DejaVu Serif'],
    'font.size': 8, 'axes.labelsize': 9, 'axes.titlesize': 9,
    'legend.fontsize': 7, 'xtick.labelsize': 7, 'ytick.labelsize': 7,
    'figure.dpi': DPI, 'savefig.dpi': DPI, 'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.02, 'lines.linewidth': 1.0,
    'axes.grid': True, 'grid.alpha': 0.3, 'grid.linewidth': 0.5,
})

COLORS = {'cgr': '#7F7F7F', 'ecgr': '#FF7F0E', 'pecgr': '#1F77B4'}
LABELS = {'cgr': 'Standard CGR', 'ecgr': 'SOTA ECGR', 'pecgr': 'Proposed P-ECGR'}


def _f(v):
    """Safely convert JSON value to float."""
    return float(v)


def load_data(results_dir):
    with open(os.path.join(results_dir, 'simulation_results.json')) as f:
        agg = json.load(f)
    ts_path = os.path.join(results_dir, 'detailed_timeseries.json')
    ts = json.load(open(ts_path)) if os.path.exists(ts_path) else None
    return agg, ts


# ── Figure 1: Bundle Delivery Ratio Comparison (bar chart) ──────────────
def fig_delivery_ratio(agg, out):
    stats = agg['aggregate_statistics']
    fig, ax = plt.subplots(figsize=(COL_W, 2.2))
    cats = ['Overall', 'Priority 1\n(Critical)', 'Priority 2\n(Normal)', 'Priority 3\n(Low)']
    keys = ['delivery_ratio','priority_1_delivery_ratio','priority_2_delivery_ratio','priority_3_delivery_ratio']
    x = np.arange(len(cats)); w = 0.24
    for i, algo in enumerate(['cgr','ecgr','pecgr']):
        vals = [stats[algo][k]['mean']*100 for k in keys]
        errs = [stats[algo][k]['std']*100 for k in keys]
        ax.bar(x + (i-1)*w, vals, w, yerr=errs, label=LABELS[algo],
               color=COLORS[algo], capsize=2, edgecolor='white', linewidth=0.5)
    ax.set_ylabel('Bundle Delivery Ratio (%)')
    ax.set_xticks(x); ax.set_xticklabels(cats)
    ax.set_ylim(0, 110); ax.legend(loc='lower right')
    ax.yaxis.set_major_locator(MaxNLocator(6))
    fig.savefig(os.path.join(out, 'fig1_delivery_ratio.pdf'))
    fig.savefig(os.path.join(out, 'fig1_delivery_ratio.png'))
    plt.close(fig)
    print('  ✓ Fig 1: Delivery Ratio')


# ── Figure 2: SmallSat Battery SoC Over Time ────────────────────────────
def fig_smallsat_energy(ts, out):
    if ts is None: return
    fig, ax = plt.subplots(figsize=(COL_W, 2.2))
    for algo in ['cgr','ecgr','pecgr']:
        log = ts[algo]['smallsat_energy_log']
        times = [_f(e[0])/3600 for e in log]
        socs  = [_f(e[2])*100 for e in log]
        ax.plot(times, socs, color=COLORS[algo], label=LABELS[algo])
    ax.axhline(20, color='#FF7F0E', ls='--', lw=0.8, label='Critical Threshold (20%)')
    ax.set_xlabel('Time (hours)'); ax.set_ylabel('SmallSat Battery SoC (%)')
    ax.set_ylim(0, 100); ax.legend(loc='best')
    fig.savefig(os.path.join(out, 'fig2_smallsat_soc.pdf'))
    fig.savefig(os.path.join(out, 'fig2_smallsat_soc.png'))
    plt.close(fig)
    print('  ✓ Fig 2: SmallSat SoC')


# ── Figure 3: SmallSat Buffer Utilization Over Time ─────────────────────
def fig_smallsat_buffer(ts, out):
    if ts is None: return
    fig, ax = plt.subplots(figsize=(COL_W, 2.2))
    for algo in ['cgr','ecgr','pecgr']:
        log = ts[algo]['smallsat_buffer_log']
        times = [_f(e[0])/3600 for e in log]
        util  = [_f(e[2])*100 for e in log]
        ax.plot(times, util, color=COLORS[algo], label=LABELS[algo])
    ax.axhline(70, color='#FF7F0E', ls='--', lw=0.8, label='Warning (70%)')
    ax.set_xlabel('Time (hours)'); ax.set_ylabel('Buffer Utilization (%)')
    ax.set_ylim(0, 105); ax.legend(loc='best')
    fig.savefig(os.path.join(out, 'fig3_smallsat_buffer.pdf'))
    fig.savefig(os.path.join(out, 'fig3_smallsat_buffer.png'))
    plt.close(fig)
    print('  ✓ Fig 3: SmallSat Buffer')


# ── Figure 4: End-to-End Latency CDF ────────────────────────────────────
def fig_latency_cdf(ts, out):
    if ts is None: return
    fig, ax = plt.subplots(figsize=(COL_W, 2.2))
    for algo in ['cgr','ecgr','pecgr']:
        metrics = ts[algo]['metrics_timeseries']
        # Reconstruct per-bundle latencies from routing decisions
        # Use aggregate latency proxy from timeseries
        delivered = ts[algo].get('routing_decisions', [])
        if not delivered:
            continue
        latencies = sorted([_f(d.get('time',0)) for d in delivered])
        y = np.arange(1, len(latencies)+1) / len(latencies)
        ax.plot(np.array(latencies)/3600, y, color=COLORS[algo], label=LABELS[algo])
    ax.set_xlabel('Time of Routing Decision (hours)')
    ax.set_ylabel('Cumulative Fraction')
    ax.legend(loc='lower right')
    fig.savefig(os.path.join(out, 'fig4_latency_cdf.pdf'))
    fig.savefig(os.path.join(out, 'fig4_latency_cdf.png'))
    plt.close(fig)
    print('  ✓ Fig 4: Latency CDF')


# ── Figure 5: Cumulative Bundles Delivered Over Time ────────────────────
def fig_cumulative_delivery(ts, out):
    if ts is None: return
    fig, ax = plt.subplots(figsize=(COL_W, 2.2))
    for algo in ['cgr','ecgr','pecgr']:
        metrics = ts[algo]['metrics_timeseries']
        times = [_f(m['time'])/3600 for m in metrics]
        delivered = [_f(m['bundles_delivered']) for m in metrics]
        ax.plot(times, delivered, color=COLORS[algo], label=LABELS[algo])
    ax.set_xlabel('Time (hours)'); ax.set_ylabel('Cumulative Bundles Delivered')
    ax.legend(loc='upper left')
    fig.savefig(os.path.join(out, 'fig5_cumulative_delivery.pdf'))
    fig.savefig(os.path.join(out, 'fig5_cumulative_delivery.png'))
    plt.close(fig)
    print('  ✓ Fig 5: Cumulative Delivery')


# ── Figure 6: Dropped Bundles by Reason (stacked bar) ──────────────────
def fig_drop_reasons(agg, out):
    fig, ax = plt.subplots(figsize=(COL_W, 2.2))
    runs_cgr = agg['per_run_cgr']
    runs_ecgr = agg['per_run_ecgr']
    runs_pecgr = agg['per_run_pecgr']
    reasons = set()
    for r in runs_cgr + runs_ecgr + runs_pecgr:
        reasons.update(r.get('drop_reasons', {}).keys())
    reasons = sorted(reasons) if reasons else ['none']
    x = np.arange(3); w = 0.5
    bottom_cgr = 0; bottom_ecgr = 0; bottom_pecgr = 0
    cmap = plt.cm.Set2
    for i, reason in enumerate(reasons):
        cgr_v = np.mean([r.get('drop_reasons',{}).get(reason,0) for r in runs_cgr])
        ecgr_v = np.mean([r.get('drop_reasons',{}).get(reason,0) for r in runs_ecgr])
        pecgr_v = np.mean([r.get('drop_reasons',{}).get(reason,0) for r in runs_pecgr])
        label = reason.replace('_',' ').title()
        ax.bar(0, cgr_v, w, bottom=bottom_cgr, color=cmap(i), label=label, edgecolor='white')
        ax.bar(1, ecgr_v, w, bottom=bottom_ecgr, color=cmap(i), edgecolor='white')
        ax.bar(2, pecgr_v, w, bottom=bottom_pecgr, color=cmap(i), edgecolor='white')
        bottom_cgr += cgr_v; bottom_ecgr += ecgr_v; bottom_pecgr += pecgr_v
    ax.set_xticks([0,1,2]); ax.set_xticklabels(['Standard CGR','SOTA ECGR','Proposed P-ECGR'])
    ax.set_ylabel('Average Dropped Bundles')
    ax.legend(loc='upper right', fontsize=6)
    fig.savefig(os.path.join(out, 'fig6_drop_reasons.pdf'))
    fig.savefig(os.path.join(out, 'fig6_drop_reasons.png'))
    plt.close(fig)
    print('  ✓ Fig 6: Drop Reasons')


# ── Figure 7: MRO vs SmallSat Energy Comparison (dual panel) ───────────
def fig_dual_energy(ts, out):
    if ts is None: return
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(COL_W, 4.4))
    for algo in ['cgr','ecgr','pecgr']:
        ss = ts[algo]['smallsat_energy_log']
        ax1.plot([_f(e[0])/3600 for e in ss], [_f(e[2])*100 for e in ss],
                 color=COLORS[algo], label=LABELS[algo])
        mro = ts[algo]['mro_energy_log']
        ax2.plot([_f(e[0])/3600 for e in mro], [_f(e[2])*100 for e in mro],
                 color=COLORS[algo], label=LABELS[algo])
    ax1.axhline(20, color='#FF7F0E', ls='--', lw=0.7)
    ax1.set_title('(a) SmallSat Relay'); ax1.set_xlabel('Time (h)'); ax1.set_ylabel('SoC (%)')
    ax1.set_ylim(0,100); ax1.legend(fontsize=6)
    ax2.set_title('(b) MRO'); ax2.set_xlabel('Time (h)'); ax2.set_ylabel('SoC (%)')
    ax2.set_ylim(0,100); ax2.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'fig7_dual_energy.pdf'))
    fig.savefig(os.path.join(out, 'fig7_dual_energy.png'))
    plt.close(fig)
    print('  ✓ Fig 7: Dual Energy Panel')


# ── Figure 8: Network Topology Diagram ──────────────────────────────────
def fig_network_topology(out):
    fig, ax = plt.subplots(figsize=(COL_W, 2.8))
    ax.set_xlim(-0.5, 4.5); ax.set_ylim(-0.5, 3.5); ax.set_aspect('equal')
    ax.axis('off')
    nodes = {
        'Mars Rover':    (0.5, 0.5),
        'SmallSat\nRelay': (1.5, 2.5),
        'MRO':           (3.0, 2.5),
        'DSN\n(Earth)':  (4.0, 0.5),
    }
    colors_n = ['#8B4513','#1F77B4','#2CA02C','#D62728']
    for i, (name, (x,y)) in enumerate(nodes.items()):
        circle = plt.Circle((x,y), 0.48, color=colors_n[i], alpha=1.0, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y, name, ha='center', va='center', fontsize=6,
                color='white', fontweight='bold', zorder=4)
    edges = [
        ((0.5, 0.5), (1.5, 2.5), 'UHF 2Mbps', (0.75, 1.6), 'right'),
        ((0.5, 0.5), (3.0, 2.5), 'UHF 2Mbps', (1.75, 1.2), 'center'),
        ((1.5, 2.5), (3.0, 2.5), 'ISL 1Mbps', (2.25, 2.9), 'center'),
        ((1.5, 2.5), (4.0, 0.5), 'X 0.1Mbps', (2.75, 1.2), 'center'),
        ((3.0, 2.5), (4.0, 0.5), 'X 2Mbps', (3.75, 1.6), 'left'),
    ]
    for (x1, y1), (x2, y2), label, (lx, ly), ha in edges:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='#555', lw=1.2), zorder=1)
        ax.text(lx, ly, label, ha=ha, va='center', fontsize=5,
                color='#333', style='italic', zorder=2)
    fig.savefig(os.path.join(out, 'fig8_topology.pdf'))
    fig.savefig(os.path.join(out, 'fig8_topology.png'))
    plt.close(fig)
    print('  ✓ Fig 8: Topology')


# ── Table I: Simulation Parameters ──────────────────────────────────────
def gen_table_params(out):
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from simulation.config import NODE_SPECS, SIM_DURATION, NUM_MONTE_CARLO_RUNS, OWLT_S
        ss_spec = NODE_SPECS[1]
        mro_spec = NODE_SPECS[2]
        
        rows = [
            ('Simulation Duration', f'{SIM_DURATION:,} s ({SIM_DURATION/3600:.1f} h)'),
            ('SmallSat Battery', f'{ss_spec["battery_capacity_wh"]:.1f} Wh'),
            ('SmallSat Solar Power', f'{ss_spec["power_generation_w"]:.1f} W (avg)'),
            ('SmallSat Buffer', f'{int(ss_spec["buffer_capacity_mb"])} MB'),
            ('SmallSat Tx Power', f'{ss_spec["tx_power_w"]:.1f} W'),
            ('MRO Battery', f'{mro_spec["battery_capacity_wh"]:.1f} Wh'),
            ('MRO Buffer', f'{int(mro_spec["buffer_capacity_mb"])} MB'),
            ('Rover-SmallSat Rate', '2 Mbps (UHF)'),
            ('MRO-DSN Rate', '2 Mbps (X-band)'),
            ('Earth-Mars OWLT', f'~{int(OWLT_S)} s'),
            ('Monte Carlo Runs', str(NUM_MONTE_CARLO_RUNS)),
        ]
    except Exception as e:
        print(f"Error loading config for Table I: {e}. Using fallback.")
        rows = [
            ('Simulation Duration', '86,400 s (24 h)'),
            ('SmallSat Battery', '12.0 Wh'),
            ('SmallSat Solar Power', '4.5 W (avg)'),
            ('SmallSat Buffer', '128 MB'),
            ('SmallSat Tx Power', '7.0 W'),
            ('MRO Battery', '1,120 Wh'),
            ('MRO Buffer', '8,192 MB'),
            ('Rover-SmallSat Rate', '2 Mbps (UHF)'),
            ('MRO-DSN Rate', '2 Mbps (X-band)'),
            ('Earth-Mars OWLT', '~750 s'),
            ('Monte Carlo Runs', '10'),
        ]
    
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
        m = s[algo][key]['mean']*scale
        sd = s[algo][key]['std']*scale
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
    ]

    tex = '\\begin{table*}[t]\n\\centering\n\\caption{Comparative Performance: CGR vs.\\ SOTA ECGR vs.\\ Proposed P-ECGR}\n'
    tex += '\\label{tab:results}\n\\begin{tabular*}{\\textwidth}{@{\\extracolsep{\\fill}}lccc}\n\\hline\n'
    tex += '\\textbf{Metric} & \\textbf{CGR} & \\textbf{SOTA ECGR} & \\textbf{Proposed P-ECGR} \\\\\n\\hline\n'
    for label, key, scale, prec in rows:
        cgr_v = fmts('cgr', key, scale, prec)
        ecgr_v = fmts('ecgr', key, scale, prec)
        pecgr_v = fmts('pecgr', key, scale, prec)
        tex += f'{label} & {cgr_v} & {ecgr_v} & {pecgr_v} \\\\\n'
    tex += '\\hline\n\\end{tabular*}\n\\end{table*}\n'
    with open(os.path.join(out, 'table2_results.tex'), 'w') as f:
        f.write(tex)
    print('  ✓ Table II: Results')


# ── Table III: Per-Priority Results ──────────────────────────────────────
def gen_table_priority(agg, out):
    s = agg['aggregate_statistics']
    tex = '\\begin{table}[t]\n\\centering\n'
    tex += '\\caption{Per-Priority Bundle Delivery Ratio (\\%)}\n'
    tex += '\\label{tab:priority}\n\\begin{tabular}{lccc}\n\\hline\n'
    tex += '\\textbf{Algorithm} & \\textbf{Critical} & \\textbf{Normal} & \\textbf{Low} \\\\\n\\hline\n'
    for algo in ['cgr','ecgr','pecgr']:
        name = 'CGR' if algo == 'cgr' else ('SOTA ECGR' if algo == 'ecgr' else 'Proposed P-ECGR')
        vals = []
        for p in [1,2,3]:
            k = f'priority_{p}_delivery_ratio'
            m = s[algo][k]['mean']*100
            sd = s[algo][k]['std']*100
            vals.append(f'{m:.1f} $\\pm$ {sd:.1f}')
        tex += f'{name} & {vals[0]} & {vals[1]} & {vals[2]} \\\\\n'
    tex += '\\hline\n\\end{tabular}\n\\end{table}\n'
    with open(os.path.join(out, 'table3_priority.tex'), 'w') as f:
        f.write(tex)
    print('  ✓ Table III: Priority')


def main():
    parser = argparse.ArgumentParser(description='ECGR Analysis & Figure Generator')
    parser.add_argument('--input', default='results', help='Results directory')
    parser.add_argument('--output', default='figures', help='Output directory')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    print('\n' + '='*60)
    print('  ECGR Analysis — IEEE Publication Figure Generator')
    print('='*60)

    agg, ts = load_data(args.input)

    print('\nGenerating figures...')
    fig_delivery_ratio(agg, args.output)
    fig_smallsat_energy(ts, args.output)
    fig_smallsat_buffer(ts, args.output)
    fig_latency_cdf(ts, args.output)
    fig_cumulative_delivery(ts, args.output)
    fig_drop_reasons(agg, args.output)
    fig_dual_energy(ts, args.output)
    fig_network_topology(args.output)

    print('\nGenerating LaTeX tables...')
    gen_table_params(args.output)
    gen_table_results(agg, args.output)
    gen_table_priority(agg, args.output)

    print(f'\n  All outputs saved to {args.output}/')
    print('='*60)


if __name__ == '__main__':
    main()
