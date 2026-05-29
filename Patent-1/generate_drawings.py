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
    """Generates Figure 1: System Block Diagram of the Dynamic Solar Blind Transceiver System"""
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 75)
    ax.axis('off')

    # Draw title
    ax.text(50, 72, "FIG. 1: DEEP SPACE OPTICAL TRANSCEIVER WITH DYNAMIC SOLAR BLIND ASSEMBLY", 
            ha='center', va='center', fontsize=12, fontweight='bold')

    # Box properties for patent line drawings (white fill, black border, 1.5 line width)
    box_props = dict(boxstyle="square,pad=0.5", fc="white", ec="black", lw=1.5)
    dashed_box_props = dict(boxstyle="square,pad=0.5", fc="white", ec="black", lw=1.5, ls="--")

    # Define blocks (x, y, width, height, text)
    # Incoming signals
    ax.text(10, 60, "SOLAR GLARE\nAND NOISE [101]", ha='center', va='center', fontsize=9, bbox=box_props)
    ax.text(10, 42, "DEEP SPACE\nLASER BEACON [102]", ha='center', va='center', fontsize=9, bbox=box_props)

    # Shutter Assembly (dashed box to group)
    shutter_group = patches.Rectangle((22, 28), 28, 40, fill=False, edgecolor='black', linestyle=':', linewidth=1.5)
    ax.add_patch(shutter_group)
    ax.text(36, 65, "DYNAMIC SOLAR BLIND [103]", ha='center', va='center', fontsize=10, fontweight='bold')

    # Inside shutter assembly
    ax.text(36, 54, "LIGHT/UV SENSOR\nARRAY [104]", ha='center', va='center', fontsize=9, bbox=box_props)
    ax.text(36, 36, "DYNAMIC OPTICAL\nSHUTTER ASSEMBLY [105]\n(LIQUID CRYSTAL/MECHANICAL)", 
            ha='center', va='center', fontsize=8, bbox=box_props)

    # Telescope & Detectors
    ax.text(68, 36, "TELESCOPE\nOPTICAL ASSEMBLY [106]", ha='center', va='center', fontsize=9, bbox=box_props)
    ax.text(90, 36, "PHOTON-COUNTING\nDETECTOR ARRAY [107]", ha='center', va='center', fontsize=9, bbox=box_props)

    # Controller
    ax.text(50, 12, "ONBOARD MICROCONTROLLER STATE MACHINE\n(STM32/ESP32-GRADE) [108]", 
            ha='center', va='center', fontsize=10, fontweight='bold', bbox=box_props)

    # Connective arrows
    arrow_props = dict(arrowstyle="->", color="black", lw=1.5)
    double_arrow_props = dict(arrowstyle="<->", color="black", lw=1.5)

    # Solar glare to sensor array
    ax.annotate("", xy=(26, 54), xytext=(18, 60), arrowprops=arrow_props)
    # Laser beacon through shutter to optics
    ax.annotate("", xy=(26, 36), xytext=(18, 42), arrowprops=arrow_props)
    ax.annotate("", xy=(52, 36), xytext=(46, 36), arrowprops=arrow_props)
    ax.annotate("", xy=(78, 36), xytext=(58, 36), arrowprops=arrow_props)
    
    # Sensor readout to controller
    ax.annotate("", xy=(45, 17), xytext=(36, 49), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=-90,angleB=180,rad=0"))
    ax.text(25, 23, "PHYSICAL\nREADOUT [109]", ha='center', va='center', fontsize=8)

    # Controller to physical shutter control
    ax.annotate("", xy=(40, 31), xytext=(50, 17), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=90,angleB=0,rad=0"))
    ax.text(58, 23, "SHUTTER\nDRIVE SIGNAL [110]", ha='center', va='center', fontsize=8)

    # Controller to telescope/detector telemetry/control
    ax.annotate("", xy=(85, 31), xytext=(65, 12), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=90,angleB=0,rad=0"))
    ax.text(80, 20, "LINK CONFIG\n& FEEDBACK [111]", ha='center', va='center', fontsize=8)

    plt.tight_layout()
    plt.savefig('figure_1.png', bbox_inches='tight', facecolor='white')
    plt.close()

def draw_figure_2():
    """Generates Figure 2: Detailed Electronic Schematic & Optical Layout"""
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 75)
    ax.axis('off')

    # Draw title
    ax.text(50, 72, "FIG. 2: SENSOR READOUT & SHUTTER ACTUATION ELECTRONIC SCHEMATIC", 
            ha='center', va='center', fontsize=12, fontweight='bold')

    box_props = dict(boxstyle="square,pad=0.5", fc="white", ec="black", lw=1.5)

    # Sensor Array Circuit
    ax.text(22, 60, "MONOCHROME PHOTODIODE\nARRAY [201]", ha='center', va='center', fontsize=9, bbox=box_props)
    ax.text(22, 45, "TRANSIMPEDANCE\nAMPLIFIER (TIA) [202]", ha='center', va='center', fontsize=9, bbox=box_props)
    ax.text(22, 30, "LOW-PASS FILTER\n(ANTI-ALIASING) [203]", ha='center', va='center', fontsize=9, bbox=box_props)

    # Microcontroller and submodules
    mcu_box = patches.Rectangle((45, 15), 32, 50, fill=False, edgecolor='black', linewidth=2.0)
    ax.add_patch(mcu_box)
    ax.text(61, 62, "MICROCONTROLLER [108]", ha='center', va='center', fontsize=10, fontweight='bold')

    ax.text(61, 50, "ANALOG-TO-DIGITAL\nCONVERTER (ADC) [204]", ha='center', va='center', fontsize=9, bbox=box_props)
    ax.text(61, 35, "FINITE STATE MACHINE\n(FSM) CORE [205]", ha='center', va='center', fontsize=9, bbox=box_props)
    ax.text(61, 20, "DIGITAL-TO-ANALOG (DAC) /\nPWM GENERATOR [206]", ha='center', va='center', fontsize=9, bbox=box_props)

    # Shutter Actuator and Shutter
    ax.text(90, 30, "LIQUID CRYSTAL\nOPACITY DRIVER / \nSTEPPER MOTOR [207]", ha='center', va='center', fontsize=8, bbox=box_props)
    ax.text(90, 50, "SHUTTER BARRIER\nASSEMBLY [208]", ha='center', va='center', fontsize=9, bbox=box_props)

    # Connection lines
    arrow_props = dict(arrowstyle="->", color="black", lw=1.5)

    # Sensor to TIA
    ax.annotate("", xy=(22, 49), xytext=(22, 55), arrowprops=arrow_props)
    # TIA to LPF
    ax.annotate("", xy=(22, 34), xytext=(22, 40), arrowprops=arrow_props)
    # LPF to ADC (crosses into MCU boundary)
    ax.annotate("", xy=(48, 50), xytext=(22, 26), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=0,angleB=-90,rad=0"))
    ax.text(32, 42, "ANALOG\nSIGNAL [209]", ha='center', va='center', fontsize=8)

    # ADC to FSM
    ax.annotate("", xy=(61, 39), xytext=(61, 46), arrowprops=arrow_props)
    # FSM to DAC/PWM
    ax.annotate("", xy=(61, 24), xytext=(61, 31), arrowprops=arrow_props)

    # DAC/PWM to Driver
    ax.annotate("", xy=(82, 30), xytext=(72, 20), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=90,angleB=0,rad=0"))
    ax.text(78, 23, "DRIVE\nSIGNAL [210]", ha='center', va='center', fontsize=8)

    # Driver to Shutter Barrier
    ax.annotate("", xy=(90, 46), xytext=(90, 35), arrowprops=arrow_props)

    plt.tight_layout()
    plt.savefig('figure_2.png', bbox_inches='tight', facecolor='white')
    plt.close()

def draw_figure_3():
    """Generates Figure 3: Finite State Machine Transition Diagram"""
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 75)
    ax.axis('off')

    # Draw title
    ax.text(50, 72, "FIG. 3: FINITE STATE MACHINE (FSM) STATE TRANSITION DIAGRAM", 
            ha='center', va='center', fontsize=12, fontweight='bold')

    # State node drawer helper
    def draw_state(x, y, r, label, state_num):
        circle = patches.Circle((x, y), r, fill=True, facecolor='white', edgecolor='black', linewidth=2.0)
        ax.add_patch(circle)
        ax.text(x, y + 1.5, label, ha='center', va='center', fontsize=8, fontweight='bold')
        ax.text(x, y - 2, f"STATE [{state_num}]", ha='center', va='center', fontsize=7, style='italic')

    # Draw States
    draw_state(20, 50, 9, "ACQUISITION", "301")
    draw_state(50, 50, 9, "TRACKING &\nMONITORING", "302")
    draw_state(80, 50, 9, "DYNAMIC\nMASKING", "303")
    draw_state(50, 20, 9, "UNALIGNED\nHOLD", "304")

    arrow_props = dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="arc3,rad=0.15")
    arrow_props_rev = dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="arc3,rad=0.15")

    # Transition 301 -> 302: Laser beacon locked
    ax.annotate("", xy=(41, 51), xytext=(29, 51), arrowprops=arrow_props)
    ax.text(35, 55, "Beacon Locked\n[T31]", ha='center', va='center', fontsize=7)

    # Transition 302 -> 301: Laser beacon lost
    ax.annotate("", xy=(29, 49), xytext=(41, 49), arrowprops=arrow_props_rev)
    ax.text(35, 43, "Beacon Lost\n[T32]", ha='center', va='center', fontsize=7)

    # Transition 302 -> 303: Solar noise > Threshold
    ax.annotate("", xy=(71, 51), xytext=(59, 51), arrowprops=arrow_props)
    ax.text(65, 56, "Solar Noise > Th1\n[T33]", ha='center', va='center', fontsize=7)

    # Transition 303 -> 302: Solar noise < Threshold - Hysteresis
    ax.annotate("", xy=(59, 49), xytext=(71, 49), arrowprops=arrow_props_rev)
    ax.text(65, 42, "Solar Noise < Th1 - Hys\n[T34]", ha='center', va='center', fontsize=7)

    # Transition 302 -> 304: Critical pointing drift / high solar noise
    ax.annotate("", xy=(49, 29), xytext=(49, 41), arrowprops=arrow_props)
    ax.text(44, 35, "Drift > Th2\n[T35]", ha='center', va='center', fontsize=7)

    # Transition 304 -> 301: Recovery & Realignment
    ax.annotate("", xy=(21, 41), xytext=(42, 21), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="arc3,rad=-0.1"))
    ax.text(26, 27, "Realignment\nCommand [T36]", ha='center', va='center', fontsize=7)

    # Transition 303 -> 304: Thermal limit / extreme noise
    ax.annotate("", xy=(58, 21), xytext=(79, 41), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="arc3,rad=0.1"))
    ax.text(74, 27, "Critical Solar\nGlare [T37]", ha='center', va='center', fontsize=7)

    plt.tight_layout()
    plt.savefig('figure_3.png', bbox_inches='tight', facecolor='white')
    plt.close()

