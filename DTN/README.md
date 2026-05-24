# ECGR: Energy and Capacity-Aware Contact Graph Routing for Deep Space SmallSat Relays

A complete simulation and analysis framework for evaluating the proposed ECGR routing algorithm against standard CGR in a Mars deep-space DTN relay network.

## Project Structure

```
DTN/
├── simulation/           # Core simulation package
│   ├── config.py         # All simulation parameters
│   ├── models.py         # Contact, Node, Bundle, Route models
│   ├── spice_data.py     # Synthetic SPICE ephemeris generator
│   ├── contact_plan.py   # Contact plan generator (+ ION-DTN export)
│   ├── routing.py        # CGR and ECGR routing algorithms
│   └── simulator.py      # Discrete-time simulation engine
├── run_simulation.py     # Part 1: Run Monte Carlo simulations
├── analyze_results.py    # Part 2: Generate IEEE-quality figures/tables
├── results/              # Simulation output (JSON, ION-DTN format)
├── figures/              # Generated figures (PDF + PNG) and LaTeX tables
├── paper/                # LaTeX manuscript
│   ├── main.tex          # Full IEEE two-column paper
│   └── references.bib    # Bibliography
└── requirements.txt      # Python dependencies
```

## Quick Start

### 1. Install Dependencies
```bash
pip install numpy matplotlib
```

### 2. Run Simulation (Part 1)
```bash
python3 run_simulation.py --runs 10 --seed 42
```
This produces:
- `results/simulation_results.json` — Aggregate & per-run metrics
- `results/detailed_timeseries.json` — Full time-series data
- `results/contact_plan.json` — Contact plan
- `results/contact_plan.ionrc` — ION-DTN compatible contact plan
- `results/spice_ephemeris.json` — Synthetic SPICE data

### 3. Generate Figures & Tables (Part 2)
```bash
python3 analyze_results.py --input results --output figures
```
Produces 8 IEEE-quality figures (PDF + PNG) and 3 LaTeX tables.

### 4. Compile Paper
```bash
cd paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Network Scenario

4-node Mars relay network:
- **Node 0**: Mars Surface Rover (Jezero Crater) — data source
- **Node 1**: SmallSat Relay (3U CubeSat, 400 km orbit) — resource bottleneck
- **Node 2**: Mars Reconnaissance Orbiter (300 km orbit) — heavy relay
- **Node 3**: NASA Deep Space Network (Earth) — destination

## Key Results

| Metric | CGR | ECGR |
|--------|-----|------|
| Bundle Delivery Ratio | ~90% | ~76% |
| Bundles Dropped | ~0.8 | **0** |
| SmallSat Min SoC | ~50% | ~53% |
| SmallSat Avg SoC | ~79% | **~85%** |
| SmallSat <20% Time | ~1.1% | **0%** |

ECGR trades slightly lower delivery ratio (due to deferred routing) for **zero bundle drops** and significantly better SmallSat energy sustainability.
