# Tri-Temporal Digital Twin (T3DT)
### A Framework for Predictive Command and Control of Deep-Space Human Exploration Systems

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![HTML5](https://img.shields.io/badge/Dashboard-HTML5%2FJS-orange?logo=html5)](index.html)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Manuscript-Acta%20Astronautica%20(Under%20Review)-purple)](https://www.sciencedirect.com/journal/acta-astronautica)

> **Paper:** *A Tri-Temporal Digital Twin Framework for Predictive Command and Control of Deep-Space Human Exploration Systems*  
> **Authors:** Jason Pandian · Dr. I. Kala  
> **Journal:** Acta Astronautica (Elsevier) — Under Submission  

---

## Overview

Human deep-space exploration missions to Mars face a fundamental operational bottleneck: **round-trip light time (RTLT) delays of 6–44 minutes** render conventional reactive ground control non-viable. By the time Earth receives a telemetry anomaly and transmits a corrective command, the spacecraft state has evolved well beyond the point of safe intervention.

The **Tri-Temporal Digital Twin (T3DT)** framework resolves this by maintaining three synchronized digital representations of the spacecraft simultaneously:

| Twin | Temporal Offset | Purpose |
|---|---|---|
| 🕐 **Past Twin** | $t - \tau$ | Anchored to the latest received telemetry packet |
| 🕑 **Present Twin** | $t$ | Dead-reckoned estimate of the current physical state |
| 🕒 **Future Twin** | $t + \tau$ | Forward projection to the command-arrival epoch |

By bridging these three temporal zones, ground operators can detect anomalies early, predict subsystem violations, and uplink **preemptive corrective commands** that arrive at the spacecraft precisely at the onset of an off-nominal event.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GROUND SEGMENT (Earth)                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  Past Twin   │───▶│ Present Twin │───▶│  Future Twin     │  │
│  │  (t - τ)     │    │     (t)      │    │  (t + τ)         │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│         ▲                                        │              │
│         │ Telemetry (DSN)                        │ Commands     │
│         │              ◄── τ (4–22 min) ──►      ▼ (DSN)       │
└─────────│────────────────────────────────────────│─────────────┘
          │                                        │
┌─────────│────────────────────────────────────────│─────────────┐
│         │        SPACE SEGMENT (Spacecraft)      │              │
│         │                                        ▼              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Physical Spacecraft: Astrodynamics · TCS · EPS · ECLSS  │  │
│  │                State Reconciliation FSM                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

- 🛰️ **Physics-based simulation** — astrodynamics (Mars orbit insertion), thermal control, electrical power, and CO2 life support subsystems
- 🔮 **Tri-temporal state management** — Past, Present, and Future twins with recursive least-squares state reconciliation
- ⚡ **Preemptive commanding** — 4.44% latency reduction by scheduling commands to arrive synchronously with anomaly onset
- 🎯 **88.4% trajectory error reduction** during Mars Orbit Insertion under T3DT vs. conventional reactive control
- 📊 **Interactive dashboard** — real-time browser-based mission control UI with three-pane visualization
- 📈 **12 publication-ready figures** — all generated programmatically from simulation data
- 📉 **Statistically significant safety improvement** — Paired T-test: $p = 3.63 \times 10^{-10}$

---

## Simulation Results

| Metric | Conventional | T3DT | Δ |
|---|---|---|---|
| Avg Safety Margin | 90.07% | 90.17% | **+0.10%** |
| Cabin Thermal Stability (σ) | 0.1843 °C | 0.1468 °C | **−20.3%** |
| Life Support CO₂ Stability (σ) | 0.01413% | 0.01352% | **−4.3%** |
| Final Trajectory Error | 325.85 km | 37.80 km | **−88.4%** |
| Average Command Latency | 8100 s | 7740 s | **−4.44%** |
| Blackout Recovery Time | N/A | < 180 s | ✅ |

---

## Repository Structure

```
Tri-Temporal-Digital-Twin/
├── Simulation/
│   ├── run_all.py            # Main orchestration script — run this first
│   ├── simulator.py          # Core T3DT simulation loop
│   ├── twin.py               # Past/Present/Future twin state management
│   ├── dynamics.py           # Astrodynamics (Mars orbit, Euler-Cromer)
│   ├── thermal.py            # Thermal Control Subsystem (TCS)
│   ├── power.py              # Electrical Power Subsystem (EPS)
│   ├── eclss.py              # CO2 Life Support Subsystem (ECLSS)
│   ├── crew.py               # Crew metabolic and workload models
│   ├── analysis.py           # Statistical validation (Paired T-test)
│   ├── generate_plots.py     # Publication figure generation
│   ├── server.py             # Flask/SSE telemetry server for dashboard
│   ├── telemetry.csv         # Raw simulation telemetry output
│   ├── predictions.csv       # Twin state prediction logs
│   ├── commands.csv          # Uplink command schedule log
│   └── experiment_results.npz # Compressed NumPy results archive
├── index.html                # Interactive mission control dashboard
├── fig_*.pdf / fig_*.png     # 12 publication-ready figures (PDF + PNG)
├── analysis_results.md       # Quantitative validation summary
└── README.md                 # This file
```

> **Note:** The `paper/` directory (LaTeX source, compiled PDFs, Elsevier template files) is excluded from version control via `.gitignore` and is available locally for submission.

---

## Getting Started

### Prerequisites

```bash
pip install numpy scipy matplotlib flask
```

### Run the Simulation

```bash
cd Simulation
python run_all.py
```

This will:
1. Run the 48-hour T3DT mission simulation across all four anomaly scenarios
2. Generate `telemetry.csv`, `predictions.csv`, and `experiment_results.npz`
3. Produce all 12 publication figures in `../paper/figs/` (PDF + PNG)
4. Print the quantitative validation report to stdout

### Launch the Interactive Dashboard

```bash
cd Simulation
python server.py
```

Then open `index.html` in your browser (or navigate to `http://localhost:8000`).

The dashboard provides:
- **Past Twin pane** — historical telemetry playback with ORBIT, TCS, EPS, and ECLSS tabs
- **Present Twin pane** — dead-reckoned current state with live gauges
- **Future Twin pane** — predictive projection with anomaly pre-warning indicators
- **Top bar** — mission elapsed time, DSN link status, and anomaly injection controls
- **Bottom panels** — command transmission log, statistical validation display, and figure viewer

---

## Publication Figures

| Figure | Description |
|---|---|
| `fig_t3dt_architecture` | System architecture and three-twin relationship diagram |
| `fig_t3dt_workflow` | Nine-step operational workflow across ground and space segments |
| `fig_operational_timeline` | 48-hour mission event timeline with anomaly markers |
| `fig_twin_synchronization` | Past/Present/Future twin temperature profiles during anomaly |
| `fig_orbital_trajectory` | Mars orbit insertion: Nominal vs. Conventional vs. T3DT trajectories |
| `fig_thermal_prediction` | TCS cabin temperature prediction accuracy |
| `fig_power_prediction` | EPS battery SOC prediction accuracy |
| `fig_eclss_prediction` | CO2 concentration prediction accuracy |
| `fig_error_convergence` | Prediction error growth during blackout and post-blackout convergence |
| `fig_command_latency` | Command latency comparison (Conventional vs. T3DT) |
| `fig_safety_margin` | Spacecraft safety margin over 48-hour mission |
| `fig_anomaly_response` | Anomaly detection and mitigation speed comparison |

---

## Citation

If you use this work, please cite:

```bibtex
@article{pandian2026t3dt,
  title   = {A Tri-Temporal Digital Twin Framework for Predictive Command 
             and Control of Deep-Space Human Exploration Systems},
  author  = {Pandian, Jason and Kala, I.},
  journal = {Acta Astronautica},
  year    = {2026},
  note    = {Under Review}
}
```

---

## Related Projects

This work is part of the broader **SPICE-ns Deep-Space Communication Research** series:

- 🔗 [VirtualPRB-DS-Communication](../VirtualPRB-DS-Communication/) — Predictive Temporal Bridge (PTB) for Mars ground-spacecraft synchronization
- 🔗 [DTN](../DTN/) — Energy-aware Contact Graph Routing for SmallSat relay networks
- 🔗 [ns-3.47](../ns-3.47/) — SPICE-ns mobility model and Mars DSN propagation simulations

---

## Authors

**Jason Pandian**  
Department of Information Technology, Nehru Institute of Technology, Coimbatore, India  
📧 pandiajason@gmail.com · [ORCID: 0000-0003-1702-5186](https://orcid.org/0000-0003-1702-5186)

**Dr. I. Kala**  
Department of Computer Science and Engineering, PSG Institute of Technology and Applied Research, Coimbatore, India  
[ORCID: 0009-0004-9062-1536](https://orcid.org/0009-0004-9062-1536)

---

*This work is not affiliated with, endorsed by, or conducted on behalf of any space agency or organization.*
