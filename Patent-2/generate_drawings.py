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
    """Generates Figure 1: System Architecture of the Laser ISL Wake-on-Beacon IoT Switch"""
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 75)
    ax.axis('off')

    # Draw title
    ax.text(50, 72, "FIG. 1: ASYNCHRONOUS OPTICAL WAKE-UP SYSTEM BLOCK DIAGRAM", 
            ha='center', va='center', fontsize=12, fontweight='bold')

    # Box properties for patent line drawings (white fill, black border, 1.5 line width)
    box_props = dict(boxstyle="square,pad=0.5", fc="white", ec="black", lw=1.5)
    dashed_box_props = dict(boxstyle="square,pad=0.5", fc="white", ec="black", lw=1.5, ls="--")

    # Ground Station / Mother-craft
    ax.text(12, 50, "OPTICAL BEACON\nTRANSMITTER\n(GS / PARENT-CRAFT)\n[101]", ha='center', va='center', fontsize=9, bbox=box_props)

    # Satellite Boundary
    satellite_group = patches.Rectangle((27, 8), 65, 52, fill=False, edgecolor='black', linestyle='--', linewidth=1.5)
    ax.add_patch(satellite_group)
    ax.text(60, 57, "SPACECRAFT / CUBESAT BOUNDARY [104]", ha='center', va='center', fontsize=10, fontweight='bold')

    # Wide-Angle Photodiode
    ax.text(42, 45, "WIDE-ANGLE\nPHOTODIODE\n(WAKE-UP SENSOR)\n[105]", ha='center', va='center', fontsize=8, bbox=box_props)

    # Ultra Low Power IoT Microcontroller (nRF Series)
    ax.text(68, 45, "ULTRA-LOW-POWER\nIoT MICROCONTROLLER\n(nRF52/nRF53 SERIES)\n[106]", ha='center', va='center', fontsize=8, fontweight='bold', bbox=box_props)

    # Transistor Power Gate (MOSFET Switch)
    ax.text(68, 25, "SOLID-STATE\nTRANSISTOR POWER GATE\n(P-CH MOSFET SWITCH)\n[107]", ha='center', va='center', fontsize=8, bbox=box_props)

    # Primary Power Bus / Battery
    ax.text(42, 25, "PRIMARY POWER BUS\n/ BATTERY\n[110]", ha='center', va='center', fontsize=8, bbox=box_props)

    # Main High-Speed Optical Transceiver
    ax.text(82, 18, "MAIN HIGH-SPEED\nOPTICAL DATA\nTRANSCEIVER\n[108]", ha='center', va='center', fontsize=8, bbox=box_props)

    # Fine-Pointing Mirror Systems
    ax.text(82, 33, "FINE-POINTING\nMIRROR ACTUATION\nSYSTEMS [109]", ha='center', va='center', fontsize=8, bbox=box_props)

    # Connective arrows
    arrow_props = dict(arrowstyle="->", color="black", lw=1.5)
    dashed_arrow_props = dict(arrowstyle="->", color="black", lw=1.5, ls=":")

    # Laser pulse beacon propagation
    ax.annotate("", xy=(32, 45), xytext=(22, 50), arrowprops=arrow_props)
    ax.text(26, 49, "Modulated Wake-up\nLaser Pulse [102]", ha='center', va='center', fontsize=7)

    # Photodiode output to ULP MCU
    ax.annotate("", xy=(56, 45), xytext=(50, 45), arrowprops=arrow_props)
    
    # ULP MCU to Power Gate control line
    ax.annotate("", xy=(68, 30), xytext=(68, 38), arrowprops=arrow_props)
    ax.text(63, 34, "Gate Drive\nSignal", ha='center', va='center', fontsize=7)

    # Power Bus to Power Gate input
    ax.annotate("", xy=(58, 25), xytext=(50, 25), arrowprops=arrow_props)

    # Power Gate output to Main transceiver (gated power rail)
    ax.annotate("", xy=(73, 20), xytext=(73, 22), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=0,angleB=-90,rad=0"))
    ax.text(78, 24, "Gated Power\nRail [111]", ha='center', va='center', fontsize=7)

    # Power Gate output to Mirror systems
    ax.annotate("", xy=(77, 33), xytext=(73, 22), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=0,angleB=-90,rad=0"))

    # Main high speed data transceiver returning data
    ax.annotate("", xy=(16, 55), xytext=(88, 23), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.2, ls="-.", connectionstyle="angle,angleA=-90,angleB=180,rad=0"))
    ax.text(50, 62, "High-Speed Data Inter-Satellite Link (ISL) Beam [103]", ha='center', va='center', fontsize=8, fontweight='bold')

    plt.tight_layout()
    plt.savefig('figure_1.png', bbox_inches='tight', facecolor='white')
    plt.close()

def draw_figure_2():
    """Generates Figure 2: Detailed Electronic Schematic & Interface Layout"""
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 75)
    ax.axis('off')

    # Draw title
    ax.text(50, 72, "FIG. 2: ELECTRONIC SCHEMATIC & WAKE-UP INTERFACE CIRCUITS", 
            ha='center', va='center', fontsize=12, fontweight='bold')

    box_props = dict(boxstyle="square,pad=0.5", fc="white", ec="black", lw=1.5)

    # Analog Front-End Blocks
    ax.text(18, 60, "WIDE-ANGLE\nPHOTODIODE [201]", ha='center', va='center', fontsize=8, bbox=box_props)
    ax.text(18, 46, "TRANSIMPEDANCE\nAMPLIFIER (TIA) [202]", ha='center', va='center', fontsize=8, bbox=box_props)
    ax.text(18, 32, "LOW-POWER\nBANDPASS FILTER & \nPULSE SHAPER [203]", ha='center', va='center', fontsize=8, bbox=box_props)
    ax.text(18, 18, "THRESHOLD COMPARATOR\n(ZERO-CROSSING/LEVEL) [204]", ha='center', va='center', fontsize=8, bbox=box_props)

    # ULP IoT Microcontroller (nRF Series) Boundary
    mcu_box = patches.Rectangle((37, 12), 34, 52, fill=False, edgecolor='black', linewidth=2.0)
    ax.add_patch(mcu_box)
    ax.text(54, 61, "ULP IoT MCU (nRF52) [205]", ha='center', va='center', fontsize=9, fontweight='bold')

    ax.text(54, 48, "LOW-POWER PERIPHERAL\nINTERFACE (GPIOTE/PPI)\n[206]", ha='center', va='center', fontsize=8, bbox=box_props)
    ax.text(54, 34, "PATTERN RECOGNITION &\nDECODING LOGIC (FSM)\n[207]", ha='center', va='center', fontsize=8, bbox=box_props)
    ax.text(54, 20, "GPIO OUTPUT CONTROL\nREGISTER / PIN [208]", ha='center', va='center', fontsize=8, bbox=box_props)

    # Actuator & Load Blocks
    ax.text(88, 20, "POWER MOSFET SWITCH\n(P-CHANNEL GATING) [209]", ha='center', va='center', fontsize=8, bbox=box_props)
    ax.text(88, 48, "MAIN HIGH-SPEED\nOPTICAL TRANSCEIVER [210]", ha='center', va='center', fontsize=8, bbox=box_props)

    # Connection lines
    arrow_props = dict(arrowstyle="->", color="black", lw=1.5)

    # Photodiode to TIA
    ax.annotate("", xy=(18, 50), xytext=(18, 56), arrowprops=arrow_props)
    # TIA to Bandpass
    ax.annotate("", xy=(18, 36), xytext=(18, 42), arrowprops=arrow_props)
    # Bandpass to Comparator
    ax.annotate("", xy=(18, 22), xytext=(18, 28), arrowprops=arrow_props)
    
    # Comparator output to MCU GPIOTE (Hardware interrupt)
    ax.annotate("", xy=(37, 48), xytext=(18, 14), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=0,angleB=-90,rad=0"))
    ax.text(28, 30, "Digitized\nPulse Train", ha='center', va='center', fontsize=7)

    # GPIOTE to Pattern FSM
    ax.annotate("", xy=(54, 38), xytext=(54, 44), arrowprops=arrow_props)
    # FSM to GPIO output
    ax.annotate("", xy=(54, 24), xytext=(54, 30), arrowprops=arrow_props)

    # GPIO output to Power MOSFET gate (Crosses out of MCU boundary)
    ax.annotate("", xy=(78, 20), xytext=(65, 20), arrowprops=arrow_props)
    ax.text(71, 23, "Gate Control\nPin", ha='center', va='center', fontsize=7)

    # MOSFET Gated output to main optical transceiver load
    ax.annotate("", xy=(88, 44), xytext=(88, 24), arrowprops=arrow_props)
    ax.text(94, 34, "Gated Power\nInput [211]", ha='center', va='center', fontsize=7)

    # Battery direct power input to MOSFET drain
    ax.annotate("", xy=(88, 10), xytext=(88, 16), arrowprops=dict(arrowstyle="<-", color="black", lw=1.5))
    ax.text(94, 11, "V_BATTERY", ha='center', va='center', fontsize=7)

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
    def draw_state(x, y, r, label, state_num, power_spec):
        circle = patches.Circle((x, y), r, fill=True, facecolor='white', edgecolor='black', linewidth=2.0)
        ax.add_patch(circle)
        ax.text(x, y + 2, label, ha='center', va='center', fontsize=8, fontweight='bold')
        ax.text(x, y - 1, f"STATE [{state_num}]", ha='center', va='center', fontsize=7.5, style='italic')
        ax.text(x, y - 4, power_spec, ha='center', va='center', fontsize=7, color='grey', fontweight='bold')

    # Draw States
    draw_state(20, 48, 10, "ASYNCHRONOUS\nDEEP SLEEP", "301", "< 1 uW")
    draw_state(50, 48, 10, "BEACON PREAMBLE\nDETECTION", "302", "< 10 uW")
    draw_state(80, 48, 10, "TRANSCEIVER BOOT\n& POWER RAIL UP", "303", "Full Power")
    draw_state(50, 18, 10, "ACTIVE ISL DATA\nSESSION", "304", "Active Link")

    arrow_props = dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="arc3,rad=0.15")
    arrow_props_rev = dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="arc3,rad=0.15")

    # Transition 301 -> 302: Optical pulse interrupt detected
    ax.annotate("", xy=(39, 49), xytext=(31, 49), arrowprops=arrow_props)
    ax.text(35, 54, "Optical Pulse\nInterrupt [T31]", ha='center', va='center', fontsize=7.5)

    # Transition 302 -> 301: Pattern mismatch / False alarm
    ax.annotate("", xy=(31, 47), xytext=(39, 47), arrowprops=arrow_props_rev)
    ax.text(35, 41, "Pattern Mismatch/\nTimeout [T32]", ha='center', va='center', fontsize=7.5)

    # Transition 302 -> 303: Hardware pattern validated
    ax.annotate("", xy=(69, 49), xytext=(61, 49), arrowprops=arrow_props)
    ax.text(65, 54, "Unique Beacon Key\nValidated [T33]", ha='center', va='center', fontsize=7.5)

    # Transition 303 -> 304: Boot complete & Alignment achieved
    ax.annotate("", xy=(69, 27), xytext=(78, 39), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="arc3,rad=0.1"))
    ax.text(78, 31, "Boot & Alignment\nComplete [T35]", ha='center', va='center', fontsize=7.5)

    # Transition 304 -> 301: Communication complete / Timeout / Shutdown Command
    ax.annotate("", xy=(22, 39), xytext=(41, 16), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="arc3,rad=0.1"))
    ax.text(26, 25, "Session Complete/\nTimeout [T34]", ha='center', va='center', fontsize=7.5)

    # Transition 304 -> 301: Link failure / Pointing lost
    ax.annotate("", xy=(25, 41), xytext=(43, 19), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, ls=":", connectionstyle="arc3,rad=-0.1"))
    ax.text(39, 29, "Critical Link Loss\nFailsafe [T36]", ha='center', va='center', fontsize=7, style='italic')

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
    ax.text(50, 97, "FIG. 4: LOW-POWER OPTICAL WAKE-ON-BEACON METHODOLOGY", 
            ha='center', va='center', fontsize=12, fontweight='bold')

    box_props = dict(boxstyle="square,pad=0.4", fc="white", ec="black", lw=1.5)

    # Custom function to draw diamond
    def draw_diamond(x, y, w, h, text, step_num):
        pts = [(x, y+h/2), (x+w/2, y), (x, y-h/2), (x-w/2, y)]
        poly = patches.Polygon(pts, fill=True, facecolor='white', edgecolor='black', linewidth=1.5)
        ax.add_patch(poly)
        ax.text(x, y + 0.5, text, ha='center', va='center', fontsize=8)
        ax.text(x, y - h/2 - 2, f"STEP [{step_num}]", ha='center', va='center', fontsize=7, style='italic')

    # Start Node
    ax.text(50, 90, "START: ENTER ASYNCHRONOUS DEEP SLEEP STATE [401]\n(GATING MOSFET OPEN; MAIN TRANSCEIVER OFF)", 
            ha='center', va='center', fontsize=8, bbox=dict(boxstyle="round4,pad=0.5", fc="white", ec="black", lw=1.5))

    # Step 402: Listen asynchronously
    ax.text(50, 80, "ASYNCHRONOUSLY LISTEN: PHOTODIODE CAPTURES BEACON ENVELOPE [402]", 
            ha='center', va='center', fontsize=8, bbox=box_props)

    # Step 403: Hardware comparison
    ax.text(50, 70, "COMPARE INCOMING SIGNAL AMPLITUDE WITH THRESHOLD [403]\n(HARDWARE INT TRIGGERS MCU WAKE)", 
            ha='center', va='center', fontsize=8, bbox=box_props)

    # Decision 404: Pulse present?
    draw_diamond(50, 56, 36, 10, "IS ENVELOPE VOLTAGE\n> NOISE THRESHOLD?", "404")

    # Step 405: Demodulate Pattern
    ax.text(50, 42, "DEMODULATE LOW-FREQUENCY PULSE TRAIN [405]\n(PROCESS DATA ENVELOPE PATTERN ON ULP CORE)", 
            ha='center', va='center', fontsize=8, bbox=box_props)

    # Decision 406: Pattern matches key?
    draw_diamond(50, 29, 36, 10, "DOES PATTERN MATCH\nUNIQUE WAKE BEACON KEY?", "406")

    # Step 407: Trip Power Gate
    ax.text(20, 16, "TRIP GATING MOSFET:\nTOGGLE GPIO CONTROL PIN HIGH [407]", 
            ha='center', va='center', fontsize=8, bbox=box_props)

    # Step 408: Boot Main Transceiver
    ax.text(20, 6, "BOOT HIGH-SPEED TRANSCEIVER\nAND SYNC ALIGNMENT MIRRORS [408]", 
            ha='center', va='center', fontsize=8, bbox=box_props)

    # Step 409: Active Session
    ax.text(68, 6, "CONDUCT HIGH-SPEED DATA INTER-SATELLITE\nCOMMUNICATION LINK SESSION [409]", 
            ha='center', va='center', fontsize=8, bbox=box_props)

    # Decision 410: Complete or Timeout?
    draw_diamond(68, 22, 36, 10, "SESSION TERMINATION\nOR WATCHDOG TIMEOUT?", "410")

    # Step 411: Severe power & return to sleep
    ax.text(80, 42, "TOGGLE GPIO CONTROL LOW:\nSEVER GATING TRANSISTOR POWER\nRE-ENTER DEEP SLEEP [411]", 
            ha='center', va='center', fontsize=8, bbox=box_props)

    # Arrow flows
    arrow_props = dict(arrowstyle="->", color="black", lw=1.5)

    ax.annotate("", xy=(50, 83), xytext=(50, 87), arrowprops=arrow_props)
    ax.annotate("", xy=(50, 73), xytext=(50, 77), arrowprops=arrow_props)
    ax.annotate("", xy=(50, 61), xytext=(50, 67), arrowprops=arrow_props)

    # Yes path from 404 to 405
    ax.annotate("", xy=(50, 45), xytext=(50, 51), arrowprops=arrow_props)
    ax.text(52, 48, "YES", ha='left', va='center', fontsize=8, fontweight='bold')

    # No path from 404 to 411
    ax.annotate("", xy=(72, 42), xytext=(68, 56), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=90,angleB=0,rad=0"))
    ax.text(69, 58, "NO", ha='center', va='center', fontsize=8, fontweight='bold')

    # Yes path from 406 to 407
    ax.annotate("", xy=(32, 16), xytext=(32, 29), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=180,angleB=-90,rad=0"))
    ax.text(28, 27, "YES", ha='center', va='center', fontsize=8, fontweight='bold')

    # No path from 406 to 411
    ax.annotate("", xy=(72, 42), xytext=(68, 29), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=0,angleB=-90,rad=0"))
    ax.text(71, 27, "NO", ha='center', va='center', fontsize=8, fontweight='bold')

    # Step 407 to 408
    ax.annotate("", xy=(20, 9), xytext=(20, 13), arrowprops=arrow_props)

    # Step 408 to 409
    ax.annotate("", xy=(50, 6), xytext=(38, 6), arrowprops=arrow_props)

    # Step 409 to 410
    ax.annotate("", xy=(68, 17), xytext=(68, 9), arrowprops=arrow_props)

    # Yes path from 410 to 411
    ax.annotate("", xy=(80, 39), xytext=(86, 22), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=90,angleB=180,rad=0"))
    ax.text(88, 24, "YES", ha='center', va='center', fontsize=8, fontweight='bold')

    # No path from 410 to 409 (loop back)
    ax.annotate("", xy=(50, 6), xytext=(50, 22), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="angle,angleA=180,angleB=90,rad=0"))
    ax.text(47, 24, "NO", ha='center', va='center', fontsize=8, fontweight='bold')

    # From 411 back to START/401 loop
    ax.annotate("", xy=(50, 93), xytext=(97, 42), 
                arrowprops=dict(arrowstyle="->", color="black", lw=1.2, ls=":", connectionstyle="angle,angleA=90,angleB=0,rad=0"))

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
