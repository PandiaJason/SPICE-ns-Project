# On-Board Edge-AI Framework for Autonomous Telemetry Diagnostics and Dynamic Compression in Mars Low Orbit Rover-Relay SmallSats

🚀 **Innovative Operations for Smart and Sustainable Space Mission Management — Next Generation (SMOPS 2026)**

---

## 📌 Introduction

Next-generation deep-space exploration increasingly relies on small satellite (SmallSat) constellations in planetary orbits to act as telecommunication relays for high-value surface assets, such as rovers and landers. In a typical **Mars Low Orbit (MLO) rover-relay scenario**, 3U CubeSats are deployed to collect multi-dimensional scientific data and health parameters from Martian surface platforms, subsequently store-and-forwarding this telemetry to a high-capacity mothership in High Mars Orbit (HMO) or downlinking it directly to Earth. 

However, these interplanetary SmallSats are bound by severe physical constraints:
1. **Extreme Power Limits:** Martian solar irradiance is highly restricted, operating at only $\approx 43\%$ of Earth's solar flux.
2. **Constrained Communication Windows:** Relays have highly intermittent Line-of-Sight (LoS) communication windows, and RF transmission represents the single largest power drain on the spacecraft.
3. **High Signal Latency:** Round-trip communications latency between Mars and Earth (up to 45 minutes) renders ground-in-the-loop Failure Detection, Isolation, and Recovery (FDIR) ineffective for prompt, safety-critical subsystem failures.

To address these challenges, this repository presents a flight-grade, **ultra-lightweight Edge-AI framework** designed to run directly on-board a resource-constrained SmallSat On-Board Computer (OBC). 

### Key Architectural Innovation
The framework integrates an ultra-compact **PyTorch micro-Autoencoder (1,203 parameters, 4.81 KB ROM footprint)** that maps correlations between 31 spacecraft telemetry channels to detect anomalies on the edge. Utilizing a **Dual-Mode Telemetry Compression Strategy**, the system:
* **Mode A (Nominal Operations):** Dynamic suppression of telemetry, transmitting only an ultra-low-overhead 10-byte nominal heartbeat status message, reducing bandwidth utilization.
* **Mode B (Anomalous Operations):** Instantly triggers upon threshold violation ($\tau$), capturing a high-fidelity sliding history buffer (30 pre- and post-trigger samples) that is losslessly compressed (GZIP) and downlinked to give ground operations full diagnostic context of the failure onset.

The framework's performance, stability, and scientific validity are demonstrated via a **50-trial Monte Carlo simulation** under stochastically parameterized physical orbits, eclipse profiles, load dynamics, thermals, sensor noises, and six critical subsystem failures.

---

## 📂 Codebase & Pipeline Structure

The codebase is engineered with modularity and clean software design patterns:

```
SMOPS2026/
│
├── run_pipeline.py          # Master coordinator running the entire pipeline end-to-end
│
├── data_generator.py        # Stage 1: Mars MLO physical modeling & MC telemetry generation
├── train_model.py           # Stage 2: MinMaxScaler fitting, Autoencoder training, & threshold calibration
├── test_model.py            # Stage 3: Real-time edge inference & dual-mode compression execution
├── analyze_performance.py   # Stage 4: Statistical extraction, plot compilation, & micro-benchmarking
│
├── manuscript.tex           # IEEE-compliant academic manuscript (LaTeX)
├── sim_summary.txt          # Saved performance lookup file
│
├── data/                    # Generated datasets (NPZ format for Monte Carlo trials)
├── models/                  # Trained neural network weights (.pth checkpoints)
├── results/                 # Test inference logs and prediction streams (.npz files)
└── figures/                 # Rendered publication-quality figures
```

---

## 🛠️ Detailed Pipeline Stages

