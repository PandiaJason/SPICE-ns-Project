import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Ensure figures directory exists
fig_dir = "/home/jason/SPICE-ns-Project/SMOPS2026/figures"
os.makedirs(fig_dir, exist_ok=True)

def generate_nn_architecture():
    print("--- Generating Neural Network Architecture Diagram ---")
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    
    # Hide axes
    ax.axis('off')
    
    # Set limits
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.5, 5.5)
    
    # Define layer configurations
    # Name, x_pos, nodes, color, label, dims, activation
    layers = [
        ("Input", 1.0, 31, "#1f77b4", "Input Vector\n(Telemetry Channels)", "31", "None"),
        ("Encoder\nHidden", 3.0, 16, "#ff7f0e", "Encoder Hidden\n(Fully Connected)", "16\n[ReLU]", "ReLU"),
        ("Latent\nBottleneck", 5.0, 4, "#9467bd", "Latent Space\n(Compressed Code)", "4\n[Bottleneck]", "None"),
        ("Decoder\nHidden", 7.0, 16, "#ff7f0e", "Decoder Hidden\n(Fully Connected)", "16\n[ReLU]", "ReLU"),
        ("Output", 9.0, 31, "#2ca02c", "Reconstructed\nTelemetry Vector", "31", "None")
    ]
    
    # Draw layer columns
    for name, x, nodes, color, label, dims, act in layers:
        # Draw node column representations
        # We will draw a subset of circles to represent nodes
        num_circles = min(nodes, 8)
        y_positions = [2.5] if num_circles == 1 else [2.5 + 1.6 * (i / (num_circles - 1) - 0.5) for i in range(num_circles)]
        
        # Draw nodes
        for y in y_positions:
            circle = plt.Circle((x, y), 0.15, facecolor=color, edgecolor="black", linewidth=1.2, zorder=3)
            ax.add_patch(circle)
        
        # Add labels and captions
        ax.text(x, 4.3, name, fontsize=11, fontweight="bold", ha="center", va="center")
        ax.text(x, 0.9, label, fontsize=8, ha="center", va="top")
        
        # Box for dimensions
        bbox_props = dict(boxstyle="round,pad=0.3", fc="white", ec=color, lw=1.5, alpha=0.9)
        ax.text(x, 4.7, f"Dim: {dims}", fontsize=9, ha="center", bbox=bbox_props)
        
    # Draw connection lines (arrows) and parameter counts
    connections = [
        (1.0, 3.0, "31 x 16 + 16\n= 512 Params"),
        (3.0, 5.0, "16 x 4 + 4\n= 68 Params"),
        (5.0, 7.0, "4 x 16 + 16\n= 80 Params"),
        (7.0, 9.0, "16 x 31 + 31\n= 527 Params")
    ]
    
    for x1, x2, param_text in connections:
        # Add dynamic arrow
        arrow = patches.FancyArrowPatch(
            (x1 + 0.35, 2.5), (x2 - 0.35, 2.5),
            arrowstyle="->", mutation_scale=15, color="dimgray", lw=2, zorder=1
        )
        ax.add_patch(arrow)
        # Parameter text
        ax.text((x1+x2)/2.0, 2.7, param_text, fontsize=8, fontweight="bold", 
                color="black", ha="center", va="bottom",
                bbox=dict(facecolor='#f7f7f7', edgecolor='lightgray', boxstyle='round,pad=0.2'))
 
    # Draw Title and Metadata
    ax.text(5.0, 0.1, "Micro-Autoencoder: 31 -> 16 -> 4 -> 16 -> 31 Architecture\nTotal Flight Parameters: 1,203 Weights & Biases (4.81 KB ROM Footprint)", 
            fontsize=10.5, fontweight="bold", color="#1c1c1c", ha="center", va="center")
            
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "nn_architecture.png"), dpi=300)
    plt.close()

