#!/usr/bin/env python3
"""
analyze_results.py – Loads Space-FL simulation results, generates publication-quality
                     figures, and prints a LaTeX summary table for the manuscript.

Usage:
    python analyze_results.py
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from simulation.config import RESULTS_DIR, FIGURES_DIR, EXPERIMENTS, STALENESS_BETA, DTN_MAX_DELAY

# Academic styling for IEEE journals
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
    'lines.markersize': 4,
    'figure.dpi':       150,
    'savefig.dpi':      300,
    'savefig.bbox':     'tight',
    'axes.grid':        True,
    'grid.linestyle':   '--',
    'grid.alpha':       0.4,
})

# Harmonious, IEEE-friendly color palette
COLOR_MAP = {
    'FedAvg-Standard':          '#d62728', # Red (Failures/Baseline)
    'FedProx-Standard':         '#ff7f0e', # Orange
    'Asynchronous-FL-NoComp':   '#1f77b4', # Blue
    'DAFL-Proposed':            '#2ca02c', # Green (Proposed)
}

MARKER_MAP = {
    'FedAvg-Standard':          'x',
    'FedProx-Standard':         's',
    'Asynchronous-FL-NoComp':   '^',
    'DAFL-Proposed':            'o',
}

LABEL_MAP = {
    'FedAvg-Standard':          'Standard Sync FedAvg',
    'FedProx-Standard':         'Standard Sync FedProx',
    'Asynchronous-FL-NoComp':   'Async FL (No Comp/Pruning)',
    'DAFL-Proposed':            'DAFL (Proposed)',
}

def load_results():
    data = {}
    for exp in EXPERIMENTS:
        label = exp['label']
        path = os.path.join(RESULTS_DIR, f"{label}.json")
        if os.path.exists(path):
            with open(path, 'r') as f:
                data[label] = json.load(f)
        else:
            print(f"Warning: Result file not found for {label} at {path}")
    return data

def plot_accuracy_convergence(data):
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    
    for label, history in data.items():
        steps = [h['step'] for h in history]
        acc = [h['test_accuracy'] * 100.0 for h in history]
        
        # Plot with markers every 10 steps to keep it clean
        ax.plot(steps, acc, label=LABEL_MAP[label], color=COLOR_MAP[label], 
                marker=MARKER_MAP[label], markevery=10, ls='-' if 'DAFL' in label else '--')
        
    ax.set_xlabel("Simulation Step (Time)")
    ax.set_ylabel("Global Test Accuracy (%)")
    ax.set_title("Global AI Model Accuracy Convergence")
    ax.set_xlim(0, len(steps)-1 if len(data) > 0 else 100)
    ax.set_ylim(20, 100)
    ax.legend(loc='lower right', framealpha=0.9)
    
    out_pdf = os.path.join(FIGURES_DIR, "accuracy_convergence.pdf")
    out_png = os.path.join(FIGURES_DIR, "accuracy_convergence.png")
    fig.savefig(out_pdf)
    fig.savefig(out_png)
    plt.close(fig)
    print(f"Saved: {out_pdf} and {out_png}")

def plot_battery_profile(data):
    """
    Plots the battery level of Satellite 3 (which orbits Tharsis volcanic/hydrothermal region)
    comparing DAFL (pruning) vs Asynchronous FL (no pruning).
    """
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    sat_id = "3"  # Sat D
    
    # We want to compare Asynchronous-FL-NoComp vs DAFL-Proposed
    for label in ['Asynchronous-FL-NoComp', 'DAFL-Proposed']:
        if label not in data:
            continue
            
        history = data[label]
        steps = [h['step'] for h in history]
        battery = [h['satellites'][sat_id]['battery_pct'] for h in history]
        mode = [h['satellites'][sat_id]['mode'] for h in history]
        
        ax.plot(steps, battery, label=f"{LABEL_MAP[label]} (Sat D)", color=COLOR_MAP[label], ls='-' if 'DAFL' in label else '--')
        
        # If DAFL, plot pruning state highlights
        if label == 'DAFL-Proposed':
            pruned_steps = [steps[i] for i in range(len(steps)) if mode[i] == 'pruned']
            pruned_batt = [battery[i] for i in range(len(steps)) if mode[i] == 'pruned']
            if pruned_steps:
                ax.scatter(pruned_steps, pruned_batt, color='purple', s=10, zorder=5, label='Energy Pruning Active')
                
            sleep_steps = [steps[i] for i in range(len(steps)) if mode[i] == 'asleep']
            sleep_batt = [battery[i] for i in range(len(steps)) if mode[i] == 'asleep']
            if sleep_steps:
                ax.scatter(sleep_steps, sleep_batt, color='red', s=15, marker='x', zorder=5, label='Safe Mode (Sleep)')
                
    ax.axhline(30.0, color='grey', ls=':', alpha=0.7, label='Pruning Threshold (30%)')
    ax.axhline(10.0, color='red', ls=':', alpha=0.7, label='Safe Mode Threshold (10%)')
    ax.set_xlabel("Simulation Step (Time)")
    ax.set_ylabel("Battery Charge State (%)")
    ax.set_title("SmallSat Battery State-of-Charge Dynamics")
    ax.set_xlim(0, len(steps)-1 if len(data) > 0 else 100)
    ax.set_ylim(0, 105)
    ax.legend(loc='lower left', framealpha=0.9)
    
    out_pdf = os.path.join(FIGURES_DIR, "battery_profile.pdf")
    out_png = os.path.join(FIGURES_DIR, "battery_profile.png")
    fig.savefig(out_pdf)
    fig.savefig(out_png)
    plt.close(fig)
    print(f"Saved: {out_pdf} and {out_png}")

def plot_dtn_queue(data):
    """
    Plots the transmit queue size of Satellite 1 (Sat B) over time,
    illustrating occlusion bundling and burst transmissions.
    """
    if 'DAFL-Proposed' not in data:
        return
        
    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    history = data['DAFL-Proposed']
    sat_id = "1"
    
    steps = [h['step'] for h in history]
    queue_sizes = [h['satellites'][sat_id]['queue_size'] for h in history]
    visibility = [h['satellites'][sat_id]['is_visible'] for h in history]
    
    # Plot queue size
    ax.plot(steps, queue_sizes, color='teal', label='DTN Queue Size')
    
    # Highlight occlusion regions (where visibility is False)
    # We can plot shaded regions
    start_occl = None
    for i in range(len(steps)):
        if not visibility[i] and start_occl is None:
            start_occl = steps[i]
        elif visibility[i] and start_occl is not None:
            ax.axvspan(start_occl, steps[i], color='gray', alpha=0.15, label='Orbital Occlusion' if 'Orbital Occlusion' not in ax.get_legend_handles_labels()[1] else "")
            start_occl = None
            
    if start_occl is not None:
        ax.axvspan(start_occl, steps[-1], color='gray', alpha=0.15)
        
    ax.set_xlabel("Simulation Step (Time)")
    ax.set_ylabel("Bundles in Queue")
    ax.set_title("DTN Custody Queue Dynamics under Intermittent Links")
    ax.set_xlim(0, len(steps)-1)
    ax.set_ylim(0, max(queue_sizes) + 1)
    ax.legend(loc='upper right', framealpha=0.9)
    
    out_pdf = os.path.join(FIGURES_DIR, "dtn_queue.pdf")
    out_png = os.path.join(FIGURES_DIR, "dtn_queue.png")
    fig.savefig(out_pdf)
    fig.savefig(out_png)
    plt.close(fig)
    print(f"Saved: {out_pdf} and {out_png}")

def plot_staleness_function():
    """
    Plots the mathematical staleness compensation factor as a function of delay.
    """
    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    delays = np.arange(0, DTN_MAX_DELAY + 2)
    factors = (1.0 + delays) ** (-STALENESS_BETA)
    
    ax.plot(delays, factors, color='purple', marker='*')
    ax.set_xlabel(r"Weight Staleness / Delay $\tau$ (steps)")
    ax.set_ylabel(r"Aggregation Discount Factor $\alpha(\tau)$")
    ax.set_title("Stochastic Staleness Compensation")
    ax.set_xlim(0, DTN_MAX_DELAY)
    ax.set_ylim(0, 1.1)
    
    out_pdf = os.path.join(FIGURES_DIR, "staleness_discount.pdf")
    out_png = os.path.join(FIGURES_DIR, "staleness_discount.png")
    fig.savefig(out_pdf)
    fig.savefig(out_png)
    plt.close(fig)
    print(f"Saved: {out_pdf} and {out_png}")

def print_latex_table(data):
    """
    Generates and prints a LaTeX table summarizing the performance of all schemes.
    """
    rows = []
    
    for label in EXPERIMENTS:
        name = label['label']
        if name not in data:
            continue
            
        history = data[name]
        final_step = history[-1]
        
        accuracy = final_step['test_accuracy'] * 100.0
        updates_received = final_step['global_updates_received']
        dropped = final_step['stale_updates_dropped']
        aggregated = final_step['updates_aggregated']
        
        # Calculate final average battery of all satellites
        batteries = [final_step['satellites'][str(i)]['battery_pct'] for i in range(5)]
        avg_battery = np.mean(batteries)
        
        # Count total safe mode triggers / sleeping states overall steps
        sleep_steps_total = sum([
            sum([1 for i in range(5) if h['satellites'][str(i)]['is_sleeping']])
            for h in history
        ])
        
        rows.append((
            LABEL_MAP[name],
            f"{accuracy:.2f}\\%",
            f"{updates_received}",
            f"{aggregated}",
            f"{dropped}",
            f"{avg_battery:.1f}\\%",
            f"{sleep_steps_total}"
        ))
        
    print("\n" + "%"*60)
    print("% LaTeX Results Table for Manuscript")
    print("%"*60)
    print(r"\begin{table*}[t]")
    print(r"\centering")
    print(r"\caption{Performance Comparison of Federated Learning Frameworks over Intermittent Space Networks}")
    print(r"\label{tab:fl_comparison}")
    print(r"\begin{tabular}{lcccccc}")
    print(r"\toprule")
    print(r"Framework & Final Accuracy & Rx Updates & Aggregated Updates & Dropped Updates & Final Avg Battery & Total Sleep Steps \\")
    print(r"\midrule")
    for row in rows:
        print(" & ".join(row) + r" \\")
    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\end{table*}")
    print("%"*60 + "\n")

def main():
    print("Loading simulation results...")
    data = load_results()
    if not data:
        print("Error: No results found in results/. Run the simulation runner first!")
        return
        
    print("Generating figures...")
    plot_accuracy_convergence(data)
    plot_battery_profile(data)
    plot_dtn_queue(data)
    plot_staleness_function()
    
    print_latex_table(data)
    print("Analysis and plotting complete.")

if __name__ == '__main__':
    main()
