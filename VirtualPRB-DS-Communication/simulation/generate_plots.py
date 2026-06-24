import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import shutil
import random
import math

# Set random seeds for reproducible stochastic curves
random.seed(42)
np.random.seed(42)

# --- Simulation Physics Constants ---
ANOMALY_T = 90.0
SIM_END_T = 300.0

def delay(t):
    return min(60.0 + (t / 60.0) * 2.0, 480.0)

def nominal(t):
    return dict(
        t=t,
        gimbal_port_C=78.0 + 0.04*t + 3.0*math.sin(t/30.0),
        gimbal_stbd_C=76.0 + 0.02*t + 1.5*math.cos(t/45.0),
        thrust_pct=98.5 - 0.01*t,
        traj_dev=0.0,
        anomaly=False,
    )

def inject(base, t, correction_applied_at):
    dt = t - ANOMALY_T
    corrected = (correction_applied_at is not None) and (t >= correction_applied_at)
    decay = math.exp(-(t - correction_applied_at) / 15.0) if corrected else 1.0
    base['gimbal_port_C'] += 12.0 * (1.0 - math.exp(-dt/20.0)) * decay
    base['thrust_pct']    -= 3.2 * (1.0 - math.exp(-dt/25.0)) * decay
    base['traj_dev']      += 0.06 * (1.0 - math.exp(-dt/30.0)) * decay
    base['anomaly']       = decay > 0.05
    return base

def cabin_state(t, correction_applied_at):
    s = nominal(t)
    if t >= ANOMALY_T:
        s = inject(s, t, correction_applied_at)
    return s

def predict(recv, m):
    t_base = recv['t']
    t_pred = t_base + 2.0*m
    p = nominal(t_pred)
    
    if recv.get('anomaly'):
        dt_base = t_base - ANOMALY_T
        dt_pred = t_pred - ANOMALY_T
        
        # Earth AI has model parameter mismatch (10 vs 12, 3.0 vs 3.2, 0.035 vs 0.06)
        delta_temp_base = 10.0 * (1.0 - math.exp(-dt_base / 20.0))
        delta_temp_pred = 10.0 * (1.0 - math.exp(-dt_pred / 20.0))
        temp_change = delta_temp_pred - delta_temp_base
        
        delta_thrust_base = -3.0 * (1.0 - math.exp(-dt_base / 25.0))
        delta_thrust_pred = -3.0 * (1.0 - math.exp(-dt_pred / 25.0))
        thrust_change = delta_thrust_pred - delta_thrust_base
        
        delta_dev_base = 0.035 * (1.0 - math.exp(-dt_base / 30.0))
        delta_dev_pred = 0.035 * (1.0 - math.exp(-dt_pred / 30.0))
        dev_change = delta_dev_pred - delta_dev_base
        
        p['gimbal_port_C'] = recv['gimbal_port_C'] + temp_change
        p['thrust_pct']    = recv['thrust_pct'] + thrust_change
        p['traj_dev']      = recv['traj_dev'] + dev_change
        p['anomaly']       = True
    else:
        p['gimbal_port_C'] = recv['gimbal_port_C'] + 0.04 * (2.0*m)
        p['gimbal_stbd_C'] = recv['gimbal_stbd_C'] + 0.02 * (2.0*m)
        p['thrust_pct']    = recv['thrust_pct'] - 0.01 * (2.0*m)
        p['traj_dev']      = recv['traj_dev']
    p['t'] = t_pred
    return p

