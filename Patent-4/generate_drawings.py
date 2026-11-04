import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Global patent drawing style: clean black and white, crisp lines, standard fonts
plt.rcParams['text.color'] = 'black'
plt.rcParams['axes.labelcolor'] = 'black'
plt.rcParams['xtick.color'] = 'black'
plt.rcParams['ytick.color'] = 'black'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']

def draw_figure_1():
    """FIG. 1: Tri-Temporal Digital Twin (T3DT) System Architecture across DSN Latency"""
    fig, ax = plt.subplots(figsize=(11, 8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 80)
    ax.axis('off')

    ax.text(50, 77, "FIG. 1: TRI-TEMPORAL DIGITAL TWIN (T3DT) SYSTEM ARCHITECTURE", 
            ha='center', va='center', fontsize=11, fontweight='bold')

    box_props = dict(boxstyle="square,pad=0.6", fc="white", ec="black", lw=1.5)
    inner_box = dict(boxstyle="square,pad=0.4", fc="white", ec="black", lw=1.0)

    # 100 Ground Station Segment (Earth)
    ground_boundary = patches.Rectangle((4, 8), 38, 64, fill=False, edgecolor='black', linewidth=1.8, linestyle='--')
    ax.add_patch(ground_boundary)
    ax.text(23, 69, "GROUND MISSION CONTROL (100)\n(EARTH SEGMENT)", ha='center', va='center', fontsize=9, fontweight='bold')

    # Ground Components
    ax.text(23, 58, "DSN Ground Transceiver\n& Ingress FIFO (102)", ha='center', va='center', fontsize=8, bbox=inner_box)
    ax.text(23, 42, "GROUND TRI-TEMPORAL\nPROCESSING UNIT (T3PU) (104)\n[Past (t-\u03c4) | Present (t) | Future (t+\u03c4)]\n- Residual Matrix Engine\n- Physics Acceleration Core", 
            ha='center', va='center', fontsize=7.5, bbox=box_props)
    ax.text(23, 24, "Preemptive Command Synthesizer\n& Epoch Comparator (106)", ha='center', va='center', fontsize=8, bbox=inner_box)
    ax.text(23, 13, "Mission Operations HMI &\nSituational Display (108)", ha='center', va='center', fontsize=8, bbox=inner_box)

    # Internal Ground Connections
    arrow_props = dict(arrowstyle="->", color="black", lw=1.3)
    ax.annotate("", xy=(23, 50), xytext=(23, 54), arrowprops=arrow_props)
    ax.annotate("", xy=(23, 29), xytext=(23, 34), arrowprops=arrow_props)
    ax.annotate("", xy=(23, 17), xytext=(23, 20), arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))

    # 200 Spacecraft Segment (Deep Space / Mars)
    space_boundary = patches.Rectangle((58, 8), 38, 64, fill=False, edgecolor='black', linewidth=1.8, linestyle='--')
    ax.add_patch(space_boundary)
    ax.text(77, 69, "CREWED EXPLORATION VEHICLE (200)\n(SPACE SEGMENT - MARS VICINITY)", ha='center', va='center', fontsize=9, fontweight='bold')

    # Spacecraft Components
    ax.text(77, 58, "Deep Space Comm Transceiver\n& Telemetry Packager (202)", ha='center', va='center', fontsize=8, bbox=inner_box)
    ax.text(77, 42, "CABIN RECONCILIATION\nARBITER (CRA) CHIP (204)\n- Ingress Command FIFO\n- Real-time Sensor Sampling\n- Dual-Gate Hardware FSM", 
            ha='center', va='center', fontsize=7.5, bbox=box_props)
    ax.text(77, 24, "Hardware Actuator Interlocks &\nSwitching Drivers (206)", ha='center', va='center', fontsize=8, bbox=inner_box)
    ax.text(77, 13, "Physical Spacecraft Subsystems (208)\n[TCS Valves | EPS Relays | ECLSS | RCS]", ha='center', va='center', fontsize=7.5, bbox=inner_box)

    # Internal Spacecraft Connections
    ax.annotate("", xy=(77, 50), xytext=(77, 54), arrowprops=arrow_props)
    ax.annotate("", xy=(77, 29), xytext=(77, 34), arrowprops=arrow_props)
    ax.annotate("", xy=(77, 17), xytext=(77, 20), arrowprops=arrow_props)

    # DSN Channel & Latencies (300)
    ax.text(50, 61, "Deep Space Network (DSN)\nInterplanetary Propagation Channel (300)", ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Preemptive Command (Down to Spacecraft)
    ax.annotate("", xy=(58, 55), xytext=(42, 55), arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
    ax.text(50, 56.5, "Preemptive Command c(t+\u03c4)\n(Transit Delay \u03c4)", ha='center', va='center', fontsize=7)

    # Telemetry (Back to Ground)
    ax.annotate("", xy=(42, 47), xytext=(58, 47), arrowprops=dict(arrowstyle="->", color="black", lw=1.5, ls="--"))
    ax.text(50, 44.5, "Asynchronous Telemetry x(t)\n(Arrives at t+\u03c4 as Past Twin)", ha='center', va='center', fontsize=7)

    # Temporal Math Legend
    ax.text(50, 32, "Round-Trip Light Time (RTLT) = 2\u03c4\nEffective Operational Latency = 0 s\nVia Preemptive Arrival at t_exec = t+\u03c4", 
            ha='center', va='center', fontsize=7.5, style='italic', bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="black", lw=1.0, ls=":"))

    plt.tight_layout()
    plt.savefig('figure_1.png', bbox_inches='tight', facecolor='white')
    plt.close()

def draw_figure_2():
    """FIG. 2: Ground Tri-Temporal Processing Unit (T3PU) Hardware Architecture"""
    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 85)
    ax.axis('off')

    ax.text(50, 82, "FIG. 2: GROUND TRI-TEMPORAL PROCESSING UNIT (T3PU) HARDWARE ARCHITECTURE", 
            ha='center', va='center', fontsize=11, fontweight='bold')

    # Main T3PU Boundary
    chip_border = patches.Rectangle((6, 6), 88, 73, fill=False, edgecolor='black', linewidth=2.0)
    ax.add_patch(chip_border)
    ax.text(50, 76, "TRI-TEMPORAL PROCESSING UNIT (T3PU) CO-PROCESSOR ASIC / FPGA (104)", 
            ha='center', va='center', fontsize=9.5, fontweight='bold')

    box_props = dict(boxstyle="square,pad=0.5", fc="white", ec="black", lw=1.3)
    reg_props = dict(boxstyle="square,pad=0.4", fc="white", ec="black", lw=1.0)

    # 1. Tri-Temporal Register Bank (400)
    ax.text(26, 67, "TRI-TEMPORAL REGISTER BANK (400)", ha='center', va='center', fontsize=8.5, fontweight='bold')
    ax.text(14, 58, "PAST TWIN\nREGISTER (402)\nState x(t-\u03c4)\n[Telemetry Anchor]", ha='center', va='center', fontsize=7.5, bbox=reg_props)
    ax.text(26, 58, "PRESENT TWIN\nREGISTER (404)\nState x(t)\n[Dead-Reckoned Now]", ha='center', va='center', fontsize=7.5, bbox=reg_props)
    ax.text(38, 58, "FUTURE TWIN\nREGISTER (406)\nState x(t+\u03c4)\n[Target at Uplink]", ha='center', va='center', fontsize=7.5, bbox=reg_props)

    # 2. Residual Matrix Engine (410)
    ax.text(72, 63, "RESIDUAL MATRIX ENGINE (410)\nHardware Residual Adder: e(t-\u03c4) = x_actual - x_pred\nParameter Calibration MAC Pipeline:\n\u03b8_k = \u03b8_{k-1} + K \u00b7 e(t-\u03c4)\n[\u03b5_rad, E_batt, \u03b7_scrub, F_thrust]", 
            ha='center', va='center', fontsize=7.5, bbox=box_props)

    # Interconnect between Past Register and Residual Matrix Engine
    ax.annotate("", xy=(56, 63), xytext=(45, 63), arrowprops=dict(arrowstyle="<->", color="black", lw=1.3))

    # 3. Physics Simulation Acceleration Core (PSAC) (420)
    psac_border = patches.Rectangle((10, 22), 80, 26, fill=False, edgecolor='black', linewidth=1.5, linestyle='-.')
    ax.add_patch(psac_border)
    ax.text(50, 45, "PHYSICS SIMULATION ACCELERATION CORE (PSAC) (420) - HARDWIRED PARALLEL ODE SOLVERS", 
            ha='center', va='center', fontsize=8.5, fontweight='bold')

    ax.text(20, 32, "Astrodynamics Pipeline (422)\n\u00a8r = -(\u03bc/|r|\u00b3)r + a_thrust\nOrbit & Hyperbolic Escape\nRunge-Kutta 4 Hardware", 
            ha='center', va='center', fontsize=7, bbox=box_props)
    ax.text(40, 32, "Thermal Balance Pipeline (424)\nC_cab(dT/dt) = Q_dot_in - \u03b7_rad\u00b7Q_rad\nRadiator & Avionics Node\nEuler/RK Hardware Integrator", 
            ha='center', va='center', fontsize=7, bbox=box_props)
    ax.text(60, 32, "Power Dynamics Pipeline (426)\nd(SOC)/dt = (\u03b7/E)(P_arr - P_load)\nBattery Degradation Model\nDynamic Load Shedding Calc", 
            ha='center', va='center', fontsize=7, bbox=box_props)
    ax.text(80, 32, "ECLSS Kinetics Pipeline (428)\nV(dC_CO2/dt) = m_gen - \u03b7_scrub\u00b7m_scrub\nCabin Volume Metabolic Flux\nScrubber Clogging Integrator", 
            ha='center', va='center', fontsize=7, bbox=box_props)

    # Interconnects from PSAC to Register Bank & Residual Engine
    ax.annotate("", xy=(26, 51), xytext=(26, 48), arrowprops=dict(arrowstyle="<->", color="black", lw=1.3))
    ax.annotate("", xy=(72, 51), xytext=(72, 48), arrowprops=dict(arrowstyle="<->", color="black", lw=1.3))

    # 4. Bottom Row: Ingress Telemetry FIFO, Preemptive Command Synthesizer, DSN Bus
    ax.text(22, 13, "DSN Telemetry Ingress FIFO\n& Protocol Packet De-serializer (430)", ha='center', va='center', fontsize=7.5, bbox=box_props)
    ax.text(50, 13, "Preemptive Command Synthesizer\n& Hardware Epoch Comparator (432)", ha='center', va='center', fontsize=7.5, bbox=box_props)
    ax.text(78, 13, "System Bus & Host Interface (434)\n[PCIe / AXI-4 / SpaceWire to Control HMI]", ha='center', va='center', fontsize=7.5, bbox=box_props)

    ax.annotate("", xy=(22, 22), xytext=(22, 18), arrowprops=dict(arrowstyle="->", color="black", lw=1.3))
    ax.annotate("", xy=(50, 22), xytext=(50, 18), arrowprops=dict(arrowstyle="<-", color="black", lw=1.3))
    ax.annotate("", xy=(78, 22), xytext=(78, 18), arrowprops=dict(arrowstyle="<->", color="black", lw=1.3))

    plt.tight_layout()
    plt.savefig('figure_2.png', bbox_inches='tight', facecolor='white')
    plt.close()