def generate_pipeline_flowchart():
    print("--- Generating Training and Testing Pipeline Flowchart ---")
    fig, ax = plt.subplots(figsize=(10.0, 5.2))
    ax.axis('off')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.2)
    
    # -------------------------------------------------------------
    # Training Stage (Left Column)
    # -------------------------------------------------------------
    # Draw dashed bounding box for Ground / Training
    train_box = patches.FancyBboxPatch(
        (0.2, 0.4), 4.4, 4.4, boxstyle="round,pad=0.1",
        facecolor="#fcfcfc", edgecolor="navy", linestyle="--", linewidth=1.5, zorder=0
    )
    ax.add_patch(train_box)
    ax.text(2.4, 4.6, "OFFLINE CALIBRATION PHASE (ON-GROUND)", fontsize=10, fontweight="bold", color="navy", ha="center")
    
    # Blocks inside Training
    # Block 1: 31-ch healthy nominals
    ax.text(2.4, 3.8, "Raw 31-Channel Housekeeping Telemetry\n(Collected during AIT or Nominal Checkout)", 
            ha="center", va="center", fontsize=8.5,
            bbox=dict(facecolor='#e6f2ff', edgecolor='#1f77b4', boxstyle='round,pad=0.5', lw=1.2))
            
    # Arrow 1->2
    ax.add_patch(patches.FancyArrowPatch((2.4, 3.4), (2.4, 3.0), arrowstyle="->", mutation_scale=12, color="gray", lw=1.5))
    
    # Block 2: Unsupervised Reconstruction Loss Optimization
    ax.text(2.4, 2.5, "Unsupervised Mini-Batch Training\nMinimize Mean Squared Error (MSE)\nOptimizer: Adam (lr=0.01) | Epochs: 60", 
            ha="center", va="center", fontsize=8.5, fontweight="bold",
            bbox=dict(facecolor='#ffe6cc', edgecolor='#ff7f0e', boxstyle='round,pad=0.5', lw=1.2))
            
    # Arrow 2->3
    ax.add_patch(patches.FancyArrowPatch((2.4, 2.0), (2.4, 1.6), arrowstyle="->", mutation_scale=12, color="gray", lw=1.5))
    
    # Block 3: Validation Threshold Calibration
    ax.text(2.4, 1.1, "Dynamic Calibration of Threshold tau\n99.0th Percentile of Validation MSE\n(Ensures Strict 1% False Alarm Rate)", 
            ha="center", va="center", fontsize=8.5,
            bbox=dict(facecolor='#f3e6ff', edgecolor='#9467bd', boxstyle='round,pad=0.5', lw=1.2))
            
    # -------------------------------------------------------------
    # OBC Upload Bridge
    # -------------------------------------------------------------
    # Arrow from Left to Right
    upload_arrow = patches.FancyArrowPatch(
        (4.7, 2.5), (5.3, 2.5),
        arrowstyle="-|>", mutation_scale=18, color="#8b0000", lw=3.0, zorder=2
    )
    ax.add_patch(upload_arrow)
    ax.text(5.0, 2.8, "OBC Upload\nWeights & tau", fontsize=9, fontweight="bold", color="#8b0000", ha="center")
    
    # -------------------------------------------------------------
    # Testing/Inference Stage (Right Column)
    # -------------------------------------------------------------
    # Draw dashed bounding box for Spacecraft / Testing
    test_box = patches.FancyBboxPatch(
        (5.4, 0.4), 4.4, 4.4, boxstyle="round,pad=0.1",
        facecolor="#fcfcfc", edgecolor="darkgreen", linestyle="--", linewidth=1.5, zorder=0
    )
    ax.add_patch(test_box)
    ax.text(7.6, 4.6, "ON-BOARD INFERENCE PHASE (DEEP-SPACE)", fontsize=10, fontweight="bold", color="darkgreen", ha="center")
    
    # Block 1: Real-Time Telemetry
    ax.text(7.6, 3.8, "Real-Time 31-Channel Telemetry Stream\nAcquisition Interval: dt = 30 seconds", 
            ha="center", va="center", fontsize=8.5,
            bbox=dict(facecolor='#e6f7e6', edgecolor='#2ca02c', boxstyle='round,pad=0.5', lw=1.2))
            
    # Arrow 1->2
    ax.add_patch(patches.FancyArrowPatch((7.6, 3.4), (7.6, 3.0), arrowstyle="->", mutation_scale=12, color="gray", lw=1.5))
    
    # Block 2: Reconstruction MSE Evaluation
    ax.text(7.6, 2.5, "On-Board Micro-Autoencoder Inference\nCompute Step-wise reconstruction MSE\nIs MSE > threshold tau?", 
            ha="center", va="center", fontsize=8.5, fontweight="bold",
            bbox=dict(facecolor='#fff0f0', edgecolor='#d62728', boxstyle='round,pad=0.5', lw=1.2))
            
    # Conditional Arrows 2 -> Mode A (down left) & Mode B (down right)
    arrow_left = patches.FancyArrowPatch((7.0, 2.0), (6.4, 1.4), arrowstyle="->", mutation_scale=12, color="green", lw=2)
    arrow_right = patches.FancyArrowPatch((8.2, 2.0), (8.8, 1.4), arrowstyle="->", mutation_scale=12, color="red", lw=2)
    ax.add_patch(arrow_left)
    ax.add_patch(arrow_right)
    
    ax.text(6.5, 1.8, "NO\n(Nominal)", fontsize=8, color="green", fontweight="bold", ha="right")
    ax.text(8.7, 1.8, "YES\n(Anomalous)", fontsize=8, color="red", fontweight="bold", ha="left")
    
    # Block 3a: Mode A Downlink
    ax.text(6.2, 0.9, "MODE A: Heartbeat\nTransmit 10-byte nominal\nstatus heartbeat packet\n(70.10% Bandwidth Savings)", 
            ha="center", va="center", fontsize=7.5,
            bbox=dict(facecolor='#eafaf1', edgecolor='#2ca02c', boxstyle='round,pad=0.4', lw=1.0))
            
    # Block 3b: Mode B Downlink
    ax.text(9.0, 0.9, "MODE B: Diagnostics\nFreeze 30-sample buffer\nOverlap-free GZIP compression\nUplink high-fidelity diagnostics", 
            ha="center", va="center", fontsize=7.5,
            bbox=dict(facecolor='#fdf2f2', edgecolor='#d62728', boxstyle='round,pad=0.4', lw=1.0))
            
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "pipeline_flowchart.png"), dpi=300)
    plt.close()

