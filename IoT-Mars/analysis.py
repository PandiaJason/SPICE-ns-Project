import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

# Ensure results directory exists
os.makedirs("results", exist_ok=True)

# Centralized Configurations
from config import *


def plot_pdr_vs_density():
    print("Plotting PDR vs Node Density...")
    df = pd.read_csv("results/pdr_summary.csv")
    nodes = df['Nodes']
    eb = dict(capsize=3, capthick=1, elinewidth=1)

    fig, ax = plt.subplots(figsize=(10, 8.5), dpi=300)
    ax.errorbar(nodes, df['Earth PDR (%)'],                 yerr=df['Earth PDR CI'],                 fmt='o-', color='#1a5f7a', label='Earth (868M, Clear)',              linewidth=2.5, **eb)
    ax.errorbar(nodes, df['Mars Surf Clear PDR (%)'],       yerr=df['Mars Surf Clear PDR CI'],       fmt='s--',color='#e67e22', label='Mars Surf (868M, Clear)',           linewidth=2,   **eb)
    ax.errorbar(nodes, df['Mars Surf Dust PDR (%)'],        yerr=df['Mars Surf Dust PDR CI'],        fmt='x-.',color='#d35400', label='Mars Surf (868M, Dust)',            linewidth=2,   **eb)
    ax.errorbar(nodes, df['Mars Sat Clear PDR (%)'],        yerr=df['Mars Sat Clear PDR CI'],        fmt='d-', color='#2ecc71', label='Mars Sat (868M, Clear)',             linewidth=2.5, **eb)
    ax.errorbar(nodes, df['Mars Sat Dust PDR (%)'],         yerr=df['Mars Sat Dust PDR CI'],         fmt='^-', color='#27ae60', label='Mars Sat (868M, Dust)',              linewidth=2.5, **eb)
    ax.errorbar(nodes, df['Mars Prop Surf Clear PDR (%)'],  yerr=df['Mars Prop Surf Clear PDR CI'],  fmt='H--',color='#c0392b', label='Prop. Surf (433M, Clear)',          linewidth=2.3, **eb)
    ax.errorbar(nodes, df['Mars Prop Surf Dust PDR (%)'],   yerr=df['Mars Prop Surf Dust PDR CI'],   fmt='D-.',color='#922b21', label='Prop. Surf (433M, Dust)',           linewidth=2.3, **eb)
    ax.errorbar(nodes, df['Mars Prop Clear PDR (%)'],       yerr=df['Mars Prop Clear PDR CI'],       fmt='*-', color='#9b59b6', label='Prop. Sat (433M, Clear)',           linewidth=2.8, **eb)
    ax.errorbar(nodes, df['Mars Prop Dust PDR (%)'],        yerr=df['Mars Prop Dust PDR CI'],        fmt='p-', color='#8e44ad', label='Prop. Sat (433M, Dust)',            linewidth=2.8, **eb)

    ax.set_title("Packet Delivery Ratio (PDR) vs. Network Node Density\n(Mean \u00b1 95% CI, 30 Paired Monte Carlo Runs)", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Number of Network Nodes", fontsize=13, fontweight='bold')
    ax.set_ylabel("Packet Delivery Ratio (PDR, %)", fontsize=13, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_ylim(-5, 105)
    leg = ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.18), frameon=True,
                    framealpha=0, ncol=3, fontsize=12)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.25)
    fig.savefig("results/pdr_vs_density.png")
    plt.close(fig)
    print("Saved results/pdr_vs_density.png")