def draw_figure_4():
    """Generates Figure 4: Operational Flowchart of the Control Logic"""
    fig, ax = plt.subplots(figsize=(10, 8.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Draw title
    ax.text(50, 97, "FIG. 4: REACTIVE SOLAR BLIND CONTROL METHODOLOGY FLOWCHART", 
            ha='center', va='center', fontsize=12, fontweight='bold')

    box_props = dict(boxstyle="square,pad=0.4", fc="white", ec="black", lw=1.5)
    diamond_props = dict(boxstyle="sawtooth,pad=0.4", fc="white", ec="black", lw=1.5) # represented as a diamond shape in matplotlib by rotation, but we can draw a custom polygon or use simple rectangle with label for clean look

    # Custom function to draw diamond
    def draw_diamond(x, y, w, h, text, step_num):
        pts = [(x, y+h/2), (x+w/2, y), (x, y-h/2), (x-w/2, y)]
        poly = patches.Polygon(pts, fill=True, facecolor='white', edgecolor='black', linewidth=1.5)
        ax.add_patch(poly)
        ax.text(x, y + 0.5, text, ha='center', va='center', fontsize=8)
        ax.text(x, y - h/2 - 2, f"STEP [{step_num}]", ha='center', va='center', fontsize=7, style='italic')

    # Start Node
    ax.text(50, 90, "START: SYSTEM INITIALIZATION [401]", ha='center', va='center', fontsize=8, 
            bbox=dict(boxstyle="round4,pad=0.5", fc="white", ec="black", lw=1.5))

    # Step 402: Read Photodiode Array
    ax.text(50, 80, "READ PHYSICAL ANALOG READOUTS FROM\nLIGHT/UV SENSOR ARRAY [402]", 
            ha='center', va='center', fontsize=8, bbox=box_props)

    # Step 403: Calculate Solar Noise
    ax.text(50, 68, "CALCULATE AMBIENT SOLAR NOISE POWER (P_solar)\nAND ANGULAR SEPARATION (theta) [403]", 
            ha='center', va='center', fontsize=8, bbox=box_props)

    # Decision 404: Noise exceeds threshold?
    draw_diamond(50, 52, 40, 12, "IS P_solar > NOISE\nTHRESHOLD (Th_noise)?", "404")

    # Step 405: Adjust Shutter Opacity
    ax.text(25, 36, "DYNAMICALLY INCREASE OPACITY/\nADJUST SHUTTER STEPS [405]", 
            ha='center', va='center', fontsize=8, bbox=box_props)

    # Step 406: Keep Shutter Open
    ax.text(75, 36, "MAINTAIN MAXIMUM SHUTTER OPACITY\n(FULLY TRANSPARENT STATE) [406]", 
            ha='center', va='center', fontsize=8, bbox=box_props)

    # Decision 407: Solar angle critical?
    draw_diamond(50, 22, 40, 12, "IS ANGULAR SEPARATION (theta) <\nCRITICAL POINTING THRESHOLD?", "407")

    # Step 408: Unaligned Hold State (Shut down / Full block)
    ax.text(22, 8, "ACTIVATE UNALIGNED HOLD:\nSEVER POWER / CLOSE SHUTTER [408]", 
            ha='center', va='center', fontsize=8, bbox=box_props)

    # Step 409: Continue Normal tracking
    ax.text(75, 8, "CONTINUE OPTICAL BEACON\nDATA RECEPTION [409]", 
            ha='center', va='center', fontsize=8, bbox=box_props)

    # Arrow flows
    arrow_props = dict(arrowstyle="->", color="black", lw=1.5)

    ax.annotate("", xy=(50, 83), xytext=(50, 87), arrowprops=arrow_props)
    ax.annotate("", xy=(50, 71), xytext=(50, 77), arrowprops=arrow_props)
    ax.annotate("", xy=(50, 58), xytext=(50, 65), arrowprops=arrow_props)

    # Yes path from 404 to 405
    ax.annotate("", xy=(25, 40), xytext=(30, 52), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=90,angleB=180,rad=0"))
    ax.text(28, 54, "YES", ha='center', va='center', fontsize=8, fontweight='bold')

    # No path from 404 to 406
    ax.annotate("", xy=(75, 40), xytext=(70, 52), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=90,angleB=0,rad=0"))
    ax.text(72, 54, "NO", ha='center', va='center', fontsize=8, fontweight='bold')

    # Paths merging into 407
    ax.annotate("", xy=(40, 22), xytext=(25, 32), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=0,angleB=-90,rad=0"))
    ax.annotate("", xy=(60, 22), xytext=(75, 32), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=0,angleB=-90,rad=0"))

    # Yes path from 407 to 408
    ax.annotate("", xy=(22, 12), xytext=(30, 22), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=90,angleB=180,rad=0"))
    ax.text(28, 24, "YES", ha='center', va='center', fontsize=8, fontweight='bold')

    # No path from 407 to 409
    ax.annotate("", xy=(75, 12), xytext=(70, 22), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=90,angleB=0,rad=0"))
    ax.text(72, 24, "NO", ha='center', va='center', fontsize=8, fontweight='bold')

    # Loop backs to start (feedback)
    ax.annotate("", xy=(50, 93), xytext=(10, 8), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.2, ls=":", connectionstyle="angle,angleA=180,angleB=90,rad=0"))
    ax.annotate("", xy=(50, 93), xytext=(90, 8), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.2, ls=":", connectionstyle="angle,angleA=0,angleB=90,rad=0"))

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