def generate_mission_scenario():
    print("--- Generating Martian Rover-Relay Mission Scenario Diagram ---")
    fig, ax = plt.subplots(figsize=(10.0, 4.6))
    ax.axis('off')
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.3, 5.2)

    # 1. Mars Surface and Rover
    # Draw Mars surface arc
    mars_surface = patches.Arc((1.0, -1.0), 3.5, 3.0, theta1=0, theta2=90, color="#d14905", lw=3, zorder=1)
    ax.add_patch(mars_surface)
    ax.text(1.2, 0.3, "Martian Surface\n(Jezero Crater)", color="#d14905", fontsize=9.5, fontweight="bold", ha="center")
    
    # Rover block
    rover_box = dict(boxstyle="round,pad=0.4", fc="#fdf2ee", ec="#d14905", lw=1.5, alpha=0.95)
    ax.text(1.2, 1.2, "Martian Surface Rover\n(Surface Activities)", fontsize=8.5, fontweight="bold", ha="center", bbox=rover_box, zorder=2)

    # 2. MLO 3U CubeSat (Low Orbit)
    mlo_box = dict(boxstyle="round,pad=0.5", fc="#e6f7ff", ec="#007acc", lw=2.0, alpha=0.95)
    ax.text(3.5, 2.9, "MLO 3U CubeSat Relay\n(Edge-AI Diagnostics\n& Dynamic Compression\nROM: 4.81 KB | Param: 1,203)", 
            fontsize=8.5, fontweight="bold", ha="center", bbox=mlo_box, zorder=2)
    
    # Draw MLO Orbit Arc
    mlo_orbit = patches.Arc((1.0, -1.0), 5.5, 5.0, theta1=0, theta2=90, color="#007acc", linestyle="--", lw=1.2, zorder=1)
    ax.add_patch(mlo_orbit)
    
    # 3. HMO Mothership (High Orbit)
    hmo_box = dict(boxstyle="round,pad=0.5", fc="#faf0fa", ec="#9467bd", lw=1.5, alpha=0.95)
    ax.text(6.8, 4.1, "HMO Mothership Orbiter\n(High-Capacity Mothership\nBackhaul Link Node)", 
            fontsize=8.5, fontweight="bold", ha="center", bbox=hmo_box, zorder=2)
    
    # Draw HMO Orbit Arc
    hmo_orbit = patches.Arc((1.0, -1.0), 10.0, 9.0, theta1=0, theta2=90, color="#9467bd", linestyle="--", lw=1.2, zorder=1)
    ax.add_patch(hmo_orbit)

    # 4. Earth and DSN
    # Draw Earth surface arc
    earth_surface = patches.Arc((9.0, -1.0), 3.0, 2.5, theta1=90, theta2=180, color="#1f77b4", lw=3, zorder=1)
    ax.add_patch(earth_surface)
    ax.text(8.8, 0.3, "Planet Earth\n(DSN Ground)", color="#1f77b4", fontsize=9.5, fontweight="bold", ha="center")
    
    # DSN Antenna block
    dsn_box = dict(boxstyle="round,pad=0.4", fc="#e6f2ff", ec="#1f77b4", lw=1.5, alpha=0.95)
    ax.text(8.8, 1.2, "Earth DSN Station\n(70m Antenna Array)", fontsize=8.5, fontweight="bold", ha="center", bbox=dsn_box, zorder=2)

    # 5. Communication Links (Arrows)
    # Link 1: Rover -> MLO CubeSat
    arrow_1 = patches.FancyArrowPatch(
        (1.5, 1.5), (2.8, 2.5),
        arrowstyle="-|>", mutation_scale=15, color="#d14905", lw=2.0, zorder=3
    )
    ax.add_patch(arrow_1)
    ax.text(1.9, 2.1, "Proximity S-Band Link\n(9.6-19.2 kbps, 5-20W)", fontsize=7.5, color="#d14905", fontweight="bold", ha="left")

    # Link 2: MLO CubeSat -> HMO Mothership
    arrow_2 = patches.FancyArrowPatch(
        (4.7, 3.3), (6.0, 3.8),
        arrowstyle="-|>", mutation_scale=15, color="#007acc", lw=2.5, zorder=3
    )
    ax.add_patch(arrow_2)
    ax.text(5.4, 3.2, "Dynamic inter-Satellite Link\nMode A: 10-byte Heartbeat\nMode B: Compressed Diagnostics\n(70.10% Data Savings)", 
            fontsize=7.5, color="#007acc", fontweight="bold", ha="center")

    # Link 3: HMO Mothership -> Earth DSN
    arrow_3 = patches.FancyArrowPatch(
        (7.4, 3.6), (8.5, 1.5),
        arrowstyle="-|>", mutation_scale=15, color="#9467bd", lw=2.0, zorder=3
    )
    ax.add_patch(arrow_3)
    ax.text(8.2, 2.6, "Deep Space Ka-Band Link\n4-20 Light-Minutes Latency\nDSN Backhaul", fontsize=7.5, color="#9467bd", fontweight="bold", ha="left")

    # Title
    ax.text(5.0, -0.1, "Mars Rover-to-Earth Deep Space Network (DSN) Communication Relay Architecture", 
            fontsize=11, fontweight="bold", color="#1c1c1c", ha="center")

    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "mission_scenario.png"), dpi=300)
    plt.close()

if __name__ == "__main__":
    generate_nn_architecture()
    generate_pipeline_flowchart()
    generate_mission_scenario()
    print("All architectural, flowchart, and mission scenario diagrams compiled successfully.")
