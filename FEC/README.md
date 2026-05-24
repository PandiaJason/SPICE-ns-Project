# Adaptive Turbo Code for Deep-Space Non-Gaussian Channels

> **Paper title:** *"A Dynamically Punctured Variable-Memory Turbo Code Optimization
> for Non-Gaussian Radiation Noise Channels in Deep Space"*

## Project Structure

```
FEC/
├── run_simulation.py        ← STEP 1: run this first
├── analyze_results.py       ← STEP 2: run this after simulation
├── requirements.txt
├── simulation/
│   ├── __init__.py
│   ├── config.py            ← all tunable parameters
│   ├── channel.py           ← AWGN + Middleton Class-A + channel estimator
│   ├── codec.py             ← RSC encoder, BCJR decoder, turbo decoder w/ DET
│   └── runner.py            ← Monte-Carlo simulation loop
├── figures/                 ← output PDFs (created by analyze_results.py)
├── results/                 ← output JSON files (created by run_simulation.py)
└── paper/
    ├── main.tex             ← IEEE two-column LaTeX manuscript
    └── references.bib
```

## Quick Start

```bash
# Install dependencies
pip3 install -r requirements.txt

# Step 1: Run simulation (saves JSON files to results/)
python3 run_simulation.py

# Step 2: Generate figures and LaTeX table (reads results/, writes figures/)
python3 analyze_results.py

# Step 3: Compile paper
cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

## Experiments

| Label | Channel | Puncturing | DET |
|---|---|---|---|
| CCSDS-Static-AWGN | AWGN | Rate-1/2 static | No |
| DET-Static-AWGN | AWGN | Rate-1/2 static | Yes |
| CCSDS-Static-Middleton | Middleton | Rate-1/2 static | No |
| DET-Static-Middleton | Middleton | Rate-1/2 static | Yes |
| **Proposed-Adaptive-Middleton** | **Middleton** | **Adaptive** | **Yes** |
| Proposed-Adaptive-AWGN | AWGN | Adaptive | Yes |

## Figures Generated

| File | Description |
|---|---|
| `fig1_ber_awgn.pdf` | BER vs Eb/N0 – AWGN baseline |
| `fig2_ber_middleton.pdf` | BER vs Eb/N0 – Middleton (error floor elimination) |
| `fig3_bler_comparison.pdf` | BLER comparison |
| `fig4_iter_savings.pdf` | Average iterations / decoder power savings |
| `fig5_ce_traces.pdf` | Cross-entropy convergence per iteration |
| `fig6_error_floor_zoom.pdf` | Zoomed error-floor region (high SNR) |

## Key Parameters (simulation/config.py)

| Parameter | Default | Description |
|---|---|---|
| `BLOCK_SIZES` | [256, 1024] | Info block sizes in bits |
| `SNR_DB_RANGE` | -1 to 6.5 dB | Eb/N0 sweep |
| `MAX_ITERATIONS` | 12 | Max BCJR iterations |
| `DET_START_ITER` | 3 | Iteration at which DET activates |
| `DET_DELTA` | 0.005 | CE convergence threshold |
| `MIDDLETON_A` | 0.1 | Impulsive index (SEP severity) |
| `MIDDLETON_GAMMA` | 0.01 | Gaussian/impulsive power ratio |
| `MIN_BIT_ERRORS` | 100 | Min errors before moving to next SNR |
| `MAX_FRAMES` | 2000 | Frame cap per SNR point |