def draw_figure_3():
    """FIG. 3: Onboard Cabin Reconciliation Arbiter (CRA) Hardware Architecture"""
    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 85)
    ax.axis('off')

    ax.text(50, 82, "FIG. 3: ONBOARD CABIN RECONCILIATION ARBITER (CRA) HARDWARE ARCHITECTURE", 
            ha='center', va='center', fontsize=11, fontweight='bold')

    chip_border = patches.Rectangle((6, 6), 88, 73, fill=False, edgecolor='black', linewidth=2.0)
    ax.add_patch(chip_border)
    ax.text(50, 76, "CABIN RECONCILIATION ARBITER (CRA) RADIATION-HARDENED ASIC (204)", 
            ha='center', va='center', fontsize=9.5, fontweight='bold')

    box_props = dict(boxstyle="square,pad=0.5", fc="white", ec="black", lw=1.3)
    inner_box = dict(boxstyle="square,pad=0.4", fc="white", ec="black", lw=1.0)

    # Ingress Uplink Command Port
    ax.text(22, 66, "UPLINK COMMAND RECEIVER (502)\nDemux & Header Parsing\nExtracts c(t+\u03c4), \u03c4, & T_pred(t+\u03c4)", 
            ha='center', va='center', fontsize=7.5, bbox=box_props)

    # Real-time Sensor Sampling Engine
    ax.text(78, 66, "REAL-TIME SENSOR SAMPLING (504)\nDirect ADC / Sensor Bus Interface\nSamples T_actual(t_arr)\n[Cabin Temp, Batt SOC, CO2%, Gyro]", 
            ha='center', va='center', fontsize=7.5, bbox=box_props)

    # Dual-Gate Hardware Threshold Comparator
    ax.text(50, 50, "DUAL-GATE HARDWARE THRESHOLD COMPARATOR (506)\nParallel Subtraction: \u0394_k = |T_actual,k(t_arr) - T_pred,k(t_arr)|\nDynamic Safety Envelope Evaluator: |\u0394_k| \u2264 \u03b4_{safe,k}\nAUTH = \u2227_{k=1}^N (|\u0394_k| \u2264 \u03b4_{safe,k})", 
            ha='center', va='center', fontsize=8, bbox=dict(boxstyle="square,pad=0.6", fc="white", ec="black", lw=1.5))

    ax.annotate("", xy=(36, 52), xytext=(30, 60), arrowprops=dict(arrowstyle="->", color="black", lw=1.3))
    ax.annotate("", xy=(64, 52), xytext=(70, 60), arrowprops=dict(arrowstyle="->", color="black", lw=1.3))

    # Dynamic Safety Threshold Register Bank
    ax.text(50, 67, "Dynamic Safety Envelope Register Bank (508)\n[\u03b4_TCS = 4.0\u00b0C | \u03b4_EPS = 14.0 kWh | \u03b4_ECLSS = 0.16% | \u03b4_traj]", 
            ha='center', va='center', fontsize=7, bbox=inner_box)
    ax.annotate("", xy=(50, 56), xytext=(50, 62), arrowprops=dict(arrowstyle="->", color="black", lw=1.2))

    # Hardware FSM Logic Block
    ax.text(50, 34, "REALITY RECONCILIATION FINITE STATE MACHINE (FSM) (510)\nDeterministic Hardware State Logic: IDLE \u2192 INGRESS \u2192 COMPARE \u2192 GATED", 
            ha='center', va='center', fontsize=8, bbox=box_props)
    ax.annotate("", xy=(50, 39), xytext=(50, 44), arrowprops=dict(arrowstyle="->", color="black", lw=1.3))

    # Dual Outputs: Validated Actuation vs Desync Alarm
    ax.text(25, 20, "ACTUATOR DRIVER INTERLOCK (512)\nHardwired Actuation Pulses:\n- Auxiliary Cooling Boost Relay\n- Non-essential Load Shedding\n- Backup CO2 Scrubber Switch\n- RCS Thruster Gimbal Actuator", 
            ha='center', va='center', fontsize=7.5, bbox=box_props)

    ax.text(75, 20, "ANOMALY VETO & CREW OVERRIDE (514)\nHardware Veto Flag & Inhibit\nCrew HMI Audio/Visual Alarm\nProtects against Automation Bias\nRequests Manual Crew Inspection", 
            ha='center', va='center', fontsize=7.5, bbox=box_props)

    ax.annotate("", xy=(28, 26), xytext=(42, 31), arrowprops=dict(arrowstyle="->", color="black", lw=1.3))
    ax.text(32, 30, "AUTH = 1 (Valid)", ha='center', va='center', fontsize=7)

    ax.annotate("", xy=(72, 26), xytext=(58, 31), arrowprops=dict(arrowstyle="->", color="black", lw=1.3))
    ax.text(68, 30, "AUTH = 0 (Violation)", ha='center', va='center', fontsize=7)

    # Universal Avionics Bus Interface
    ax.text(50, 10, "UNIVERSAL AEROSPACE BUS INTERFACE (516) [SpaceWire / MIL-STD-1553 / CAN Bus]", 
            ha='center', va='center', fontsize=8, fontweight='bold', bbox=inner_box)
    ax.annotate("", xy=(35, 12), xytext=(25, 15), arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.annotate("", xy=(65, 12), xytext=(75, 15), arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))

    plt.tight_layout()
    plt.savefig('figure_3.png', bbox_inches='tight', facecolor='white')
    plt.close()