### 1. Synthetic Data Generation (`data_generator.py`)
Generates 13-orbit datasets at a 30-second sampling frequency modeling a 3U CubeSat operating in a Mars Low Orbit. It models 31 telemetry variables covering power, thermal, attitude determination and control (ADCS), and computing subsystems.
* **Stochastic Orbits:** Randomizes eclipse durations, peak solar currents, thermal dissipation/conduction constants, and baseline subsystem load cycles.
* **Stochastic Failures:** Stochastically injects six critical subsystem failures:
  1. *Battery Micro-Short Circuit (`volt_drop`)*: Sudden step-down degradation of battery cell voltage.
  2. *Reaction Wheel Lubricant Freeze (`wheel_lock`)*: Increased motor friction and current spike.
  3. *Cosmic-Ray CPU Memory Leak (`cpu_leak`)*: Asymptotic memory consumption due to radiation SEEs.
  4. *Transmitter Power Amplifier cooling failure (`sensor_overheat`)*: Thermal runaway under active communication.
  5. *Magnetorquer Coil Short Circuit (`magnetorquer_short`)*: Sudden voltage drop and magnetic control failure.
  6. *Atmospheric Dust Storm Link Drops (`comms_drop`)*: Packet drops due to severe dust attenuation.

### 2. Model Training (`train_model.py`)
Instantiates the PyTorch micro-Autoencoder and processes the nominal training orbits:
* Standardizes training telemetry using fitted standard scalers.
* Optimizes network weights over 40 epochs.
* Feeds validation orbits to the model and computes the reconstruction Mean Squared Error (MSE). The $99.5^{\text{th}}$ percentile of nominal MSE is calibrated as the edge trigger threshold ($\tau$).

### 3. Edge Inference & Dual-Mode Compression (`test_model.py`)
Loads the trained model checkpoint, processes scaled test telemetry step-by-step, and simulates real-time edge triggers:
* Evaluates reconstruction error at each step and flags anomalies the instant MSE exceeds $\tau$.
* Simulates **Dual-Mode Compression**: Suppresses telemetry transmission during nominal phases (Mode A), and immediately transmits a losslessly compressed (GZIP) sliding history window containing high-fidelity pre/post-failure variables upon anomaly detection (Mode B).

### 4. Statistical Analysis & Benchmarking (`analyze_performance.py`)
Aggregates statistical metrics across all 50 Monte Carlo trials:
* Computes aggregate ROC-AUC, F1-scores, precision, recall, bandwidth savings, and trigger latencies.
* Benchmarks inference footprint, memory consumption, and execution execution times to estimate ARM Cortex-M4 microcontroller performance.
* Renders publication-quality charts and reports.

---

## 🚀 Execution Instructions

Run the master pipeline script to execute the entire simulation sequence from data generation to final analysis:

```bash
python3 run_pipeline.py
```

### Execution Output Snapshot:
```text
=======================================================
🌍 STARTING EDGE-AI TELEMETRY SIMULATION PIPELINE
=======================================================
🚀 RUNNING STAGE: data_generator.py ... ✅ COMPLETE (Duration: 1.15s)
🚀 RUNNING STAGE: train_model.py ...    ✅ COMPLETE (Duration: 69.32s)
🚀 RUNNING STAGE: test_model.py ...     ✅ COMPLETE (Duration: 2.42s)
🚀 RUNNING STAGE: analyze_performance.py ✅ COMPLETE (Duration: 4.86s)

🎉 PIPELINE SUCCESSFUL! All stages completed.
⏱️ Total Pipeline Execution Time: 77.40 seconds
```

---

## 📈 Summary of Monte Carlo Results (50 Trials)

Below is the aggregate performance compiled across all 50 stochastically generated Monte Carlo trials, matching the exact results reported in the academic manuscript:

### Diagnostic & Bandwidth Performance

| Metric | Mean Value | Standard Deviation ($\pm$) | Target Benchmark |
| :--- | :---: | :---: | :---: |
| **ROC-AUC Score** | **0.9749** | $\pm$ 0.0091 | > 0.9000 |
| **F1-Score** | **90.52%** | $\pm$ 5.08% | > 85.00% |
| **Precision** | **90.82%** | $\pm$ 9.04% | — |
| **Recall** | **90.91%** | $\pm$ 1.99% | — |
| **False Alarm Rate (FAR)** | **2.12%** | $\pm$ 3.15% | < 5.00% |
| **Downlink Bandwidth Savings** | **70.10%** | $\pm$ 7.54% | > 50.00% |
| **Bandwidth Compression Factor**| **3.54x** | $\pm$ 0.84x | — |
| **RF-to-Computation Energy Payoff** | **$1.48 \times 10^6$** | — | — |

### Physical Resource Footprint (ARM Cortex-M4 @ 80 MHz Profile)

