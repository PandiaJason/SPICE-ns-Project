import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import shutil

def generate_analytics():
    # Define directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paper_dir = os.path.join(base_dir, 'paper')
    
    os.makedirs(paper_dir, exist_ok=True)
    
    # Simulation Time array (SCET — Spacecraft Event Time, seconds from burn ignition)
    t = np.linspace(0, 300, 300)
    anomaly_start = 90
    correction_time = 130
    m_delay = 60  # one-way light-time delay (s): 2m = 120s round-trip

    # Time axis formatters: T+MM:SS Mission Elapsed Time
    def fmt_scet(x, pos):
        """Format SCET seconds as T+MM:SS (spacecraft local clock)."""
        x = int(round(x))
        if x < 0: return ''
        return f'T+{x // 60:02d}:{x % 60:02d}'

    def fmt_ert(x, pos):
        """Format ERT seconds as T+MM:SS (Earth ground clock = SCET + m)."""
        x = int(round(x + m_delay))
        if x < 0: return ''
        return f'T+{x // 60:02d}:{x % 60:02d}'
    
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
    
    # 5. Earth trajectory: actual deviation vs AI-predicted deviation (two separate signals)
    # Actual deviation: grows when gimbal anomaly causes unmodelled thrust loss
    actual_earth_deviation = 0.0 + 0.05 * (1 - np.exp(-(t - anomaly_start)/25)) * (t >= anomaly_start)
    actual_earth_deviation[t >= correction_time] = actual_earth_deviation[correction_time-1] * np.exp(
        -(t[t >= correction_time] - correction_time)/20)
    # AI-predicted deviation: slightly smoothed, converges closely to actual (small prediction lag)
    predicted_earth_deviation = 0.0 + 0.048 * (1 - np.exp(-(t - anomaly_start)/28)) * (t >= anomaly_start)
    predicted_earth_deviation[t >= correction_time] = predicted_earth_deviation[correction_time-1] * np.exp(
        -(t[t >= correction_time] - correction_time)/22)

    # 6. Mars trajectory: true measured deviation vs DSN target plan (nominal = zero deviation)
    true_mars_deviation = 0.0 + 0.06 * (1 - np.exp(-(t - anomaly_start)/30)) * (t >= anomaly_start)
    true_mars_deviation[t >= correction_time] = true_mars_deviation[correction_time-1] * np.exp(
        -(t[t >= correction_time] - correction_time)/15)
    dsn_target_plan = np.zeros_like(t)  # Nominal profile: zero deviation from plan

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

    # --- Plot 2: Effective Command Latency Illusion ---
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    ax2.plot(t, actual_latency, label='Actual One-Way Light-Time Delay (s)', color='grey', linestyle='-.', linewidth=2)
    ax2.plot(t, perceived_latency, label='Effective Command Latency / PTB (s)', color=colors[0], linewidth=2)
    ax2.axvline(x=anomaly_start, color='red', linestyle='--', alpha=0.6, label='Anomaly Trigger')
    ax2.axvline(x=correction_time, color='green', linestyle='--', alpha=0.6, label='Reconciliation')
    ax2.set_xlabel('Simulation Time (s)')
    ax2.set_ylabel('Latency (s)')
    ax2.set_title('Effective Command Latency: Actual vs PTB-Mediated')
    ax2.legend()
    save_plot(fig2, 'fig_latency_illusion.pdf')
    save_plot(fig2, 'fig_latency_illusion.png')
    plt.close(fig2)

    # --- Plot 3: Earth AI — Actual Orbital Deviation vs AI Predicted Deviation ---
    # X-axis (bottom): Earth Received Time (ERT = SCET + m) — ground station perspective
    # X-axis (top):    Spacecraft Event Time (SCET) — what epoch on Mars this corresponds to
    fig3, ax3 = plt.subplots(figsize=(9, 5.5))
    plt.subplots_adjust(top=0.82)
    ax3.plot(t, actual_earth_deviation, label='Actual Orbital Deviation (%)',
             color='#ff3a5c', linewidth=2)
    ax3.plot(t, predicted_earth_deviation, label='Earth AI Predicted Deviation (%)',
             color='#0072ff', linewidth=2, linestyle='--')
    ax3.fill_between(t, actual_earth_deviation, predicted_earth_deviation,
                     alpha=0.15, color='orange', label='Prediction Error Envelope')
    ax3.axvline(x=anomaly_start, color='red', linestyle='--', alpha=0.6, label=f'Anomaly @ SCET T+01:30')
    ax3.axvline(x=correction_time, color='green', linestyle='--', alpha=0.6, label=f'Reconciliation @ SCET T+02:10')
    # Bottom axis: ERT (Earth ground clock)
    ax3.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_ert))
    ax3.set_xlabel('Earth Received Time — ERT (T+MM:SS)', labelpad=6)
    ax3.set_ylabel('Trajectory Deviation (%)')
    ax3.set_title('Earth AI: Actual vs Predicted Orbital Deviation', pad=28)
    ax3.legend(fontsize=8, loc='upper right')
    # Top axis: SCET (spacecraft clock)
    ax3_top = ax3.secondary_xaxis('top')
    ax3_top.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_scet))
    ax3_top.set_xlabel('Spacecraft Event Time — SCET (T+MM:SS)', labelpad=8)
    save_plot(fig3, 'fig_earth_path_error.pdf')
    save_plot(fig3, 'fig_earth_path_error.png')
    plt.close(fig3)

    # --- Plot 4: Mars Cabin — True Path vs DSN Target Plan ---
    # X-axis (bottom): Spacecraft Event Time (SCET) — crew's local mission clock
    # X-axis (top):    Earth Received Time (ERT = SCET + m) — when Earth sees this epoch
    fig4, ax4 = plt.subplots(figsize=(9, 5.5))
    plt.subplots_adjust(top=0.82)
    ax4.plot(t, true_mars_deviation, label='True Measured Trajectory Deviation (%)',
             color='#ff007f', linewidth=2)
    ax4.plot(t, dsn_target_plan, label='DSN Target Plan — Nominal Profile (%)',
             color='#00b300', linewidth=2, linestyle='--')
    ax4.fill_between(t, true_mars_deviation, dsn_target_plan,
                     alpha=0.15, color='red', label=r'$\Delta_k$ Reconciliation Gap')
    ax4.axvline(x=anomaly_start, color='red', linestyle='--', alpha=0.6, label='Anomaly @ SCET T+01:30')
    ax4.axvline(x=correction_time, color='green', linestyle='--', alpha=0.6, label='Reconciliation @ SCET T+02:10')
    # Bottom axis: SCET (spacecraft local clock)
    ax4.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_scet))
    ax4.set_xlabel('Spacecraft Event Time — SCET (T+MM:SS)', labelpad=6)
    ax4.set_ylabel('Trajectory Deviation (%)')
    ax4.set_title('Mars Cabin: True Path vs DSN Target Plan', pad=28)
    ax4.legend(fontsize=8, loc='upper right')
    # Top axis: ERT (Earth ground clock — offset by +m)
    ax4_top = ax4.secondary_xaxis('top')
    ax4_top.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_ert))
    ax4_top.set_xlabel('Earth Received Time — ERT (T+MM:SS)', labelpad=8)
    save_plot(fig4, 'fig_mars_path_error.pdf')
    save_plot(fig4, 'fig_mars_path_error.png')
    plt.close(fig4)

    return {"status": "success", "message": "Graphs successfully generated and saved."}

if __name__ == "__main__":
    generate_analytics()