def run_simulation(protocol='PTB', corr_time=130.0, noise_factor=1.0, threshold=0.5):
    """
    Runs a discrete time-step simulation of the Mars approach burn.
    Returns lists of physical states, predictions, and human factors metrics.
    """
    t_steps = np.arange(0, 301, 1.0)
    
    # State histories
    history = {
        't': [],
        'm': [],
        'gimbal_port_C': [],
        'thrust_pct': [],
        'traj_dev': [],
        'pred_traj_dev': [],
        'pred_gimbal_port_C': [],
        'opfi': [],
        'ocli': [],
        'ecl': [],
        'ssa': [],
    }
    
    # Human factors states
    ocli = 22.0
    opfi = 96.0
    ecl = 0.4
    ssa = 99.8
    
    correction_applied_at = None
    
    for t in t_steps:
        m = delay(t)
        
        # Decide if correction is applied
        if protocol == 'PTB':
            if t >= corr_time:
                correction_applied_at = corr_time
        elif protocol == 'CONVENTIONAL':
            # Conventional correction is delayed by full round-trip delay 2m from anomaly start (90s)
            conv_delay = 2.0 * delay(ANOMALY_T)  # 120s round-trip
            if t >= (ANOMALY_T + conv_delay):
                correction_applied_at = ANOMALY_T + conv_delay
                
        # Mars true state
        cab = cabin_state(t, correction_applied_at)
        
        # Ground received state from t - 2m (since ground projects forward by 2m targeting t)
        t_tel = max(0, t - 2.0*m)
        recv_clean = cabin_state(t_tel, correction_applied_at)
        recv = dict(recv_clean)
        
        # Add telemetry measurement noise
        if noise_factor > 0:
            if t_tel >= ANOMALY_T:
                recv['gimbal_port_C'] += random.gauss(0, 0.15) * noise_factor
                recv['thrust_pct']    += random.gauss(0, 0.08) * noise_factor
                recv['traj_dev']      += random.gauss(0, 0.001) * noise_factor
            else:
                recv['gimbal_port_C'] += random.gauss(0, 0.05) * noise_factor
                recv['thrust_pct']    += random.gauss(0, 0.04) * noise_factor
                recv['traj_dev']      += random.gauss(0, 0.0002) * noise_factor
                
        # Ground forward prediction targeting time t
        pred = predict(recv, m)
        
        # Reconciliation check
        deltas = {k: cab[k] - pred[k] for k in ('gimbal_port_C', 'thrust_pct', 'traj_dev')}
        max_d = max(abs(v) for v in deltas.values())
        safe = max_d < threshold
        
        # Metrics targets
        if protocol == 'PTB':
            if not safe:
                ocli_target = 75.0
                ecl_target = 2.0 * m
                ssa_target = max(60.0, 99.5 - max_d * 50.0)
                opfi_target = max(65.0, 95.0 - max_d * 30.0)
            elif correction_applied_at is not None:
                ocli_target = 18.0
                ecl_target = 0.5
                ssa_target = 99.9
                opfi_target = 99.0
            else:
                ocli_target = 22.0
                ecl_target = 0.4
                ssa_target = 99.8
                opfi_target = 96.0
        else: # CONVENTIONAL protocol
            if t < ANOMALY_T:
                ocli_target = 22.0
                ecl_target = 0.4
                ssa_target = 99.8
                opfi_target = 96.0
            elif correction_applied_at is None:
                # Anomaly active, lag is unmasked
                ocli_target = 88.0
                ecl_target = 2.0 * m
                ssa_target = 40.0
                opfi_target = 45.0
            else:
                # Post-correction recovery
                ocli_target = 20.0
                ecl_target = 0.5
                ssa_target = 99.5
                opfi_target = 95.0
                
        # Integrate metric state-space filters (dt = 1.0s)
        dt_step = 1.0
        ocli += (ocli_target - ocli) * (1.0 - math.exp(-dt_step / 15.0))
        ecl  += (ecl_target - ecl) * (1.0 - math.exp(-dt_step / 8.0))
        ssa  += (ssa_target - ssa) * (1.0 - math.exp(-dt_step / 10.0))
        opfi += (opfi_target - opfi) * (1.0 - math.exp(-dt_step / 12.0))
        
        # Add stochastic observation noise to metrics
        ocli_noisy = max(10.0, min(100.0, ocli + random.gauss(0, 0.4) * noise_factor))
        opfi_noisy = max(10.0, min(100.0, opfi + random.gauss(0, 0.3) * noise_factor))
        ssa_noisy  = max(10.0, min(100.0, ssa + random.gauss(0, 0.1) * noise_factor))
        ecl_noisy  = max(0.1, min(100.0, ecl + random.gauss(0, 0.02) * noise_factor))
        
        history['t'].append(t)
        history['m'].append(m)
        history['gimbal_port_C'].append(cab['gimbal_port_C'])
        history['thrust_pct'].append(cab['thrust_pct'])
        history['traj_dev'].append(cab['traj_dev'] * 100.0) # convert to %
        history['pred_traj_dev'].append(pred['traj_dev'] * 100.0)
        history['pred_gimbal_port_C'].append(pred['gimbal_port_C'])
        history['opfi'].append(opfi_noisy)
        history['ocli'].append(ocli_noisy)
        history['ecl'].append(ecl_noisy)
        history['ssa'].append(ssa_noisy)
        
    return history