| Resource Metric | Value | Constraint Status |
| :--- | :---: | :---: |
| **Model Size (Parameter Count)** | **1,203 weights** | Strict SWaP Limit |
| **Estimated ROM Footprint** | **4.81 KB** (4,812 bytes) | Extremely Compliant |
| **Estimated RAM Footprint** | **< 1.5 KB** | Extremely Compliant |
| **Onboard Inference Latency** | **0.377 ms** | Real-time Capable |
| **Active Computation Energy** | **$0.0124\ \mu$J** | $< 0.001\%$ of standard 3U budget |

### Anomaly Detection Latency (Minutes from Onset to Trigger)

| Failure Mode | Target Subsystem | Mean Delay | Max Delay |
| :--- | :--- | :---: | :---: |
| **Battery Cell Micro-Short** | Electrical Power (EPS) | **0.00 mins** | 0.00 mins |
| **Reaction Wheel Lubricant Freeze** | Attitude Control (ADCS) | **0.00 mins** | 0.00 mins |
| **Cosmic-Ray CPU Memory Leak** | Command & Data (CDHS) | **0.00 mins** | 0.00 mins |
| **Transmitter PA Cooling Failure** | Telecommunications | **21.09 mins** | 39.50 mins |
| **Magnetorquer Coil Short** | Attitude Control (ADCS) | **0.00 mins** | 0.00 mins |
| **Atmospheric Dust Storm Link Drop**| Telecommunications | **0.00 mins** | 0.00 mins |

---

## 💬 Discussion

### 1. Edge-AI Feasibility on Low-Power Microcontrollers
The micro-Autoencoder architecture leverages tight physical correlations across 31 telemetry dimensions to compress diagnostic knowledge into just **1,203 trainable parameters**. 
* With a **4.81 KB ROM** and **< 1.5 KB RAM** footprint, this neural network completely eliminates the need for expensive GPU/VPU hardware accelerators (such as the Intel Movidius Myriad 2 or NVIDIA Jetson), enabling native deployment on heritage, radiation-hardened microcontrollers (such as the ARM Cortex-M4 or RISC-V cores).
* An inference latency of **0.377 ms** at 80 MHz ensures real-time tracking with virtually zero CPU overhead, leaving the spacecraft's primary processor fully available for critical GNC (Guidance, Navigation, and Control) and payload operations.

### 2. The Astronomical Energy Payoff Ratio
A crucial contribution of this work is the mathematical quantification of the active energy trade-off between onboard computation and RF communication. 
* Operating an X-band or UHF transmitter on a 3U CubeSat requires approximately **2.0 to 10.0 W** of active power, demanding up to **300,000 $\mu$J** per telemetry packet downlinked.
* In contrast, executing a single inference step of the micro-Autoencoder on an ARM Cortex-M4 requires just **0.0124 $\mu$J** of active energy.
* This yields an astronomical **RF-to-Computation Energy Payoff Ratio of $1.48 \times 10^6 \times$**. For every micro-joule of active electrical energy invested in running AI inference on the edge, the spacecraft saves over 1.48 million micro-joules of battery energy by suppressing nominal, redundant telemetry transmission. This drastically alleviates battery depth-of-discharge stress during challenging Martian winter orbits.

### 3. Rapid Failure Isolation and Ground Impact
Except for the slow-growing thermal anomaly (`sensor_overheat`), the framework achieves **zero-latency detection (0.00 mins delay)** across the battery micro-short, reaction wheel freeze, CPU leak, magnetorquer short, and link drops. 
* By instantly detecting anomalies, the system immediately shifts into Mode B, downlinking the high-fidelity pre-failure buffer before a catastrophic subsystem outage occurs. 
* The **70.10% bandwidth savings** significantly reduces the daily downlinked volume, relieving severe congestion on the NASA/ESA Deep Space Network (DSN) and reducing the active tracking workload of mission operations teams.
* A low **False Alarm Rate (2.12%)** ensures ground operators are not overwhelmed with false failure alerts, directly addressing operator fatigue and enhancing long-term mission reliability.

---

## 📜 Citations and References

For technical details, please consult our SMOPS 2026 manuscript:

* **Title:** *An On-Board Edge-AI Framework for Autonomous Telemetry Diagnostics and Dynamic Compression in Mars Low Orbit Rover-Relay SmallSats*
* **Authors:** Jason Pandian (Nehru Institute of Technology) and I. Kala (Nehru Institute of Technology)
* **Venue:** Proceedings of the Space Mission Operations Symposium (SMOPS), Bengaluru, India, 2026.