def plot_energy_vs_density():
    print("Plotting Energy vs Node Density...")
    df = pd.read_csv("results/pdr_summary.csv")
    nodes = df['Nodes']
    eb = dict(capsize=3, capthick=1, elinewidth=1)

    fig, ax = plt.subplots(figsize=(10, 8.5), dpi=300)
    ax.errorbar(nodes, df['Earth Energy (J)'],                  yerr=df['Earth Energy CI'],                  fmt='o-', color='#1a5f7a', label='Earth (868M, Clear)',         linewidth=2.5, **eb)
    ax.errorbar(nodes, df['Mars Surf Clear Energy (J)'],        yerr=df['Mars Surf Clear Energy CI'],        fmt='s--',color='#e67e22', label='Mars Surf (868M, Clear)',      linewidth=2,   **eb)
    ax.errorbar(nodes, df['Mars Surf Dust Energy (J)'],         yerr=df['Mars Surf Dust Energy CI'],         fmt='x-.',color='#d35400', label='Mars Surf (868M, Dust)',       linewidth=2,   **eb)
    ax.errorbar(nodes, df['Mars Sat Clear Energy (J)'],         yerr=df['Mars Sat Clear Energy CI'],         fmt='d-', color='#2ecc71', label='Mars Sat (868M, Clear)',       linewidth=2.5, **eb)
    ax.errorbar(nodes, df['Mars Sat Dust Energy (J)'],          yerr=df['Mars Sat Dust Energy CI'],          fmt='^-', color='#27ae60', label='Mars Sat (868M, Dust)',        linewidth=2.5, **eb)
    ax.errorbar(nodes, df['Mars Prop Surf Clear Energy (J)'],   yerr=df['Mars Prop Surf Clear Energy CI'],   fmt='H--',color='#c0392b', label='Prop. Surf (433M, Clear)',     linewidth=2.3, **eb)
    ax.errorbar(nodes, df['Mars Prop Surf Dust Energy (J)'],    yerr=df['Mars Prop Surf Dust Energy CI'],    fmt='D-.',color='#922b21', label='Prop. Surf (433M, Dust)',      linewidth=2.3, **eb)
    ax.errorbar(nodes, df['Mars Prop Clear Energy (J)'],        yerr=df['Mars Prop Clear Energy CI'],        fmt='*-', color='#9b59b6', label='Prop. Sat (433M, Clear)',      linewidth=2.8, **eb)
    ax.errorbar(nodes, df['Mars Prop Dust Energy (J)'],         yerr=df['Mars Prop Dust Energy CI'],         fmt='p-', color='#8e44ad', label='Prop. Sat (433M, Dust)',       linewidth=2.8, **eb)

    ax.set_title("Energy Efficiency vs. Network Node Density\n(Mean \u00b1 95% CI, 30 Paired Monte Carlo Runs)", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Number of Network Nodes", fontsize=13, fontweight='bold')
    ax.set_ylabel("Avg. Energy Consumed per Successful Packet (Joules)", fontsize=13, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_yscale('log')
    leg = ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.18), frameon=True,
                    framealpha=0, ncol=3, fontsize=12)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.25)
    fig.savefig("results/energy_vs_density.png")
    plt.close(fig)
    print("Saved results/energy_vs_density.png")


def plot_pdr_vs_distance():
    print("Plotting PDR vs Coverage Radius...")
    df = pd.read_csv("results/pdr_vs_distance.csv")
    dist = df['Distance_km']
    eb = dict(capsize=3, capthick=1, elinewidth=1)

    fig, ax = plt.subplots(figsize=(10, 8.5), dpi=300)
    ax.errorbar(dist, df['Earth_PDR'],                yerr=df['Earth_PDR_CI'],                fmt='o-', color='#1a5f7a', label='Earth (868M, Clear)',         linewidth=2.5, **eb)
    ax.errorbar(dist, df['Mars_Surf_Clear_PDR'],      yerr=df['Mars_Surf_Clear_PDR_CI'],      fmt='s--',color='#e67e22', label='Mars Surf (868M, Clear)',      linewidth=2,   **eb)
    ax.errorbar(dist, df['Mars_Surf_Dust_PDR'],       yerr=df['Mars_Surf_Dust_PDR_CI'],       fmt='x-.',color='#d35400', label='Mars Surf (868M, Dust)',       linewidth=2,   **eb)
    ax.errorbar(dist, df['Mars_Sat_Clear_PDR'],       yerr=df['Mars_Sat_Clear_PDR_CI'],       fmt='d-', color='#2ecc71', label='Mars Sat (868M, Clear)',       linewidth=2.5, **eb)
    ax.errorbar(dist, df['Mars_Sat_Dust_PDR'],        yerr=df['Mars_Sat_Dust_PDR_CI'],        fmt='^-', color='#27ae60', label='Mars Sat (868M, Dust)',        linewidth=2.5, **eb)
    ax.errorbar(dist, df['Mars_Prop_Surf_Clear_PDR'], yerr=df['Mars_Prop_Surf_Clear_PDR_CI'], fmt='H--',color='#c0392b', label='Prop. Surf (433M, Clear)',     linewidth=2.3, **eb)
    ax.errorbar(dist, df['Mars_Prop_Surf_Dust_PDR'],  yerr=df['Mars_Prop_Surf_Dust_PDR_CI'],  fmt='D-.',color='#922b21', label='Prop. Surf (433M, Dust)',      linewidth=2.3, **eb)
    ax.errorbar(dist, df['Mars_Prop_Clear_PDR'],      yerr=df['Mars_Prop_Clear_PDR_CI'],      fmt='*-', color='#9b59b6', label='Prop. Sat (433M, Clear)',      linewidth=2.8, **eb)
    ax.errorbar(dist, df['Mars_Prop_Dust_PDR'],       yerr=df['Mars_Prop_Dust_PDR_CI'],       fmt='p-', color='#8e44ad', label='Prop. Sat (433M, Dust)',       linewidth=2.8, **eb)

    ax.set_title("PDR vs. Maximum Node Distance from Gateway\n(Mean \u00b1 95% CI, 30 Paired Monte Carlo Runs)", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Gateway Coverage Radius (km)", fontsize=13, fontweight='bold')
    ax.set_ylabel("Packet Delivery Ratio (PDR, %)", fontsize=13, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_ylim(-5, 105)
    leg = ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.18), frameon=True,
                    framealpha=0, ncol=3, fontsize=12)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.25)
    fig.savefig("results/pdr_vs_distance.png")
    plt.close(fig)
    print("Saved results/pdr_vs_distance.png")


