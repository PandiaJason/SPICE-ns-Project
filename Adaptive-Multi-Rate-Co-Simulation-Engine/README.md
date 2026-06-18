# Adaptive Multi-Rate Co-Simulation Engine

This repository contains the source code and simulation engine for evaluating hybrid time-stepping paradigms in deep space network simulations.

## Project Overview

Traditional simulation tools generally fall into two categories: continuous astrodynamics propagators (like GMAT or STK) and discrete-event network simulators (like NS-3 or OMNeT++). When simulating terrestrial networks, the discrete-event paradigm works exceptionally well. However, in relativistic deep space environments, assumptions about instantaneous state changes fail due to:
1. **Temporal Discontinuity**
2. **Light-Time Asymmetry**
3. **Relativistic Clock Bias**

This project demonstrates that combining these domains via Fixed-Step or pure Event-Driven synchronization introduces severe, irreducible simulation errors. To resolve this, we propose and implement an **Adaptive Multi-Rate Co-Simulation** orchestrator. By acting as a predictive zero-crossing detector, the adaptive heuristic contracts the integration step near dynamic physical gradients and expands it during stable phases, successfully bridging the gap between continuous accuracy and discrete efficiency.

## Simulation Benchmark Suite

The custom co-simulation engine evaluates the three synchronization paradigms against three canonical astrodynamical mission profiles:
1. **Mars Occultation (MRO-like):** Tests the engine's ability to handle sharp geometric transitions and atmospheric attenuation boundaries.
2. **Elliptical Doppler (Molniya-class):** Tests the engine's response to dynamic Shannon capacity changes driven by extreme radial velocity gradients near periapsis.
3. **Cislunar NRHO DTN:** Tests long-term Delay-Tolerant Networking (DTN) buffer accumulation over multi-day communication blackouts.

## Directory Structure

*   `simulation/` - Python-based simulation engine and orchestrator.
    *   `generate_data.py` - Generates ground-truth astrodynamics and mission profile data.
    *   `generate_figures.py` - Executes the simulation engine, parses results, and generates graphs.
    *   `data/` - Cached trajectory and profile states.
    *   `graphs/` - Generated output figures.

## Getting Started

### Prerequisites
*   Python 3.8+
*   NumPy, Pandas, Matplotlib, SciPy

### Running the Simulations
To run the simulations and generate the output graphs:

```bash
cd simulation
python3 generate_data.py
python3 generate_figures.py
```

This will run the Fixed-Step, Event-Driven, and Adaptive engines against all three mission profiles and output the execution metrics and graphs.
