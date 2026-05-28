# Weather-Resilient Martian LoRaWAN Simulation & Research Pipeline

[![Language](https://img.shields.io/badge/Language-Python%203.8+-blue.svg)](https://www.python.org/)
[![Compilation](https://img.shields.io/badge/LaTeX-Tectonic%20%7C%20pdfTeX-brightgreen.svg)](https://tectonic-typesetting.github.io/)
[![AeroSpace](https://img.shields.io/badge/Domain-Martian%20IoT%20%26%20Nanosatellites-orange.svg)](https://github.com/)

An advanced, cross-layer physical-MAC event-driven network simulator and comprehensive academic research pipeline. This project models, simulates, and evaluates the performance of Long Range Wide Area Networks (LoRaWAN) in the hostile Martian environment, comparing standard terrestrial configurations against our **Proposed Martian-Optimized Architecture** (utilizing 433 MHz UHF bands, space-grade Low-Noise Amplifiers (LNAs), active TCXO temperature compensation, and RF-transparent hydrophobic antenna coatings).

---

## 🪐 1. Martian Environmental Challenges & Mitigation Model

Operating wireless sensor networks on Mars introduces major physical-layer degradations that do not exist on Earth:

1. **Extreme Diurnal Temperature Cycles**: Mars experiences temperature swings from **$140\text{ K}$ (night)** to **$280\text{ K}$ (day)**. This causes:
   - **Dynamic Thermal Noise Floor**: Fluctuating thermal noise density ($N_0 = k_B T$), making demodulation sensitivity dynamic rather than static.
   - **TCXO Frequency Drift**: Standard Temperature Compensated Crystal Oscillators experience significant frequency offsets, causing packet demodulation failures when drift exceeds $25\%$ of the bandwidth.
2. **Charged Dust Storms**: Martian dust storms attenuate the radio signal through scattering and absorption. Regolith accumulation also forms a thick dust coating on transceiver antennas, introducing massive impedance mismatches (modeled as a $4\text{ dB}$ loss penalty on both ends).
3. **Severe Geological Path Loss**: The lack of liquid water in Martian regolith results in poor surface reflectivity, increasing path loss exponents ($\eta \approx 3.5$) and log-normal shadowing standard deviations ($\sigma \approx 8\text{ dB}$).

<img width="1024" height="1024" alt="martian_lorawan_topology" src="https://github.com/user-attachments/assets/cbfd2d6e-3fe7-4264-9489-b083a3642ef5" />
The Simulated Martian LoRaWAN Scenario Topology.

### The Proposed Weather-Resilient Model
To counter these Martian physical challenges, this framework introduces and evaluates:
* **UHF 433 MHz Band Shift**: Leveraging longer wavelengths to reduce Rayleigh frequency-squared scattering by a factor of 16 and lower path loss exponents.
* **Low-Loss Tangent RF-Transparent Coating**: A protective hydrophobic nanostructured dome that mitigates dust accumulation losses from $4.0\text{ dB}$ to less than $0.5\text{ dB}$.
* **Active TCXO Compensation**: Frequency correction keeping drift well below $0.5\text{ ppm}$ ($216.5\text{ Hz}$ at $433\text{ MHz}$), completely eliminating clock-drift packet drops.
* **Aggressive ADR Safety Margin**: Expanding the Adaptive Data Rate margin to $12\text{ dB}$ to cushion against dynamic diurnal noise shifts and rapid dust fading.

---

## 📂 2. Repository Directory Structure

```directory
.
├── README.md                  # Project overview, model physics, and execution guides (This file)
├── simulation.py              # Cross-layer physical-MAC event-driven Monte Carlo simulator
├── analysis.py                # Visualizer generating high-resolution publication-grade figures
├── config.py                  # Physics, environment, transceiver, and network parameters
├── results/                   # Destination folder for raw CSV data and generated figures
│   ├── diurnal_performance.csv
│   ├── link_budget_analysis.csv
│   ├── pdr_summary.csv
│   ├── pdr_vs_distance.csv
│   ├── pdr_vs_density.png
│   ├── energy_vs_density.png
│   └── ...
└── paper/                     # LaTeX Academic Manuscripts & Publication Pipeline

```

---

## 🛠️ 3. Installation & Getting Started

### Prerequisites
Ensure you have Python 3.8+ and the following scientific packages installed:
```bash
pip install numpy pandas matplotlib
```


---

## 🚀 4. Running the Simulation & Analysis

The entire simulation workflow is modularized into two stages: **Data Generation** and **Visualization**.

### Step 1: Generate Simulation Datasets
Run the Monte Carlo simulator to evaluate PDR, energy efficiency, and dynamic diurnal shifts across different Martian seasons (Clear vs. Dust Storm) and network topologies (Surface Gateways vs. direct-to-satellite LEO Walker Star Constellations):
```bash
python3 simulation.py
```
*This executes 30 independent paired Monte Carlo runs (to guarantee $95\%$ confidence intervals) for node densities up to 500, gateway coverage radii up to 20 km, and sol-cycle hours.*

### Step 2: Plot Publication-Grade Figures
Visualize the output datasets by running the plotting script:
```bash
python3 analysis.py
```
This generates professional-grade, publication-ready vector-compliant visual plots inside the `results/` folder:
- **`pdr_vs_density.png`**: Packet Delivery Ratio (PDR, %) as a function of node count under Earth/Mars configurations.
- **`energy_vs_density.png`**: Logarithmic energy consumption (Joules per successful delivery) under different weather seasons.
- **`pdr_vs_distance.png`**: Spatial reliability and maximum communication radius around the gateways.
- **`diurnal_performance.png`**: PDR fluctuation synced with the 24-hour Sol temperature cycles.

---

## 📊 5. Key Scientific Results

Our system simulation models demonstrate several notable findings:

| Scenario / Configuration | Frequency | Clear Season PDR (%) | Dust Storm PDR (%) | Meteorological Decoupling |
| :--- | :---: | :---: | :---: | :---: |
| **Standard Earth Baseline** | 868 MHz | $98.1\%$ | N/A | Yes |
| **Mars Surface Gateway (Standard)** | 868 MHz | $81.2\%$ | $19.4\%$ | **No** (Severe Fading) |
| **Mars Satellite Gateway (Standard)** | 868 MHz | $89.5\%$ | $42.1\%$ | **No** (Clock/Regolith Losses) |
| **Proposed Martian Surface (Optimized)** | 433 MHz | $92.4\%$ | $87.8\%$ | Partial (Atmospheric Path Loss) |
| **Proposed Martian Satellite (Optimized)** | 433 MHz | **$98.2\%$** | **$97.9\%$** | **Yes (Fully Decoupled)** |

### 📈 Major Insights:
1. **Weather-Sensitivity Decoupling**: Under standard configurations (868 MHz), Martian dust storms collapse the satellite PDR to **$42.1\%$** due to dust coating signal attenuation and clock frequency drift.
2. **Atmospheric Immunity**: Our proposed 433 MHz Walker-star satellite constellation scheme achieves complete weather immunity, maintaining an outstanding **$97.9\%$ PDR** even during intense global dust storms—demonstrating a flat performance line irrespective of meteorological conditions.
3. **Power Efficiency**: The optimized active compensation reduces energy consumption per successful packet by over **$2.5\times$** during dusty seasons compared to uncompensated systems.