def generate_analytics():
    # Define directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paper_dir = os.path.join(base_dir, 'paper')
    os.makedirs(paper_dir, exist_ok=True)
    
    # Run the simulations
    ptb_data = run_simulation('PTB', corr_time=130.0, noise_factor=1.0)
    conv_data = run_simulation('CONVENTIONAL', noise_factor=1.0)
    
    t = np.array(ptb_data['t'])
    m_delay = 60.0  # reference delay for axis formatter

    # Time axis formatters: T+MM:SS Mission Elapsed Time
    def fmt_scet(x, pos):
        x = int(round(x))
        if x < 0: return ''
        return f'T+{x // 60:02d}:{x % 60:02d}'

    def fmt_ert(x, pos):
        x = int(round(x + m_delay))
        if x < 0: return ''
        return f'T+{x // 60:02d}:{x % 60:02d}'
        
    plt.style.use('ggplot')
    colors = ['#0072ff', '#d6006b', '#997300']
    
    def save_plot(fig, filename):
        path_base = os.path.join(base_dir, filename)
        path_paper = os.path.join(paper_dir, filename)
        fig.savefig(path_base, dpi=300, bbox_inches='tight')
        shutil.copy2(path_base, path_paper)
        
        # Copy to the specific folders where LaTeX projects search for them
        targets = [
            os.path.join(paper_dir, 'els-cas-templates', 'figs', filename),
            os.path.join(paper_dir, 'els-cas-templates', 'upload_sources', 'figs', filename),
            os.path.join(paper_dir, 'w_paper', 'images', filename),
            os.path.join(paper_dir, 'images', filename)
        ]
        for t in targets:
            if os.path.exists(os.path.dirname(t)):
                shutil.copy2(path_base, t)
        print(f"Saved {filename} to {path_base} and propagated to document directories")

    # --- Plot 1: Operational Metrics (OPFI, OCLI, SSA) ---
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(t, ptb_data['opfi'], label='Operator Presence Fidelity Index (OPFI)', color=colors[0], linewidth=2)
    ax1.plot(t, ptb_data['ocli'], label='Operator Cognitive Load Index (OCLI)', color=colors[1], linewidth=2)
    ax1.plot(t, ptb_data['ssa'], label='State Synchronization Accuracy (SSA)', color=colors[2], linewidth=2)
    ax1.axvline(x=ANOMALY_T, color='red', linestyle='--', alpha=0.6, label='Anomaly @ SCET T+01:30')
    ax1.axvline(x=130.0, color='green', linestyle='--', alpha=0.6, label='Reconciliation @ SCET T+02:10')
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_scet))
    ax1.set_xlabel('Spacecraft Event Time — SCET (T+MM:SS)')
    ax1.set_ylabel('Percentage (%)')
    ax1.set_title('PTB Onboard Operational Performance Metrics')
    ax1.legend(fontsize=8)
    save_plot(fig1, 'fig_hci_metrics.pdf')
    save_plot(fig1, 'fig_hci_metrics.png')
    plt.close(fig1)

    # --- Plot 2: Effective Command Latency ---
    fig2, ax2 = plt.subplots(figsize=(9, 5.5))
    plt.subplots_adjust(top=0.82)
    actual_latency = np.array(ptb_data['m'])
    ax2.plot(t, actual_latency, label='Actual One-Way Light-Time Delay — m(t) (s)', color='grey', linestyle='-.', linewidth=2)
    ax2.plot(t, ptb_data['ecl'], label='Effective Command Latency via PTB (s)', color=colors[0], linewidth=2)
    ax2.fill_between(t, actual_latency, ptb_data['ecl'], alpha=0.10, color='blue', label='PTB Latency Masking Envelope')
    ax2.axvline(x=ANOMALY_T, color='red', linestyle='--', alpha=0.6, label='Anomaly @ SCET T+01:30')
    ax2.axvline(x=130.0, color='green', linestyle='--', alpha=0.6, label='Reconciliation @ SCET T+02:10')
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_scet))
    ax2.set_xlabel('Spacecraft Event Time — SCET (T+MM:SS)', labelpad=6)
    ax2.set_ylabel('Latency (s)')
    ax2.set_title('Effective Command Latency: Actual Light-Time vs PTB-Mediated', pad=28)
    ax2.legend(fontsize=8, loc='center right')
    ax2_top = ax2.secondary_xaxis('top')
    ax2_top.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_ert))
    ax2_top.set_xlabel('Earth Received Time — ERT (T+MM:SS)', labelpad=8)
    save_plot(fig2, 'fig_latency_illusion.pdf')
    save_plot(fig2, 'fig_latency_illusion.png')
    plt.close(fig2)

    # --- Plot 3: Earth AI prediction error ---
    fig3, ax3 = plt.subplots(figsize=(9, 5.5))
    plt.subplots_adjust(top=0.82)
    ax3.plot(t, ptb_data['traj_dev'], label='Actual Orbital Deviation (%)', color='#ff3a5c', linewidth=2)
    ax3.plot(t, ptb_data['pred_traj_dev'], label='Earth AI Predicted Deviation (%)', color='#0072ff', linewidth=2, linestyle='--')
    ax3.fill_between(t, ptb_data['traj_dev'], ptb_data['pred_traj_dev'], alpha=0.15, color='orange', label='Prediction Error Envelope')
    ax3.axvline(x=ANOMALY_T, color='red', linestyle='--', alpha=0.6, label='Anomaly @ SCET T+01:30')
    ax3.axvline(x=130.0, color='green', linestyle='--', alpha=0.6, label='Reconciliation @ SCET T+02:10')
    ax3.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_ert))
    ax3.set_xlabel('Earth Received Time — ERT (T+MM:SS)', labelpad=6)
    ax3.set_ylabel('Trajectory Deviation (%)')
    ax3.set_title('Earth AI: Actual vs Predicted Orbital Deviation', pad=28)
    ax3.legend(fontsize=8, loc='upper right')
    ax3_top = ax3.secondary_xaxis('top')
    ax3_top.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_scet))
    ax3_top.set_xlabel('Spacecraft Event Time — SCET (T+MM:SS)', labelpad=8)
    save_plot(fig3, 'fig_earth_path_error.pdf')
    save_plot(fig3, 'fig_earth_path_error.png')
    plt.close(fig3)

    # --- Plot 4: Mars Cabin — True Path vs Plan (PTB vs Conventional) ---
    fig4, ax4 = plt.subplots(figsize=(9, 5.5))
    plt.subplots_adjust(top=0.82)
    ax4.plot(t, ptb_data['traj_dev'], label='True Path Deviation (PTB Protocol) (%)', color='#ff007f', linewidth=2.5)
    ax4.plot(t, conv_data['traj_dev'], label='True Path Deviation (Conventional Reactive) (%)', color='#a3a3a3', linewidth=2, linestyle='-.')
    ax4.plot(t, np.zeros_like(t), label='DSN Target Plan — Nominal (%)', color='#00b300', linewidth=1.5, linestyle='--')
    ax4.axvline(x=ANOMALY_T, color='red', linestyle='--', alpha=0.6, label='Anomaly @ SCET T+01:30')
    ax4.axvline(x=130.0, color='green', linestyle='--', alpha=0.6, label='PTB Intercept @ SCET T+02:10')
    # Conventional correction occurs at 90s + 2m delay (210s)
    ax4.axvline(x=210.0, color='grey', linestyle=':', alpha=0.8, label='Conv Correction @ SCET T+03:30')
    ax4.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_scet))
    ax4.set_xlabel('Spacecraft Event Time — SCET (T+MM:SS)', labelpad=6)
    ax4.set_ylabel('Trajectory Deviation (%)')
    ax4.set_title('Mars Cabin Trajectory Deviation: PTB vs. Conventional', pad=28)
    ax4.legend(fontsize=8, loc='upper right')
    ax4_top = ax4.secondary_xaxis('top')
    ax4_top.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_ert))
    ax4_top.set_xlabel('Earth Received Time — ERT (T+MM:SS)', labelpad=8)
    save_plot(fig4, 'fig_mars_path_error.pdf')
    save_plot(fig4, 'fig_mars_path_error.png')
    plt.close(fig4)

    # --- Plot 5: Delay & Intercept Window Evolution ---
    fig5, ax5 = plt.subplots(figsize=(8, 5))
    ax5.plot(t, actual_latency, label='One-Way Light-Time Delay — m(t) (s)', color=colors[0], linewidth=2)
    ax5.plot(t, 2.0 * actual_latency, label='Round-Trip Delay / Intercept Window — 2m(t) (s)', color=colors[1], linewidth=2, linestyle='--')
    ax5.axvline(x=ANOMALY_T, color='red', linestyle='--', alpha=0.6, label='Anomaly @ SCET T+01:30')
    ax5.axvline(x=130.0, color='green', linestyle='--', alpha=0.6, label='Reconciliation @ SCET T+02:10')
    ax5.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_scet))
    ax5.set_xlabel('Spacecraft Event Time — SCET (T+MM:SS)')
    ax5.set_ylabel('Time Delay (s)')
    ax5.set_title('PTB Delay and Intercept Window Evolution')
    ax5.legend(fontsize=8)
    save_plot(fig5, 'fig_delay_evolution.pdf')
    save_plot(fig5, 'fig_delay_evolution.png')
    plt.close(fig5)

    # --- Plot 6: Prediction Error vs Intercept Horizon (2m) ---
    horizons = np.linspace(10, 600, 50)
    err_temp = []
    err_traj = []
    
    # Dynamic Monte Carlo sweep to find prediction errors for horizons
    for h in horizons:
        m_val = h / 2.0
        # Run 30 trials with noise
        temp_errs = []
        traj_errs = []
        for _ in range(30):
            # Evaluate at anomaly middle point
            t_base = ANOMALY_T + 10.0
            recv = cabin_state(t_base, None)
            # Add random noise
            recv['gimbal_port_C'] += random.gauss(0, 0.15)
            recv['traj_dev']      += random.gauss(0, 0.001)
            pred = predict(recv, m_val)
            true_future = cabin_state(t_base + h, None)
            
            temp_errs.append(abs(true_future['gimbal_port_C'] - pred['gimbal_port_C']))
            traj_errs.append(abs(true_future['traj_dev'] - pred['traj_dev']) * 100.0)
            
        err_temp.append(np.mean(temp_errs))
        err_traj.append(np.mean(traj_errs))

    fig6, ax6_left = plt.subplots(figsize=(8, 5))
    color_temp = colors[1]
    color_traj = colors[0]

    ax6_left.plot(horizons, err_temp, color=color_temp, linewidth=2, label='Gimbal Temp Error (°C)')
    ax6_left.set_xlabel('Intercept Horizon / Round-Trip Delay — 2m (s)')
    ax6_left.set_ylabel('Mean Absolute Temp Error (°C)', color=color_temp)
    ax6_left.tick_params(axis='y', labelcolor=color_temp)

    ax6_right = ax6_left.twinx()
    ax6_right.plot(horizons, err_traj, color=color_traj, linewidth=2, linestyle='--', label='Trajectory Dev Error (%)')
    ax6_right.set_ylabel('Mean Absolute Trajectory Error (%)', color=color_traj)
    ax6_right.tick_params(axis='y', labelcolor=color_traj)
    ax6_right.grid(False)

    lines_l, labels_l = ax6_left.get_legend_handles_labels()
    lines_r, labels_r = ax6_right.get_legend_handles_labels()
    ax6_left.legend(lines_l + lines_r, labels_l + labels_r, loc='upper left', fontsize=8)
    ax6_left.set_title('Prediction Model Error Accumulation vs. Intercept Horizon')
    save_plot(fig6, 'fig_prediction_drift.pdf')
    save_plot(fig6, 'fig_prediction_drift.png')
    plt.close(fig6)

    # --- Plot 7: Final Trajectory insertion Error vs Delay (PTB vs Conventional) ---
    delays = np.logspace(0, 4.7, 100) # 1s to ~50,000s
    err_conv_sweep = []
    err_ptb_sweep = []
    
    T_burn = 1000.0
    for d in delays:
        # PTB: drift accumulates with round-trip delay
        drift = 0.05 * ((d / 1000.0) ** 0.6)
        err_ptb = 0.02 + drift + random.uniform(-0.002, 0.002)
        err_ptb = max(0.005, err_ptb)
        err_ptb_sweep.append(err_ptb)
        
        # Conventional: correction is applied at ANOMALY_T + d
        t_corr = ANOMALY_T + d
        if t_corr <= T_burn:
            peak_dev = 6.0 * (1.0 - math.exp(-d / 300.0))
            err_conv = peak_dev * math.exp(-(T_burn - t_corr) / 15.0)
        else:
            err_conv = 6.0 * (1.0 - math.exp(-(T_burn - ANOMALY_T) / 300.0))
        err_conv += random.uniform(-0.02, 0.02)
        err_conv = max(0.0, err_conv)
        err_conv_sweep.append(err_conv)

    fig7, ax7 = plt.subplots(figsize=(9, 5.5))
    ax7.plot(delays, err_conv_sweep, label='Conventional Reactive Protocol (Unassisted Lag)', color='#d6006b', linewidth=2.5)
    ax7.plot(delays, err_ptb_sweep, label='PTB Protocol (Forward-Projected Intercept)', color='#0072ff', linewidth=2.5)
    ax7.axhline(y=0.5, color='black', linestyle=':', alpha=0.7, label='Safety Threshold (δ_safe = 0.5%)')
    
    # Mission markers
    missions = [
        ('Moon', 2.6, 'grey'),
        ('Mars', 1000.0, '#997300'),
        ('Jupiter', 4000.0, '#555555'),
        ('Saturn', 9000.0, '#a3a3a3'),
        ('Pluto', 32000.0, '#772277')
    ]
    for name, rtt, color in missions:
        ax7.axvline(x=rtt, color=color, linestyle='--', alpha=0.5)
        # Position labels neatly
        y_pos = 1.0 if name == 'Moon' else 3.0
        ax7.text(rtt * 1.15, y_pos, f'{name}\n({rtt}s)', fontsize=8, color=color, weight='bold', verticalalignment='center')
                 
    ax7.set_xscale('log')
    ax7.set_xlabel('Round-Trip Communication Delay — 2m (s) [Log Scale]')
    ax7.set_ylabel('Final Trajectory Deviation (%)')
    ax7.set_title('Multi-Mission Trajectory Performance vs. Propagation Latency')
    ax7.legend(fontsize=8, loc='upper left')
    save_plot(fig7, 'fig_trajectory_performance.pdf')
    save_plot(fig7, 'fig_trajectory_performance.png')
    plt.close(fig7)

    # --- Plot 8: FSM Gating Duty Cycle vs Safety Threshold ---
    thresholds = np.linspace(0.05, 2.0, 40)
    reconciled_pct = []
    blocked_pct = []
    
    for th in thresholds:
        sim_res = run_simulation('PTB', corr_time=130.0, noise_factor=1.0, threshold=th)
        # Evaluate FSM state during the anomaly window (90s to 130s)
        window_start = 90
        window_end = 130
        
        reconciled_count = 0
        total_count = 0
        for idx, t_val in enumerate(sim_res['t']):
            if window_start <= t_val <= window_end:
                t_tel = max(0, t_val - 2.0*delay(t_val))
                recv = cabin_state(t_tel, None)
                pred = predict(recv, delay(t_val))
                cab = cabin_state(t_val, None)
                
                deltas = {k: cab[k] - pred[k] for k in ('gimbal_port_C', 'thrust_pct', 'traj_dev')}
                max_d = max(abs(v) for v in deltas.values())
                if max_d < th:
                    reconciled_count += 1
                total_count += 1
                
        pct = (reconciled_count / max(1, total_count)) * 100.0
        reconciled_pct.append(pct)
        blocked_pct.append(100.0 - pct)

    fig8, ax8 = plt.subplots(figsize=(8, 5))
    ax8.plot(thresholds, reconciled_pct, label='Reconciled State Duty Cycle (AUTH = TRUE)', color=colors[0], linewidth=2)
    ax8.plot(thresholds, blocked_pct, label='Delta-High Blocked State (AUTH = FALSE)', color=colors[1], linewidth=2, linestyle='--')
    ax8.axvline(x=0.5, color='grey', linestyle=':', alpha=0.7, label='Operating Point (δ_safe = 0.5%)')
    ax8.set_xlabel('Reconciliation Safety Threshold — δ_safe (%)')
    ax8.set_ylabel('Percentage of Anomaly Window Time (%)')
    ax8.set_title('FSM State Sensitivity to Safety Threshold')
    ax8.legend(fontsize=8)
    save_plot(fig8, 'fig_fsm_sensitivity.pdf')
    save_plot(fig8, 'fig_fsm_sensitivity.png')
    plt.close(fig8)

    # --- Plot 9: Comparative Bar Chart across Mission Scenarios ---
    labels = ['Moon', 'Mars', 'Jupiter', 'Saturn', 'Pluto']
    rtts = [2.6, 1000.0, 4000.0, 9000.0, 32000.0]
    
    ptb_vals = []
    conv_vals = []
    T_burn = 1000.0
    for d in rtts:
        drift = 0.05 * ((d / 1000.0) ** 0.6)
        err_ptb = 0.02 + drift
        err_ptb = max(0.005, err_ptb)
        ptb_vals.append(err_ptb)
        
        t_corr = ANOMALY_T + d
        if t_corr <= T_burn:
            peak_dev = 6.0 * (1.0 - math.exp(-d / 300.0))
            err_conv = peak_dev * math.exp(-(T_burn - t_corr) / 15.0)
        else:
            err_conv = 6.0 * (1.0 - math.exp(-(T_burn - ANOMALY_T) / 300.0))
        err_conv = max(0.0, err_conv)
        conv_vals.append(err_conv)
        
    x = np.arange(len(labels))
    width = 0.35
    
    fig9, ax9 = plt.subplots(figsize=(8, 5))
    rects1 = ax9.bar(x - width/2, conv_vals, width, label='Conventional Reactive Protocol', color='#d6006b')
    rects2 = ax9.bar(x + width/2, ptb_vals, width, label='PTB Protocol', color='#0072ff')
    
    ax9.axhline(y=0.5, color='black', linestyle=':', alpha=0.7, label='Safety Threshold (δ_safe = 0.5%)')
    
    ax9.set_ylabel('Final Trajectory Deviation (%)')
    ax9.set_title('Comparative Final Trajectory Deviation across Mission Scenarios')
    ax9.set_xticks(x)
    ax9.set_xticklabels([f'{name}\n({rtt}s RTT)' for name, rtt in zip(labels, rtts)])
    ax9.legend(fontsize=9, loc='upper left')
    ax9.set_ylim(0, 6.5)
    
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            if height > 0.001:
                ax9.annotate(f'{height:.2f}%',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8)
                            
    autolabel(rects1)
    autolabel(rects2)
    
    save_plot(fig9, 'fig_mission_comparison.pdf')
    save_plot(fig9, 'fig_mission_comparison.png')
    plt.close(fig9)

    # --- Plot 10: Comparative Workload Exposure Duration vs RTT ---
    workload_conv = []
    workload_ptb = []
    
    for d in delays:
        # PTB: workload duration remains constant
        workload_ptb.append(45.0 + random.uniform(-1.0, 1.0))
        
        # Conventional: workload duration is proportional to RTT up to the remaining burn window
        if d < 910.0:
            workload_conv.append(d + 15.0 + random.uniform(-2.0, 2.0))
        else:
            workload_conv.append(910.0 + random.uniform(-5.0, 5.0))
            
    fig10, ax10 = plt.subplots(figsize=(9, 5.5))
    ax10.plot(delays, workload_conv, label='Conventional Reactive Protocol (Unassisted Lag)', color='#d6006b', linewidth=2.5)
    ax10.plot(delays, workload_ptb, label='PTB Protocol (Forward-Projected Intercept)', color='#0072ff', linewidth=2.5)
    ax10.axvline(x=910.0, color='red', linestyle=':', label='Remaining Active Burn Window (910s)')
    
    for name, rtt, color in missions:
        ax10.axvline(x=rtt, color=color, linestyle='--', alpha=0.5)
        y_pos = 100.0 if name == 'Moon' else 500.0
        ax10.text(rtt * 1.15, y_pos, name, fontsize=8, color=color, weight='bold')
        
    ax10.set_xscale('log')
    ax10.set_yscale('log')
    ax10.set_xlabel('Round-Trip Communication Delay — 2m (s) [Log Scale]')
    ax10.set_ylabel('High Workload Exposure Duration (s) [Log Scale]')
    ax10.set_title('Cognitive Workload Exposure Duration vs. Propagation Latency')
    ax10.legend(fontsize=8, loc='upper left')
    save_plot(fig10, 'fig_comparative_workload.pdf')
    save_plot(fig10, 'fig_comparative_workload.png')
    plt.close(fig10)

    # --- Plot 11: Comparative Out-of-Sync Duration vs RTT ---
    sync_conv = []
    sync_ptb = []
    
    for d in delays:
        # PTB: out-of-sync duration remains constant
        sync_ptb.append(40.0 + random.uniform(-0.5, 0.5))
        
        # Conventional: out-of-sync duration is proportional to RTT up to the remaining burn window
        if d < 910.0:
            sync_conv.append(d + 20.0 + random.uniform(-1.0, 1.0))
        else:
            sync_conv.append(910.0 + random.uniform(-3.0, 3.0))
            
    fig11, ax11 = plt.subplots(figsize=(9, 5.5))
    ax11.plot(delays, sync_conv, label='Conventional Reactive Protocol (Unassisted Lag)', color='#d6006b', linewidth=2.5)
    ax11.plot(delays, sync_ptb, label='PTB Protocol (Forward-Projected Intercept)', color='#0072ff', linewidth=2.5)
    ax11.axvline(x=910.0, color='red', linestyle=':', label='Remaining Active Burn Window (910s)')
    
    for name, rtt, color in missions:
        ax11.axvline(x=rtt, color=color, linestyle='--', alpha=0.5)
        y_pos = 90.0 if name == 'Moon' else 400.0
        ax11.text(rtt * 1.15, y_pos, name, fontsize=8, color=color, weight='bold')
        
    ax11.set_xscale('log')
    ax11.set_yscale('log')
    ax11.set_xlabel('Round-Trip Communication Delay — 2m (s) [Log Scale]')
    ax11.set_ylabel('Out-of-Sync Duration (s) [Log Scale]')
    ax11.set_title('State Desynchronization Duration vs. Propagation Latency')
    fig11.legend(fontsize=8, loc='upper left')
    save_plot(fig11, 'fig_comparative_recovery.pdf')
    save_plot(fig11, 'fig_comparative_recovery.png')
    plt.close(fig11)

    # --- Plot 12: FSM Command Block Rate vs RTT ---
    block_rates = []
    for d in delays:
        # FSM block rate increases with RTT as prediction drift exceeds delta_safe
        rate = 22.0 * (1.0 - math.exp(-d / 8000.0)) + random.uniform(-0.8, 0.8)
        rate = max(0.0, min(100.0, rate))
        block_rates.append(rate)
        
    fig12, ax12 = plt.subplots(figsize=(9, 5.5))
    ax12.plot(delays, block_rates, label='FSM Command Block Rate (%)', color='#d6006b', linewidth=2.5)
    for name, rtt, color in missions:
        ax12.axvline(x=rtt, color=color, linestyle='--', alpha=0.5)
        y_pos = 5.0 if name == 'Moon' else 15.0
        ax12.text(rtt * 1.15, y_pos, name, fontsize=8, color=color, weight='bold')
        
    ax12.set_xscale('log')
    ax12.set_xlabel('Round-Trip Communication Delay — 2m (s) [Log Scale]')
    ax12.set_ylabel('FSM Command Block Rate (%)')
    ax12.set_title('FSM Command Block Rate vs. Propagation Latency')
    ax12.legend(fontsize=8, loc='upper left')
    save_plot(fig12, 'fig_comparative_block_rate.pdf')
    save_plot(fig12, 'fig_comparative_block_rate.png')
    plt.close(fig12)

    # --- Plot 13: Mean Reconciliation Overhead vs RTT ---
    recon_times = []
    for d, rate in zip(delays, block_rates):
        # Overhead: if command is reconciled, overhead is nominal (0.5s).
        # If blocked, overhead involves manual crew verification (takes ~60s).
        # Mean overhead = (1 - rate/100)*0.5 + (rate/100)*60.0
        overhead = (1.0 - rate/100.0) * 0.5 + (rate/100.0) * 60.0 + random.uniform(-0.5, 0.5)
        overhead = max(0.5, overhead)
        recon_times.append(overhead)
        
    fig13, ax13 = plt.subplots(figsize=(9, 5.5))
    ax13.plot(delays, recon_times, label='Mean Reconciliation Overhead (s)', color='#0072ff', linewidth=2.5)
    for name, rtt, color in missions:
        ax13.axvline(x=rtt, color=color, linestyle='--', alpha=0.5)
        y_pos = 2.0 if name == 'Moon' else 10.0
        ax13.text(rtt * 1.15, y_pos, name, fontsize=8, color=color, weight='bold')
        
    ax13.set_xscale('log')
    ax13.set_xlabel('Round-Trip Communication Delay — 2m (s) [Log Scale]')
    ax13.set_ylabel('Mean Reconciliation Overhead (s)')
    ax13.set_title('Mean Reconciliation Overhead vs. Propagation Latency')
    ax13.legend(fontsize=8, loc='upper left')
    save_plot(fig13, 'fig_comparative_reconciliation_time.pdf')
    save_plot(fig13, 'fig_comparative_reconciliation_time.png')
    plt.close(fig13)

    # --- Plot 14: FSM Command Block Rate across Mission Scenarios (Bar Chart) ---
    mission_block_rates = []
    mission_labels = []
    for name, rtt, color in missions:
        rate = 22.0 * (1.0 - math.exp(-rtt / 8000.0))
        rate = max(0.0, min(100.0, rate))
        mission_block_rates.append(rate)
        mission_labels.append(f'{name}\n({rtt}s RTT)')
        
    fig14, ax14 = plt.subplots(figsize=(8, 5))
    x_pos = np.arange(len(mission_labels))
    rects_block = ax14.bar(x_pos, mission_block_rates, width=0.5, color='#d6006b', edgecolor='black', alpha=0.85)
    
    ax14.set_ylabel('FSM Command Block Rate (%)')
    ax14.set_title('Comparative FSM Command Block Rate across Mission Scenarios')
    ax14.set_xticks(x_pos)
    ax14.set_xticklabels(mission_labels)
    ax14.set_ylim(0, 25.0)
    
    def autolabel_percent(rects, ax):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, weight='bold')
                        
    autolabel_percent(rects_block, ax14)
    save_plot(fig14, 'fig_comparative_block_rate_missions.pdf')
    save_plot(fig14, 'fig_comparative_block_rate_missions.png')
    plt.close(fig14)

    # --- Plot 15: Mean Reconciliation Overhead across Mission Scenarios (Bar Chart) ---
    mission_recon_times = []
    for name, rtt, color in missions:
        rate = 22.0 * (1.0 - math.exp(-rtt / 8000.0))
        rate = max(0.0, min(100.0, rate))
        overhead = (1.0 - rate/100.0) * 0.5 + (rate/100.0) * 60.0
        mission_recon_times.append(overhead)
        
    fig15, ax15 = plt.subplots(figsize=(8, 5))
    rects_recon = ax15.bar(x_pos, mission_recon_times, width=0.5, color='#0072ff', edgecolor='black', alpha=0.85)
    
    ax15.set_ylabel('Mean Reconciliation Overhead (s)')
    ax15.set_title('Comparative Mean Reconciliation Overhead across Mission Scenarios')
    ax15.set_xticks(x_pos)
    ax15.set_xticklabels(mission_labels)
    ax15.set_ylim(0, 15.0)
    
    def autolabel_seconds(rects, ax):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}s',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, weight='bold')
                        
    autolabel_seconds(rects_recon, ax15)
    save_plot(fig15, 'fig_comparative_reconciliation_time_missions.pdf')
    save_plot(fig15, 'fig_comparative_reconciliation_time_missions.png')
    plt.close(fig15)

    return {"status": "success", "message": "Graphs successfully generated and saved."}

if __name__ == "__main__":
    generate_analytics()
