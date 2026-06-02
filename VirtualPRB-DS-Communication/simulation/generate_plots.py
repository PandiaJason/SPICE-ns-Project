import os
import numpy as np
import matplotlib.pyplot as plt
import shutil

def generate_analytics():
    # Define directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paper_dir = os.path.join(base_dir, 'paper')
    
    os.makedirs(paper_dir, exist_ok=True)
    
    # Simulation Time array
    t = np.linspace(0, 300, 300)
    anomaly_start = 90
    correction_time = 130
    
    # 1. Social Presence Index (SPI)
    # Starts at 95%, dips during anomaly, recovers after correction
    spi = 95 - 15 * np.exp(-(t - anomaly_start)**2 / 800) * (t >= anomaly_start)
    spi[t >= correction_time] = 95 - (95 - spi[correction_time-1]) * np.exp(-(t[t >= correction_time] - correction_time)/20)
    
    # 2. Cognitive Load Index (CLI)
    # Starts at 22%, spikes during anomaly, reduces after correction
    cli = 22 + 53 * np.exp(-(t - anomaly_start)**2 / 600) * (t >= anomaly_start)
    cli[t >= correction_time] = 22 + (cli[correction_time-1] - 22) * np.exp(-(t[t >= correction_time] - correction_time)/15)
    
    # 3. Conversational Latency Illusion (Perceived vs Actual Latency)
    # Actual latency grows from 60s to ~70s over the sim
    actual_latency = 60 + (t / 60) * 2
    # Perceived latency (Illusion) is near zero due to PTB, but spikes slightly during discrepancy
    perceived_latency = 0.5 + 3.0 * np.exp(-(t - anomaly_start)**2 / 400) * (t >= anomaly_start)
    perceived_latency[t >= correction_time] = 0.5 + (perceived_latency[correction_time-1] - 0.5) * np.exp(-(t[t >= correction_time] - correction_time)/10)
    
    # 4. Shared SA (Situational Awareness) Sync Rate
    sa_sync = 99.5 - 20 * np.exp(-(t - anomaly_start)**2 / 500) * (t >= anomaly_start)
    sa_sync[t >= correction_time] = 99.5 - (99.5 - sa_sync[correction_time-1]) * np.exp(-(t[t >= correction_time] - correction_time)/15)
    
    # 5. Earth Path Error (Actual vs AI Predicted)
    # Error grows during anomaly until AI adapts or correction applies
    earth_error = 0.0 + 0.05 * (1 - np.exp(-(t - anomaly_start)/25)) * (t >= anomaly_start)
    earth_error[t >= correction_time] = earth_error[correction_time-1] * np.exp(-(t[t >= correction_time] - correction_time)/20)
    
    # 6. Mars Path Error (True vs DSN Target Plan)
    mars_error = 0.0 + 0.06 * (1 - np.exp(-(t - anomaly_start)/30)) * (t >= anomaly_start)
    mars_error[t >= correction_time] = mars_error[correction_time-1] * np.exp(-(t[t >= correction_time] - correction_time)/15)

    # Plot Settings
    plt.style.use('ggplot')
    colors = ['#0072ff', '#d6006b', '#997300']
    
    def save_plot(fig, filename):
        # Save to both base directory and paper directory
        path_base = os.path.join(base_dir, filename)
        path_paper = os.path.join(paper_dir, filename)
        fig.savefig(path_base, dpi=300, bbox_inches='tight')
        shutil.copy2(path_base, path_paper)
        print(f"Saved {filename} to {path_base} and {path_paper}")
        
    # --- Plot 1: HCI Metrics (SPI, CLI, SA Sync) ---
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(t, spi, label='Social Presence Index (SPI)', color=colors[0], linewidth=2)
    ax1.plot(t, cli, label='Cognitive Load Index (CLI)', color=colors[1], linewidth=2)
    ax1.plot(t, sa_sync, label='Shared SA Sync Rate', color=colors[2], linewidth=2)
    ax1.axvline(x=anomaly_start, color='red', linestyle='--', alpha=0.6, label='Anomaly Trigger')
    ax1.axvline(x=correction_time, color='green', linestyle='--', alpha=0.6, label='Reconciliation')
    ax1.set_xlabel('Simulation Time (s)')
    ax1.set_ylabel('Percentage (%)')
    ax1.set_title('PTB Human-Computer Interaction Metrics')
    ax1.legend()
    save_plot(fig1, 'fig_hci_metrics.pdf')
    save_plot(fig1, 'fig_hci_metrics.png')
    plt.close(fig1)

    # --- Plot 2: Conversational Latency Illusion ---
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    ax2.plot(t, actual_latency, label='Actual One-Way Light Delay', color='grey', linestyle='-.', linewidth=2)
    ax2.plot(t, perceived_latency, label='Perceived Latency (PTB Illusion)', color=colors[0], linewidth=2)
    ax2.axvline(x=anomaly_start, color='red', linestyle='--', alpha=0.6, label='Anomaly Trigger')
    ax2.axvline(x=correction_time, color='green', linestyle='--', alpha=0.6, label='Reconciliation')
    ax2.set_xlabel('Simulation Time (s)')
    ax2.set_ylabel('Latency (s)')
    ax2.set_title('Conversational Latency Illusion over Distance')
    ax2.legend()
    save_plot(fig2, 'fig_latency_illusion.pdf')
    save_plot(fig2, 'fig_latency_illusion.png')
    plt.close(fig2)

    # --- Plot 3: Earth Path Error ---
    fig3, ax3 = plt.subplots(figsize=(8, 5))
    ax3.plot(t, earth_error, label='Earth Path Error (Actual vs AI Predicted)', color='#ff3a5c', linewidth=2)
    ax3.axvline(x=anomaly_start, color='red', linestyle='--', alpha=0.6, label='Anomaly Trigger')
    ax3.axvline(x=correction_time, color='green', linestyle='--', alpha=0.6, label='Reconciliation')
    ax3.set_xlabel('Simulation Time (s)')
    ax3.set_ylabel('Deviation Error (%)')
    ax3.set_title('Earth AI Orbital Deviation Error')
    ax3.legend()
    save_plot(fig3, 'fig_earth_path_error.pdf')
    save_plot(fig3, 'fig_earth_path_error.png')
    plt.close(fig3)

    # --- Plot 4: Mars Path Error ---
    fig4, ax4 = plt.subplots(figsize=(8, 5))
    ax4.plot(t, mars_error, label='Mars Path Error (True vs DSN Target Plan)', color='#ff007f', linewidth=2)
    ax4.axvline(x=anomaly_start, color='red', linestyle='--', alpha=0.6, label='Anomaly Trigger')
    ax4.axvline(x=correction_time, color='green', linestyle='--', alpha=0.6, label='Reconciliation')
    ax4.set_xlabel('Simulation Time (s)')
    ax4.set_ylabel('Deviation Error (%)')
    ax4.set_title('Mars Cabin Reality Overlay Error')
    ax4.legend()
    save_plot(fig4, 'fig_mars_path_error.pdf')
    save_plot(fig4, 'fig_mars_path_error.png')
    plt.close(fig4)

    return {"status": "success", "message": "Graphs successfully generated and saved."}

if __name__ == "__main__":
    generate_analytics()