def plot_diurnal_performance():
    print("Plotting Diurnal Performance...")
    df = pd.read_csv("results/diurnal_performance.csv")
    hours = df['Sol_Hour']

    fig, ax1 = plt.subplots(figsize=(10, 8.5), dpi=300)

    ax1.set_xlabel('Martian Sol Time (Hours)', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Packet Delivery Ratio (PDR, %)', color='#333333', fontsize=13, fontweight='bold')
    line1 = ax1.plot(hours, df['Surf_Clear_PDR'], 's--', color='#e67e22', label='Mars Surf (868M, Clear)', linewidth=2)
    line2 = ax1.plot(hours, df['Surf_Dust_PDR'], 'x-.', color='#d35400', label='Mars Surf (868M, Dust)', linewidth=2)
    line3 = ax1.plot(hours, df['Sat_Clear_PDR'], 'd-', color='#2ecc71', label='Mars Sat (868M, Clear)', linewidth=2.5)
    line4 = ax1.plot(hours, df['Sat_Dust_PDR'], '^-', color='#27ae60', label='Mars Sat (868M, Dust)', linewidth=2.5)
    line_pc = ax1.plot(hours, df['Prop_Clear_PDR'], '*-', color='#9b59b6', label='Prop. Sat (433M, Clear)', linewidth=2.8)
    line_pd = ax1.plot(hours, df['Prop_Dust_PDR'], 'p-', color='#8e44ad', label='Prop. Sat (433M, Dust)', linewidth=2.8)
    ax1.tick_params(axis='y', labelcolor='#333333')
    ax1.set_ylim(-5, 105)

    ax2 = ax1.twinx()
    color_temp = '#2980b9'
    ax2.set_ylabel('Martian Atmosphere Temperature (K)', color=color_temp, fontsize=13, fontweight='bold')
    line5 = ax2.plot(hours, df['Temperature_K'], 'o-', color=color_temp, alpha=0.3, label='Temp (K)', linewidth=1.5)
    ax2.tick_params(axis='y', labelcolor=color_temp)

    lines = line1 + line2 + line3 + line4 + line_pc + line_pd + line5
    labels = [l.get_label() for l in lines]
    leg = ax1.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.14),
                     ncol=3, frameon=True, framealpha=0, fontsize=12)

    ax1.set_title("Diurnal Martian LoRaWAN Performance vs. Thermal Extremes", fontsize=14, fontweight='bold', pad=15)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.22)
    fig.savefig("results/diurnal_performance.png")
    plt.close(fig)
    print("Saved results/diurnal_performance.png")


