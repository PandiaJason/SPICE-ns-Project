import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set global matplotlib styles for clean black and white patent drawings
plt.rcParams['text.color'] = 'black'
plt.rcParams['axes.labelcolor'] = 'black'
plt.rcParams['xtick.color'] = 'black'
plt.rcParams['ytick.color'] = 'black'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']

def draw_figure_1():
    """Generates Figure 1: System Architecture of the Predictive Temporal Bridge"""
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 75)
    ax.axis('off')

    ax.text(50, 72, "FIG. 1: PREDICTIVE TEMPORAL BRIDGE (PTB) ARCHITECTURE", 
            ha='center', va='center', fontsize=12, fontweight='bold')

    box_props = dict(boxstyle="square,pad=0.5", fc="white", ec="black", lw=1.5)

    # Ground Station
    ax.text(20, 40, "GROUND STATION\n(EARTH)", ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(20, 25, "GROUND PTPU\n(AI PREDICTOR)\n[Projects t -> t+2m]", ha='center', va='center', fontsize=9, bbox=box_props)
    
    # Spacecraft
    ax.text(80, 40, "DEEP-SPACE SPACECRAFT\n(MARS)", ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(80, 25, "SPACECRAFT PTPU\n(REALITY ARBITER)\n[Reconciles t+2m]", ha='center', va='center', fontsize=9, bbox=box_props)

    # Delay line
    ax.annotate("", xy=(65, 30), xytext=(35, 30), arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
    ax.text(50, 33, "Preemptive Command\n(Arrives at t+2m)", ha='center', va='center', fontsize=8)

    ax.annotate("", xy=(35, 20), xytext=(65, 20), arrowprops=dict(arrowstyle="->", color="black", lw=1.5, ls="--"))
    ax.text(50, 17, "Asynchronous Telemetry\n(Delay: m seconds)", ha='center', va='center', fontsize=8)

    plt.tight_layout()
    plt.savefig('figure_1.png', bbox_inches='tight', facecolor='white')
    plt.close()

def draw_figure_2():
    """Generates Figure 2: Internal hardware architecture of the PTPU"""
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 75)
    ax.axis('off')

    ax.text(50, 72, "FIG. 2: PREDICTIVE TEMPORAL PROCESSING UNIT (PTPU) ARCHITECTURE", 
            ha='center', va='center', fontsize=12, fontweight='bold')

    # Chip boundary
    chip = patches.Rectangle((20, 15), 60, 50, fill=False, edgecolor='black', linewidth=2.0)
    ax.add_patch(chip)
    ax.text(50, 62, "PTPU ASIC CHIP", ha='center', va='center', fontsize=10, fontweight='bold')

    box_props = dict(boxstyle="square,pad=0.5", fc="white", ec="black", lw=1.5)

    ax.text(35, 45, "MINIMAL DETERMINISTIC\nCPU (RISC-V Lockstep)", ha='center', va='center', fontsize=8, bbox=box_props)
    ax.text(65, 45, "NEURAL MATRIX\nACCELERATOR (NMA)", ha='center', va='center', fontsize=8, bbox=box_props)
    ax.text(35, 30, "NON-VOLATILE FIRMWARE ROM\n(PTB Logic / Kinematic Models)", ha='center', va='center', fontsize=8, bbox=box_props)
    ax.text(65, 30, "UNIVERSAL AEROSPACE\nBUS INTERFACE (SpaceWire)", ha='center', va='center', fontsize=8, bbox=box_props)

    # Connections
    arrow_props = dict(arrowstyle="<->", color="black", lw=1.5)
    ax.annotate("", xy=(52, 45), xytext=(48, 45), arrowprops=arrow_props)
    ax.annotate("", xy=(35, 36), xytext=(35, 42), arrowprops=arrow_props)
    ax.annotate("", xy=(65, 36), xytext=(65, 42), arrowprops=arrow_props)
    
    plt.tight_layout()
    plt.savefig('figure_2.png', bbox_inches='tight', facecolor='white')
    plt.close()

def draw_figure_3():
    """Generates Figure 3: Reality Reconciliation Engine FSM"""
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 75)
    ax.axis('off')

    ax.text(50, 72, "FIG. 3: REALITY RECONCILIATION ENGINE FSM", 
            ha='center', va='center', fontsize=12, fontweight='bold')

    def draw_state(x, y, r, label, state_num):
        circle = patches.Circle((x, y), r, fill=True, facecolor='white', edgecolor='black', linewidth=2.0)
        ax.add_patch(circle)
        ax.text(x, y + 2, label, ha='center', va='center', fontsize=8, fontweight='bold')
        ax.text(x, y - 1, f"STATE [{state_num}]", ha='center', va='center', fontsize=7.5, style='italic')

    draw_state(25, 45, 10, "DATA\nINGRESS", "1")
    draw_state(50, 45, 10, "DEVIATION\nCALCULATION", "3")
    draw_state(75, 55, 10, "RECONCILED\n(Valid)", "5A")
    draw_state(75, 35, 10, "DESYNCED\n(Blocked)", "5B")
    
    ax.text(50, 60, "SENSOR\nSAMPLING [2]", ha='center', va='center', fontsize=8, bbox=dict(boxstyle="square,pad=0.5", fc="white", ec="black", lw=1.5))
    
    arrow_props = dict(arrowstyle="->", color="black", lw=1.5)
    
    ax.annotate("", xy=(40, 45), xytext=(35, 45), arrowprops=arrow_props)
    ax.annotate("", xy=(50, 52), xytext=(50, 56), arrowprops=arrow_props)
    
    ax.annotate("", xy=(66, 52), xytext=(59, 48), arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
    ax.text(60, 54, "Delta < Safe", ha='center', va='center', fontsize=8)

    ax.annotate("", xy=(66, 38), xytext=(59, 42), arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
    ax.text(60, 36, "Delta > Safe", ha='center', va='center', fontsize=8)

    plt.tight_layout()
    plt.savefig('figure_3.png', bbox_inches='tight', facecolor='white')
    plt.close()

def draw_figure_4():
    """Generates Figure 4: Integration of PTPU into avionics"""
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 75)
    ax.axis('off')

    ax.text(50, 72, "FIG. 4: AVIONICS NETWORK INTEGRATION", 
            ha='center', va='center', fontsize=12, fontweight='bold')
            
    box_props = dict(boxstyle="square,pad=0.5", fc="white", ec="black", lw=1.5)

    ax.text(50, 50, "SPACECRAFT PRIMARY FLIGHT COMPUTER", ha='center', va='center', fontsize=9, bbox=box_props)
    ax.text(25, 30, "SENSORS", ha='center', va='center', fontsize=9, bbox=box_props)
    ax.text(50, 30, "SPACEWIRE / MIL-STD-1553 BUS", ha='center', va='center', fontsize=10, fontweight='bold')
    ax.plot([10, 90], [30, 30], color="black", lw=2.0)
    
    ax.text(75, 30, "PTPU (AI CO-PROCESSOR)", ha='center', va='center', fontsize=9, bbox=box_props)
    ax.text(50, 10, "COMMANDER HMI DASHBOARD", ha='center', va='center', fontsize=9, bbox=box_props)
    
    ax.annotate("", xy=(50, 32), xytext=(50, 47), arrowprops=dict(arrowstyle="<->", color="black", lw=1.5))
    ax.annotate("", xy=(75, 32), xytext=(75, 38), arrowprops=dict(arrowstyle="<->", color="black", lw=1.5))
    ax.annotate("", xy=(25, 32), xytext=(25, 38), arrowprops=dict(arrowstyle="<->", color="black", lw=1.5))
    ax.annotate("", xy=(50, 13), xytext=(50, 28), arrowprops=dict(arrowstyle="<->", color="black", lw=1.5))

    plt.tight_layout()
    plt.savefig('figure_4.png', bbox_inches='tight', facecolor='white')
    plt.close()

if __name__ == "__main__":
    print("Generating Figure 1...")
    draw_figure_1()
    print("Generating Figure 2...")
    draw_figure_2()
    print("Generating Figure 3...")
    draw_figure_3()
    print("Generating Figure 4...")
    draw_figure_4()
    print("All figures generated successfully as black and white patent drawings!")
