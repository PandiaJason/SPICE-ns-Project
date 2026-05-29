# Edge-AI Autonomous Telemetry & Anomaly Pipeline for SMOPS 2026

🚀 **Innovative Operations for Smart and Sustainable Space Mission Management – Next Generation**

This repository contains a modular, flight-grade edge-computing framework designed to execute an ultra-lightweight **PyTorch micro-Autoencoder (118 parameters, 472 Bytes ROM)** directly on resource-constrained satellite On-Board Computers (OBCs). By analyzing multi-subsystem telemetry in real time, the model identifies anomalous states and coordinates a **Dual-Mode Telemetry Compression Strategy** to drastically reduce downlink bandwidth demand on ground stations.

To prove scientific and operational credibility, the framework evaluates the system using a **50-trial Monte Carlo simulation** under stochastically modeled physical fluctuations (eclipse variations, load dynamics, thermals, sensor noises) and failures.

---

## 📂 Codebase & Pipeline Structure

The simulation environment is split into modular, independent scripts representing best software engineering practices:

```
SMOPS2026/
│
├── run_pipeline.py          # Master coordinator that runs the entire sequence
│
├── data_generator.py        # Stage 1: Physical CubeSat LEO modeling & MC dataset generation
├── train_model.py           # Stage 2: MinMax fitting, model training, and threshold calibration
├── test_model.py            # Stage 3: Real-time edge inference & dual-mode compression strategy
├── analyze_performance.py   # Stage 4: Aggregate statistics extraction and plot compilation
│
├── manuscript.tex           # IEEE-compliant academic manuscript LaTeX draft
├── manuscript.pdf           # Compiled publication-ready PDF document
├── sim_summary.txt          # Saved performance lookup text file
│
├── data/                    # Generated datasets (NPZ format)
├── models/                  # Trained neural network weights (.pth checkpoints)
├── results/                 # Test results and prediction streams (.npz logs)
└── figures/                 # Rendered publication-quality figures
```

---

## 🛠️ Pipeline Stages Detail

### 1. Synthetic Data Generation (`data_generator.py`)
Generates 13-orbit datasets at a 10-second sampling frequency modeling a 3U CubeSat Electrical Power System (EPS).
* Stochastically draws Eclipse durations, Solar current peaks, thermal conduction/dissipation scales, and baseline system loads from uniform distributions.
* Injects three dynamic anomalies at randomized indices:
  1. *Battery Cell Short Circuit*: A step-down voltage degradation ($0.6 - 1.1$~V).
  2. *Battery Thermal Runaway*: An asymptotic thermal sensor leak ($18.0 - 32.0^{\circ}\text{C}$).
  3. *Solar Panel Shadowing*: A dynamic solar array current drop to $5\% - 20\%$ normal.
* Outputs 50 independent Monte Carlo trials under `data/monte_carlo/` and a deterministic representative set under `data/representative.npz`.

### 2. Training Model (`train_model.py`)
Instantiates the micro-Autoencoder network and processes the nominal training orbits:
* Fits standard scaler ranges and standardizes training features.
* Optimizes network weights over 40 epochs.
* Feeds validation orbits to the model, and marks the $99.5^{\text{th}}$ percentile of reconstruction MSE as the edge anomaly detection threshold ($\tau$).
* Natively saves weights, active MinMaxScaler instances, and $\tau$ thresholds inside PyTorch `.pth` dictionaries under `models/`.

### 3. Testing Model (`test_model.py`)
Loads trained models, standardizes scaled test telemetry, and simulates real-time edge triggers:
* Calculates reconstruction errors and flags anomalies the instant MSE breaches $\tau$.
* Simulates **Dual-Mode Compression**:
  * *Mode A (Nominal Operations)*: Transmits low-overhead 10-byte status heartbeats.
  * *Mode B (Anomalous Operations)*: Triggers high-priority, lossless GZIP compression of a 30-sample pre/post-trigger historical buffer (capturing high-fidelity diagnostics leading to failure).
* Computes false triggers (FAR), data savings (Bytes), and latency (minutes from onset to trigger).
* Logs results in `.npz` formats under `results/`.

### 4. Analyzing Performance (`analyze_performance.py`)
Loads all trial prediction files and processes the aggregated statistical metrics:
* Compiles ROC-AUC, FAR, and bandwidth compression averages and standard deviations.
* Plots the mean ROC curve with **$\pm 1$ Standard Deviation shaded confidence bands**.
* Generates metric distribution histograms and data footprint bar charts with **statistical error bars**.
* Renders the 3-panel real-time operational dashboard (`anomaly_detection.png`) and validation reconstruction curves.
* Micro-benchmarks inference footprint to estimate low-power ARM Cortex-M4 microcontroller latencies.
* Writes a full statistical report under `sim_summary.txt`.

---

## 🚀 Execution Instructions

To execute the entire simulation pipeline from generation through training, testing, and performance analysis, run the master pipeline script:

```bash
python3 run_pipeline.py
```

### Script Output Snapshot:
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

## 📈 Consolidated Monte Carlo Outcomes (50 Trials)

* **Mean Detection Accuracy (ROC-AUC):** **$0.8528 \pm 0.0679$**
* **Average Data Downlink Bandwidth Savings:** **$87.64\% \pm 8.19\%$** (representing a mean **$11.69\times \pm 5.92\times$** compression factor, easily beating our $80\%$ conference target).
* **False Alarm Rate (FAR):** **$0.42\% \pm 0.58\%$** (ensuring exceptionally clean operational diagnostics and mitigating operator fatigue).
* **Mean Detection Delays (Onset to Edge Trigger):**
  * *Battery Short Circuit ($V_{\text{batt}}$):* **$32.85 \pm 19.54$ mins** (Max: $45.00$ mins)
  * *Thermal Runaway ($T_{\text{batt}}$):* **$28.84 \pm 17.22$ mins** (Max: $45.00$ mins)
  * *Solar Current Obstruction ($I_{\text{solar}}$):* **$40.26 \pm 12.89$ mins** (Max: $45.00$ mins)
* **Estimated Microcontroller Footprint (ARM Cortex-M4 @ 80 MHz):**
  * *ROM Flash Memory:* **472 Bytes** (118 parameters)
  * *RAM Dynamic Memory:* **< 1.2 KB**
  * *Inference Latency:* **$0.377$ ms**
  * *Active Energy per Step:* **$0.0125\ \mu$J** (represents less than $0.01\%$ of standard 3U CubeSat power budgets, proving extreme mission sustainability).