def draw_figure_4():
    """FIG. 4: Reality Reconciliation Finite State Machine (FSM) State Transitions"""
    fig, ax = plt.subplots(figsize=(10.5, 8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 80)
    ax.axis('off')

    ax.text(50, 77, "FIG. 4: REALITY RECONCILIATION FINITE STATE MACHINE (FSM) STATE TRANSITIONS", 
            ha='center', va='center', fontsize=11, fontweight='bold')

    def draw_state(x, y, r, label, state_num):
        circle = patches.Circle((x, y), r, fill=True, facecolor='white', edgecolor='black', linewidth=1.8)
        ax.add_patch(circle)
        ax.text(x, y + 2.5, label, ha='center', va='center', fontsize=7.5, fontweight='bold')
        ax.text(x, y - 2, f"STATE [{state_num}]", ha='center', va='center', fontsize=7, style='italic')

    # States
    draw_state(16, 50, 10, "IDLE /\nSTANDBY", "602")
    draw_state(38, 50, 10, "COMMAND\nINGRESS", "604")
    draw_state(62, 50, 10, "DEVIATION\nEVALUATION", "606")
    draw_state(86, 62, 10, "RECONCILED\nACTUATION", "608")
    draw_state(86, 34, 10, "DESYNCED\nVETO / HOLD", "610")

    # Transitions
    arrow_props = dict(arrowstyle="->", color="black", lw=1.4)

    # 602 -> 604
    ax.annotate("", xy=(28, 50), xytext=(26, 50), arrowprops=arrow_props)
    ax.text(32, 53, "Packet Arrival\nat t_arr = t+\u03c4", ha='center', va='center', fontsize=7)

    # 604 -> 606
    ax.annotate("", xy=(52, 50), xytext=(48, 50), arrowprops=arrow_props)
    ax.text(55, 53, "Sensor Sample\nRead Latched", ha='center', va='center', fontsize=7)

    # 606 -> 608 (Reconciled)
    ax.annotate("", xy=(77, 58), xytext=(70, 54), arrowprops=arrow_props)
    ax.text(71, 62, "\u2200 k, |\u0394_k| \u2264 \u03b4_{safe,k}\n(AUTH = 1)", ha='center', va='center', fontsize=7)

    # 606 -> 610 (Desynced)
    ax.annotate("", xy=(77, 40), xytext=(70, 45), arrowprops=arrow_props)
    ax.text(71, 37, "\u2203 k, |\u0394_k| > \u03b4_{safe,k}\n(AUTH = 0)", ha='center', va='center', fontsize=7)

    # Return paths back to IDLE
    ax.annotate("", xy=(16, 40), xytext=(86, 24), arrowprops=dict(arrowstyle="->", color="black", lw=1.2, ls="--"))
    ax.text(50, 18, "Actuation Complete OR Manual Crew Override Resolved \u2192 Return to IDLE", ha='center', va='center', fontsize=7.5)

    # Hardware Timing Annotation
    ax.text(50, 8, "Deterministic Hardware Execution Timing: Total Transition Time T_eval < 5.0 \u03bcs\nZero Overhead on Primary Spacecraft Flight Computer Cycles", 
            ha='center', va='center', fontsize=7.5, bbox=dict(boxstyle="square,pad=0.5", fc="white", ec="black", lw=1.0))

    plt.tight_layout()
    plt.savefig('figure_4.png', bbox_inches='tight', facecolor='white')
    plt.close()

def draw_figure_5():
    """FIG. 5: Spacecraft Avionics Network Integration Diagram"""
    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 85)
    ax.axis('off')

    ax.text(50, 82, "FIG. 5: SPACECRAFT AVIONICS NETWORK INTEGRATION", 
            ha='center', va='center', fontsize=11, fontweight='bold')

    box_props = dict(boxstyle="square,pad=0.5", fc="white", ec="black", lw=1.3)
    inner_box = dict(boxstyle="square,pad=0.4", fc="white", ec="black", lw=1.0)

    # Primary Flight Computer (702)
    ax.text(50, 68, "SPACECRAFT PRIMARY FLIGHT COMPUTER (PFC) (702)\n(Guidance, Navigation & Basic Sequencing - Offloaded from AI Twin)", 
            ha='center', va='center', fontsize=8, bbox=box_props)

    # Shared Avionics Bus (704)
    ax.plot([10, 90], [50, 50], color="black", lw=2.5)
    ax.text(50, 53, "DUAL-REDUNDANT SPACEWIRE / MIL-STD-1553 AVIONICS BUS (704)", ha='center', va='center', fontsize=8.5, fontweight='bold')

    # Interconnect PFC to Bus
    ax.annotate("", xy=(50, 51), xytext=(50, 62), arrowprops=dict(arrowstyle="<->", color="black", lw=1.4))

    # Peripheral Nodes Connected to Bus
    # 1. Sensors (706)
    ax.text(18, 36, "TELEMETRY SENSORS (706)\n- Thermistors (T_cabin)\n- Battery Volts/Amps\n- CO2 Infrared Analyzers\n- IMU / Gyroscopes", 
            ha='center', va='center', fontsize=7, bbox=inner_box)
    ax.annotate("", xy=(18, 49), xytext=(18, 42), arrowprops=dict(arrowstyle="->", color="black", lw=1.3))

    # 2. DSN Radio Receiver (708)
    ax.text(38, 36, "DEEP SPACE RADIO (708)\nX/Ka-Band Transponder\nReceives c(t+\u03c4)\nTransmits x(t) Telemetry", 
            ha='center', va='center', fontsize=7, bbox=inner_box)
    ax.annotate("", xy=(38, 49), xytext=(38, 42), arrowprops=dict(arrowstyle="<->", color="black", lw=1.3))

    # 3. Cabin Reconciliation Arbiter (CRA) (204)
    ax.text(62, 36, "CABIN RECONCILIATION\nARBITER (CRA) CHIP (204)\nHardware Reality Gating\nZero CPU Cycle Robbing", 
            ha='center', va='center', fontsize=7.5, bbox=box_props)
    ax.annotate("", xy=(62, 49), xytext=(62, 42), arrowprops=dict(arrowstyle="<->", color="black", lw=1.4))

    # 4. Crew HMI (710)
    ax.text(84, 36, "CREW INTERFACE (710)\nCommander Cockpit Touchscreen\nAudit Trails & Override Buttons\nSituational Awareness Display", 
            ha='center', va='center', fontsize=7, bbox=inner_box)
    ax.annotate("", xy=(84, 49), xytext=(84, 42), arrowprops=dict(arrowstyle="<->", color="black", lw=1.3))

    # Physical Actuator Circuits directly coupled to CRA (720)
    ax.text(50, 16, "PHYSICAL SPACECRAFT ACTUATOR SUBSYSTEMS & SWITCHING RELAYS (720)", ha='center', va='center', fontsize=8.5, fontweight='bold')
    
    act_border = patches.Rectangle((12, 6), 76, 15, fill=False, edgecolor='black', linewidth=1.2, linestyle=':')
    ax.add_patch(act_border)

    ax.text(22, 11, "Auxiliary Cooling\nPump Relay (722)", ha='center', va='center', fontsize=7, bbox=inner_box)
    ax.text(40, 11, "Non-Essential Load\nShedding Breaker (724)", ha='center', va='center', fontsize=7, bbox=inner_box)
    ax.text(60, 11, "Backup ECLSS CO2\nScrubber Valve (726)", ha='center', va='center', fontsize=7, bbox=inner_box)
    ax.text(78, 11, "RCS Gimbal Thruster\nActuator Driver (728)", ha='center', va='center', fontsize=7, bbox=inner_box)

    # Direct Hardwired Actuation Interlock line from CRA to Actuators
    ax.annotate("", xy=(50, 21), xytext=(62, 30), arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
    ax.text(59, 24, "Hardwired Interlock Actuation Signals", ha='center', va='center', fontsize=7, fontweight='bold')

    plt.tight_layout()
    plt.savefig('figure_5.png', bbox_inches='tight', facecolor='white')
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
    print("Generating Figure 5...")
    draw_figure_5()
    print("All 5 patent drawing figures generated successfully in black and white!")
