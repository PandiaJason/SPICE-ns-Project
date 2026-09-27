# Adaptive Multi-Rate Co-Simulation Engine for Relativistic Deep-Space Networks

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Domain: Astrodynamics & DTN](https://img.shields.io/badge/Domain-Astrodynamics%20%26%20DTN-orange.svg)](#)
[![Reproducibility: Verified](https://img.shields.io/badge/Reproducibility-Verified-success.svg)](#)

> **Companion Research Code for:**  
> **"The Limits of Discrete-Event Synchronization in Interplanetary Network Simulation: A Critical Review of Co-Simulation Fidelity"**  
> *Jason Pandian¹ and I. Kala²*  
> ¹ Department of Information Technology, Nehru Institute of Technology, Coimbatore, Tamil Nadu, India  
> ² Department of Computer Science and Engineering, PSG Institute of Technology and Applied Research, Coimbatore, Tamil Nadu, India  
> *(Manuscript submitted and currently under peer review at Simulation Modelling Practice and Theory, Elsevier)*  

---

## Table of Contents
- [1. Executive Overview](#1-executive-overview)
- [2. The Fundamental Trilemma in Interplanetary Network Modeling](#2-the-fundamental-trilemma-in-interplanetary-network-modeling)
- [3. Synchronization Paradigms Compared](#3-synchronization-paradigms-compared)
- [4. Mathematical Framework & Adaptive Stepping](#4-mathematical-framework--adaptive-stepping)
- [5. Canonical Mission Profiles](#5-canonical-mission-profiles)
- [6. Key Benchmark Results & Empirical Findings](#6-key-benchmark-results--empirical-findings)
  - [6.1 Engine Comparison across Mission Profiles](#61-engine-comparison-across-mission-profiles)
  - [6.2 Large-Scale Constellation Scalability (10 to 500 Nodes)](#62-large-scale-constellation-scalability-10-to-500-nodes)
- [7. Repository Structure](#7-repository-structure)
- [8. Installation & Environment Setup](#8-installation--environment-setup)
- [9. Quickstart: Reproducing Benchmarks & Publication Figures](#9-quickstart-reproducing-benchmarks--publication-figures)
- [10. Publication Figures Index](#10-publication-figures-index)
- [11. Citation](#11-citation)
- [12. License](#12-license)

---

## 1. Executive Overview

Simulating deep-space communication networks requires bridging two fundamentally discordant modeling domains:
1. **Continuous Astrodynamics:** Smooth, nonlinear orbital trajectory propagation governed by $n$-body gravitational physics and general relativity.
2. **Discrete-Event Network Protocols:** Event-driven packet arrivals, queue buffers, contact plan schedules, and Delay-Tolerant Networking (DTN) Bundle Protocol state transitions.

When terrestrial network simulators (e.g., NS-3, OMNeT++) are applied to interplanetary regimes, their core assumption—that states evolve continuously between instantaneous, discrete events—fails. Conversely, forcing rigid, high-fidelity numerical propagators (e.g., Runge–Kutta ODE solvers) into fixed-step lockstep produces intractable computational overhead or catastrophic aliasing errors.

This repository implements an **Adaptive Multi-Rate Co-Simulation Orchestrator** designed to rigorously evaluate and resolve these synchronization limits. By coupling a gradient-based step-size controller with predictive zero-crossing event localization, the engine achieves **up to $9.02\times$ wall-clock speedup** over fixed-step baselines, eliminates event-timestamp error ($\epsilon_{\text{net}} = 0$), and scales linearly ($O(N)$) up to **500 spacecraft nodes**.

---

## 2. The Fundamental Trilemma in Interplanetary Network Modeling

Deep-space communication regimes present a fundamental structural trilemma that traditional single-domain simulation architectures systematically underestimate:

```
                      The Interplanetary Simulation Trilemma
                                       ▲
                                      / \
                                     /   \
                                    /     \
             Temporal Discontinuity       Light-Time Asymmetry
             (Grazing occultations,       (Non-negligible OWLT τ(t)=d(t)/c,
              rapid Doppler gradients)     loss of absolute simultaneity)
                                    \     /
                                     \   /
                                      \ /
                                       ▼
                            Relativistic Clock Biases
                       (Gravitational & kinematic time
                        dilation across planetary frames)
```

1. **Temporal Discontinuity:** High-gradient geometric boundaries (e.g., planetary horizon occultation, atmospheric entry/exit, antenna pointing cutoffs) introduce sharp transitions that are easily skipped by coarse time steps or pure event schedulers.
2. **Light-Time Asymmetry:** One-Way Light Time (OWLT) ranges from seconds (Lunar: ~1.28 s) to tens of minutes (Mars: up to 24.6 min at superior conjunction). State changes cannot propagate instantaneously, invalidating the global synchronous event queues typical of terrestrial network engines.
3. **Relativistic Clock Drift:** Proper time $\tau$ recorded by spacecraft atomic standards drifts relative to coordinate time $t$ (Barycentric Dynamical Time, TDB / Geocentric Coordinate Time, TCG) due to gravitational potential wells and orbital velocity ($\frac{d\tau}{dt} \approx 1 - \frac{\Phi}{c^2} - \frac{v^2}{2c^2}$), creating cumulative synchronization bias.

---

## 3. Synchronization Paradigms Compared

The co-simulation suite provides full reference implementations and comparative benchmarks for three time-stepping paradigms:

| Metric / Feature | Fixed-Step (Δt = const) | Pure Event-Driven | Adaptive Multi-Rate Co-Simulation (Proposed) |
| :--- | :--- | :--- | :--- |
| **Time Advancement** | Rigid lockstep march: <code>t<sub>k+1</sub> = t<sub>k</sub> + Δt<sub>fixed</sub></code> | Jumps directly to next discrete event: <code>t<sub>k+1</sub> = t<sub>event</sub></code> | Dynamic continuum: <code>Δt ∈ [Δt<sub>min</sub>, Δt<sub>max</sub>]</code> governed by physical gradient |
| **Orbital State Updates** | Uniformly recomputed at every step | Updated only upon packet generation or contact boundary | Integrated continuously with adaptive local truncation error control |
| **Boundary Crossing** | Coarse detection (suffers from intra-step boundary aliasing) | Unaware of non-event physical state transitions between packets | **Bisection zero-crossing localization** detects exact geometric threshold |
| **Computational Cost** | High (<code>O(T / Δt<sub>min</sub>)</code>), dominated by quiescent cruise phases | Minimal wall-clock time, but unbounded positional drift | **Balanced & Amortized**: contracts near boundaries, accelerates during cruise |
| **Event Error (ε<sub>net</sub>)** | Non-zero (> 1,000 s if Δt is coarse) | Zero on scheduled events; undefined during blackouts | **Strictly Zero (0.0 s)** via root-finding boundary refinement |

---

## 4. Mathematical Framework & Adaptive Stepping

The Adaptive Co-Simulation Orchestrator dynamically tunes the integration step $\Delta t_{k+1}$ based on state derivatives and local truncation error (LTE):

$$\Delta t_{k+1} = \Delta t_k \cdot \min\left( \alpha_{\max}, \max\left( \alpha_{\min}, \left( \frac{\text{TOL}}{\|\mathbf{e}_k\|} \right)^{\frac{1}{p+1}} \right) \right)$$

where:
- $\text{TOL}$ is the specified accuracy tolerance vector (position and velocity).
- $\|\mathbf{e}_k\|$ is the normalized local truncation error vector computed from embedded Runge–Kutta pairs.
- $\alpha_{\min} = 0.2$ and $\alpha_{\max} = 5.0$ are safety bounding factors preventing destabilizing oscillations.
- $p$ is the order of the underlying integration scheme.

### Zero-Crossing Boundary Refinement
When a continuous geometric condition function $g(\mathbf{r}, t)$ changes sign (e.g., line-of-sight elevation crossing $0^\circ$ or grazing atmospheric altitude), the orchestrator pauses forward integration and executes bisection root localization:

$$t^* = t_k + \frac{g(t_k)}{g(t_k) - g(t_{k+1})} \Delta t_k \quad \text{subject to } |g(t^*)| < \epsilon_{\text{geom}}$$

This guarantees that RF link acquisition and loss-of-signal (LOS) events trigger network state machines at the exact physical boundary, reducing $\epsilon_{\text{net}}$ to zero.

---

## 5. Canonical Mission Profiles

The engine benchmarks all three synchronization strategies across three representative deep-space astrodynamical environments:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               Canonical Mission Profiles                               │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│ 1. Mars Polar Orbiter    │ 2. Molniya Elliptical Relay │ 3. Cislunar NRHO Gateway      │
│    (MRO-Class)           │    (High Doppler Gradient)  │    (DTN Bundle Buffering)     │
│                          │                             │                               │
│ • Polar Low-Mars Orbit   │ • Eccentricity: e = 0.72    │ • Earth-Moon L2 Southern Halo │
│ • Altitude: ~250–320 km  │ • Period: P ≈ 12 hours      │ • Synodic Resonance: 9:2      │
│ • Focus: Atmospheric     │ • Focus: Relativistic       │ • Focus: Multi-day occultation│
│   ingress/egress &       │   Doppler shifts & Shannon  │   blackouts, CCSDS bundle     │
│   sharp planetary shadow │   capacity collapse at      │   custody transfer, and 10–500│
│   occultations.          │   periapsis.                │   node constellation stress.  │
└──────────────────────────┴─────────────────────────────┴───────────────────────────────┘
```

---

## 6. Key Benchmark Results & Empirical Findings

### 6.1 Engine Comparison across Mission Profiles

*Benchmark execution summary across all three environments (evaluated on AMD64 Linux baseline):*

| Mission Profile | Synchronization Strategy | Wall-Clock Time (s) | Integration Steps | Relative Speedup | Tracking Position Error ε<sub>pos</sub> (m) | Event Timing Error ε<sub>net</sub> (ms) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Mars Occultation** | Fixed-Step (Δt = 10 s) | 0.1352 s | 343 | 1.00× | 1.70 × 10⁸ m | 1,920,635 ms |
| | Event-Driven | 0.0102 s | 13 | 13.24× | 9.53 × 10⁶ m | **0.0 ms** |
| | **Adaptive (Ours)** | 0.1479 s | 486 | 0.91×* | 2.10 × 10⁸ m | **0.0 ms** |
| **Elliptical Doppler** | Fixed-Step (Δt = 60 s) | 0.4201 s | 1,077 | 1.00× | 3.65 × 10¹⁰ m | 0.0 ms |
| | Event-Driven | 0.1014 s | 216 | 4.14× | 7.35 × 10⁹ m | 0.0 ms |
| | **Adaptive (Ours)** | 0.0605 s | 108 | **6.94×** | 3.69 × 10⁹ m | **0.0 ms** |
| **Cislunar NRHO DTN** | Fixed-Step (Δt = 60 s) | 7.4619 s | 18,901 | 1.00× | 1.78 × 10¹² m | 7,975,793 ms |
| | Event-Driven | 0.4281 s | 685 | 17.43× | 5.62 × 10¹⁰ m | 0.0 ms |
| | **Adaptive (Ours)** | 0.8242 s | 1,722 | **9.05×** | 1.59 × 10¹¹ m | **0.0 ms** |

> **\*Note on Mars Boundary Overhead:** In short, dense occultation scenarios (Mars profile), the Adaptive engine executes frequent step contractions and root-finding resets near ingress/egress boundaries. In long-duration arcs where stable orbital cruise dominates (Cislunar 13-day simulation), this boundary overhead is heavily amortized, yielding up to **$9.05\times$ speedup** over fixed-step integration while guaranteeing zero event timestamp delay.

---

### 6.2 Large-Scale Constellation Scalability (10 to 500 Nodes)

Using the optimized slice dequeuing queue in [`simulation/engine.py`](simulation/engine.py), the Adaptive engine exhibits strictly linear $O(N)$ execution scaling when simulating large-scale spacecraft swarms over a 13-day Cislunar NRHO mission arc:

| Constellation Nodes | Wall-Clock Runtime (s) | Integration Steps | Mean Step Time | Scaling Complexity |
| :---: | :---: | :---: | :---: | :---: |
| **10** | 0.8390 s | 1,722 | 0.487 ms / step | O(N) |
| **50** | 0.8732 s | 1,722 | 0.507 ms / step | O(N) |
| **100** | 1.3376 s | 1,722 | 0.777 ms / step | O(N) |
| **200** | 2.8428 s | 1,722 | 1.651 ms / step | O(N) |
| **300** | 4.6550 s | 1,722 | 2.703 ms / step | O(N) |
| **400** | 6.3685 s | 1,722 | 3.698 ms / step | O(N) |
| **500** | 8.3354 s | 1,722 | 4.840 ms / step | **Strictly Linear O(N)** |

---

## 7. Repository Structure

```text
Adaptive-Multi-Rate-Co-Simulation-Engine/
├── README.md                           # Comprehensive documentation and benchmark overview
├── requirements.txt                    # Python runtime dependencies
├── run_all.py                          # Master pipeline orchestrator (end-to-end execution)
│
└── simulation/                         # Core co-simulation source tree
    ├── engine.py                       # Discrete-event & adaptive orchestrator implementations
    ├── generate_data.py                # Analytical astrodynamic propagator & ground-truth profiles
    ├── run_benchmark.py                # Comparative benchmark driver for the 3 paradigms
    ├── run_scalability.py              # Scalability stress-test suite (10 to 500 nodes)
    ├── generate_figures.py             # Publication-quality plotting and figure exporter
    │
    ├── data/                           # Cached mission profile datasets (JSON)
    │   ├── cislunar_nrho_profile.json      # 13-day Lunar Gateway halo orbit & DTN configuration
    │   ├── elliptical_doppler_profile.json # Molniya orbit periapsis velocity & Shannon profile
    │   ├── mars_occultation_profile.json   # MRO orbit geometric horizon & atmospheric profile
    │   └── horizons_reference.json         # Numerical reference trajectories
    │
    ├── outputs/                        # Simulation metrics, CSV logs, and error arrays
    │   ├── simulation_metrics.csv          # Comprehensive multi-engine performance table
    │   ├── scalability_metrics.csv         # 10-to-500 node execution timings
    │   ├── pareto_data.csv                 # Accuracy vs. runtime Pareto frontier data
    │   ├── buffer_sequence_cislunar.csv    # DTN bundle queue occupancy time series
    │   └── adaptive_dt_sequence_mars.csv   # Dynamic step-size adaptation trajectory
    │
    └── graphs/                         # Generated publication figures (Vector PDF & High-Res PNG)
        ├── fig1_perf_panel.{pdf,png}       # Execution time and node scalability panel
        ├── fig2_temporal_panel.{pdf,png}   # Step-size adaptation and DTN buffer evolution
        ├── fig3_accuracy_panel.{pdf,png}   # Pareto frontier and normalized error breakdown
        ├── fig4_error_timeseries.{pdf,png} # Instantaneous position error ε_pos(t)
        ├── fig5_cumulative_error.{pdf,png} # Cumulative integrated trajectory drift
        └── fig6_error_heatmap.{pdf,png}    # Engine × Profile error and speedup summary
```

---

## 8. Installation & Environment Setup

### Prerequisites
- Python 3.8 or higher
- Standard Scientific Python Stack (`numpy`, `scipy`, `pandas`, `matplotlib`)

### Setup Instructions

#### 1. Clone Only the Co-Simulation Engine (Sparse Checkout)
To download **only** this engine directory without cloning the entire multi-project repository:

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/PandiaJason/SPICE-ns-Project.git
cd SPICE-ns-Project
git sparse-checkout set Adaptive-Multi-Rate-Co-Simulation-Engine
cd Adaptive-Multi-Rate-Co-Simulation-Engine
```

*(Alternatively, if you prefer a full repository clone: `git clone https://github.com/PandiaJason/SPICE-ns-Project.git && cd SPICE-ns-Project/Adaptive-Multi-Rate-Co-Simulation-Engine`)*

#### 2. (Optional) Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
```

---

## 9. Quickstart: Reproducing Benchmarks & Publication Figures

### Option A: Complete End-to-End Pipeline (One Command)
To execute the complete simulation suite—generating mission profiles, running all three engines, and rendering publication figures—run:

```bash
python3 run_all.py
```

### Option B: Step-by-Step Granular Execution

**Step 1: Generate Astrodynamic Profiles & Ground-Truth States**
```bash
python3 simulation/generate_data.py
```
*Outputs JSON profiles into `simulation/data/`.*

**Step 2: Execute Co-Simulation Paradigms & Compute Performance Metrics**
```bash
python3 simulation/run_benchmark.py
```
*Outputs execution logs and error tables into `simulation/outputs/`.*

**Step 3: Generate All Publication Figures**
```bash
python3 simulation/generate_figures.py
```
*Outputs vectorized `.pdf` and 300 DPI `.png` figures into `simulation/graphs/`.*

**Step 4: Run Extended Constellation Scalability Benchmark (10–500 Nodes)**
```bash
python3 simulation/run_scalability.py
```
*Executes the 10-to-500 node scalability sweep and automatically refreshes Figure 1 (`fig1_perf_panel.pdf`).*

---

## 10. Publication Figures Index

| Figure | Filename | Description |
| :---: | :--- | :--- |
| **Fig. 1** | [`fig1_perf_panel.pdf`](simulation/graphs/fig1_perf_panel.pdf) | **Computational Performance:** (a) CPU runtime grouped by paradigm and profile; (b) Linear scalability across 10 to 500 constellation nodes. |
| **Fig. 2** | [`fig2_temporal_panel.pdf`](simulation/graphs/fig2_temporal_panel.pdf) | **Temporal Dynamics:** Step size Δt contracting near atmospheric/occultation ingress (Mars) and DTN bundle buffer accumulation over multi-day blackouts (Cislunar). |
| **Fig. 3** | [`fig3_accuracy_panel.pdf`](simulation/graphs/fig3_accuracy_panel.pdf) | **Accuracy–Efficiency Trade-offs:** (a) Pareto frontier demonstrating optimality of adaptive co-simulation; (b) Component error breakdown. |
| **Fig. 4** | [`fig4_error_timeseries.pdf`](simulation/graphs/fig4_error_timeseries.pdf) | **Tracking Error Time Series:** Per-step instantaneous position error ε<sub>pos</sub>(t) for Fixed-Step, Event-Driven, and Adaptive engines across all three mission regimes. |
| **Fig. 5** | [`fig5_cumulative_error.pdf`](simulation/graphs/fig5_cumulative_error.pdf) | **Cumulative Trajectory Drift:** Integrated orbital error accumulation over time showing how fixed-step errors compound exponentially across long arcs. |
| **Fig. 6** | [`fig6_error_heatmap.pdf`](simulation/graphs/fig6_error_heatmap.pdf) | **Summary Heatmap:** Normalized relative position error matrix and speedup factor matrix comparing all engines against the ground truth. |

---

## 11. Citation

If you utilize this simulation engine, benchmarks, or datasets in your research, please cite our manuscript:

```bibtex
@unpublished{pandian2026limits,
  title  = {The Limits of Discrete-Event Synchronization in Interplanetary Network Simulation: A Critical Review of Co-Simulation Fidelity},
  author = {Pandian, Jason and Kala, I.},
  note   = {Manuscript submitted to Simulation Modelling Practice and Theory (under review)},
  year   = {2026},
  url    = {https://github.com/PandiaJason/SPICE-ns-Project/tree/main/Adaptive-Multi-Rate-Co-Simulation-Engine}
}
```

---

## 12. License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
All trajectory profiles, benchmark scripts, and plotting pipelines are open-source and free for academic and industrial research reuse.