def plot_link_budget():
    print("Plotting Link Budget...")
    df = pd.read_csv("results/link_budget_analysis.csv")
    dist_km = df['Distance_m'] / 1000

    noise_earth = -174 + 10*np.log10(125e3) + 6.0
    boltzmann = 1.38e-23
    noise_mars_hot = 10*np.log10(boltzmann * 280 * 1000) + 10*np.log10(125e3) + 7.0
    noise_prop = 10*np.log10(boltzmann * 280 * 1000) + 10*np.log10(125e3) + PROPOSED_NOISE_FIGURE

    rx_threshold_sf7_earth  = noise_earth    + SF_THRESHOLDS[7]
    rx_threshold_sf12_earth = noise_earth    + SF_THRESHOLDS[12]
    rx_threshold_sf12_mars  = noise_mars_hot + SF_THRESHOLDS[12]
    rx_threshold_sf12_prop  = noise_prop     + SF_THRESHOLDS[12] - PROPOSED_THRESHOLD_BOOST

    fig, ax = plt.subplots(figsize=(10, 8.5), dpi=300)
    ax.plot(dist_km, df['RX_Earth'],          '-',  color='#1a5f7a', label='Earth RX (868M, Clear)', linewidth=2.5)
    ax.plot(dist_km, df['RX_Mars_Clear'],     '--', color='#e67e22', label='Mars Surf RX (868M, Clear)', linewidth=2)
    ax.plot(dist_km, df['RX_Mars_Dust'],      '-.', color='#d35400', label='Mars Surf RX (868M, Dust)', linewidth=2)
    ax.plot(dist_km, df['RX_Mars_Sat_Clear'], ':',  color='#2ecc71', label='Mars Sat RX (868M, Clear)', linewidth=2.5)
    ax.plot(dist_km, df['RX_Mars_Sat_Dust'],  ':',  color='#27ae60', label='Mars Sat RX (868M, Dust)', linewidth=2.5)
    ax.plot(dist_km, df['RX_Prop_Clear'],     '-',  color='#9b59b6', label='Prop. Sat RX (433M, Clear)', linewidth=2.8)
    ax.plot(dist_km, df['RX_Prop_Dust'],      '--', color='#8e44ad', label='Prop. Sat RX (433M, Dust)', linewidth=2.8)

    ax.axhline(rx_threshold_sf7_earth,  color='#7f8c8d', linestyle=':',  label='Earth SF7 Limit (868M)')
    ax.axhline(rx_threshold_sf12_earth, color='#2c3e50', linestyle='--', label='Earth SF12 Limit (868M)')
    ax.axhline(rx_threshold_sf12_mars,  color='#e74c3c', linestyle='-.', label='Mars SF12 Limit (868M)')
    ax.axhline(rx_threshold_sf12_prop,  color='#8e44ad', linestyle='-.', label='Prop. SF12 Limit (433M)')

    ax.set_title("Physical Layer Link Budget: Received Power vs. Distance", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Horizontal Distance to Gateway (km)", fontsize=13, fontweight='bold')
    ax.set_ylabel("Received Signal Power (dBm)", fontsize=13, fontweight='bold')
    ax.set_xscale('log')
    ax.grid(True, which="both", linestyle=':', alpha=0.6)
    ax.set_ylim(-155, -45)
    ax.set_xlim(0.01, 35)
    leg = ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.18), frameon=True,
                    framealpha=0, ncol=3, fontsize=12)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.25)
    fig.savefig("results/link_budget_analysis.png")
    plt.close(fig)
    print("Saved results/link_budget_analysis.png")


if __name__ == "__main__":
    print("====================================================")
    print("STARTING MARTIAN LORAWAN DATA ANALYSIS & PLOTTING")
    print("====================================================")

    plot_pdr_vs_density()
    plot_energy_vs_density()
    plot_pdr_vs_distance()
    plot_diurnal_performance()
    plot_link_budget()

    # Automatically copy the generated plots to the paper's figures directory
    import shutil
    paper_fig_dir = os.path.join("paper", "figures")
    os.makedirs(paper_fig_dir, exist_ok=True)
    print("Copying generated plots to paper/figures/ directory...")
    for filename in os.listdir("results"):
        if filename.endswith(".png"):
            shutil.copy(os.path.join("results", filename), os.path.join(paper_fig_dir, filename))
    print("Successfully copied all figures to paper/figures/!")

    print("====================================================")
    print("DATA ANALYSIS & PLOTS COMPLETED successfully.")
    print("====================================================")
