import matplotlib.pyplot as plt
import numpy as np

def generate_sequence_diagram():
    # Set up figure
    fig, ax = plt.subplots(figsize=(8, 6.5), dpi=300)
    
    # Timeline vertical lines (x coordinates)
    x_earth = 1.0
    x_mars = 3.0
    
    # Y-axis will be time, going downwards
    y_min = -10
    y_max = 250
    
    ax.set_xlim(0.3, 3.7)
    ax.set_ylim(y_max, y_min) # Invert Y-axis so time runs downwards
    
    # Draw timeline axes
    ax.axvline(x=x_earth, color='#2c3e50', linewidth=2.5, label='Earth Timeline (ERT)')
    ax.axvline(x=x_mars, color='#2c3e50', linewidth=2.5, label='Mars Timeline (SCET)')
    
    # Timeline headers
    ax.text(x_earth, y_min - 5, 'Earth Ground Station\n(ERT Clock)', ha='center', va='bottom', fontsize=10, fontweight='bold', color='#1a365d')
    ax.text(x_mars, y_min - 5, 'Mars Crew Cabin\n(SCET Clock)', ha='center', va='bottom', fontsize=10, fontweight='bold', color='#1a365d')
    
    # Style ticks and grid
    ax.yaxis.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')
    ax.set_ylabel('Mission Time / Epoch (seconds)', fontsize=10, fontweight='bold')
    ax.set_xticks([x_earth, x_mars])
    ax.set_xticklabels(['ERT', 'SCET'], fontsize=9, fontweight='bold')
    
    # Color palette
    color_telemetry = '#3182ce' # Blue
    color_command = '#e53e3e'   # Red
    color_predict = '#805ad5'   # Purple
    color_anomaly = '#dd6b20'   # Orange
    color_recon = '#38a169'     # Green
    
    # --- Downlink 1: Nominal Telemetry ---
    # From Mars t_SCET = 0 to Earth t_ERT = 60
    ax.annotate('', xy=(x_earth, 60), xytext=(x_mars, 0),
                arrowprops=dict(arrowstyle="->", color=color_telemetry, lw=1.5, ls='-', shrinkA=0, shrinkB=0))
    ax.text(2.0, 24, 'Nominal Downlink\n(m = 60s)', color=color_telemetry, ha='center', va='center', fontsize=8, fontstyle='italic')
    
    # --- Anomaly Onset ---
    # Mars SCET = 90
    ax.plot(x_mars, 90, marker='o', color=color_anomaly, markersize=8, zorder=5)
    ax.text(x_mars + 0.08, 90, 'Anomaly Onset\n(t = 90s SCET)', color=color_anomaly, ha='left', va='center', fontsize=9, fontweight='bold')
    
    # --- Downlink 2: Anomaly Telemetry ---
    # From Mars t_SCET = 90 to Earth t_ERT = 150
    ax.annotate('', xy=(x_earth, 150), xytext=(x_mars, 90),
                arrowprops=dict(arrowstyle="->", color=color_anomaly, lw=1.8, ls='-', shrinkA=0, shrinkB=0))
    ax.text(2.0, 115, 'Anomaly Telemetry\nDownlink (m = 60s)', color=color_anomaly, ha='center', va='center', fontsize=8, fontweight='bold')
    
    # --- Earth Detection and AI Prediction ---
    # Earth ERT = 150
    ax.plot(x_earth, 150, marker='s', color=color_predict, markersize=8, zorder=5)
    ax.text(x_earth - 0.08, 150, 'Anomaly Received\n(t = 150s ERT)', color=color_predict, ha='right', va='center', fontsize=9, fontweight='bold')
    
    # Bracket or Region showing prediction window [90, 210]
    # Earth AI projects from t=90 (anomaly state) to t=210 (command arrival)
    ax.fill_between([x_earth - 0.45, x_earth - 0.05], 90, 210, color=color_predict, alpha=0.15)
    ax.plot([x_earth - 0.05, x_earth - 0.45, x_earth - 0.45, x_earth - 0.05], [90, 90, 210, 210], color=color_predict, lw=1.2, ls='--')
    ax.text(x_earth - 0.42, 115, 'Earth AI\nPredictive Window\n[90s to 210s]\n(Horizon = 120s)', 
            color=color_predict, ha='left', va='center', fontsize=8, fontweight='bold')
    
    # --- Uplink: Preemptive Command ---
    # From Earth ERT = 150 to Mars SCET = 210
    ax.annotate('', xy=(x_mars, 210), xytext=(x_earth, 150),
                arrowprops=dict(arrowstyle="->", color=color_command, lw=1.8, ls='-', shrinkA=0, shrinkB=0))
    ax.text(2.0, 185, 'Preemptive Command\nUplink (m = 60s)', color=color_command, ha='center', va='center', fontsize=8, fontweight='bold')
    
    # --- Mars Arrival and FSM Gating ---
    # Mars SCET = 210
    ax.plot(x_mars, 210, marker='o', color=color_recon, markersize=8, zorder=5)
    ax.text(x_mars + 0.08, 210, 'Command Arrival\n& Reality Overlay\n(t = 210s SCET)', color=color_recon, ha='left', va='center', fontsize=9, fontweight='bold')
    
    # Add note about FSM evaluation
    ax.text(x_mars + 0.08, 230, 'FSM Gating Evaluation:\nCheck |True - Est| < 0.5%\nAUTH = TRUE -> Execute!',
            bbox=dict(boxstyle="round,pad=0.3", fc='#f0fff4', ec=color_recon, lw=1),
            color=color_recon, ha='left', va='center', fontsize=8)
    
    # Highlight Latency Masking Interval [90, 210] on Mars Timeline
    ax.axvspan(x_mars - 0.03, x_mars + 0.03, ymin=(250-90)/260, ymax=(250-210)/260, color='#fed7e2', alpha=0.5, zorder=1)
    ax.text(x_mars - 0.08, 150, 'Lag Window\n(Unassisted Lag = 120s)\nMasked by PTB', 
            color='#d53f8c', ha='right', va='center', fontsize=8, fontstyle='italic')
    
    # Formatting
    plt.title('Predictive Temporal Bridge (PTB) Sequence & Timing Diagram', fontsize=12, fontweight='bold', pad=45, color='#1a365d')
    plt.tight_layout()
    
    # Save files to target paths
    import os
    parent_dirs = [
        "/home/jason/SPICE-ns-Project/VirtualPRB-DS-Communication",
        "/home/jason/SPICE-ns-Project/VirtualPRB-DS-Communication/paper",
        "/home/jason/SPICE-ns-Project/VirtualPRB-DS-Communication/paper/w_paper"
    ]
    for d in parent_dirs:
        pdf_path = os.path.join(d, 'fig_simulation_sequence.pdf')
        png_path = os.path.join(d, 'fig_simulation_sequence.png')
        plt.savefig(pdf_path, format='pdf', bbox_inches='tight')
        plt.savefig(png_path, format='png', bbox_inches='tight', dpi=300)
        print(f"Saved to {pdf_path} and {png_path}")
        
    plt.close()

if __name__ == "__main__":
    generate_sequence_diagram()
