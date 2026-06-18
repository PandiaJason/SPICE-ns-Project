#!/usr/bin/env python3
"""
run_all.py  –  Master orchestration script.
Runs the full pipeline:
  1. generate_data.py    → ./simulation/data/
  2. run_benchmark.py    → ./simulation/outputs/
  3. generate_figures.py → ./simulation/graphs/ + ./paper/images/
"""

import os, sys, subprocess, time

ROOT = os.path.dirname(os.path.abspath(__file__))
SIM  = os.path.join(ROOT, "simulation")

steps = [
    ("Generating mission data profiles",   os.path.join(SIM, "generate_data.py")),
    ("Running simulation benchmarks",      os.path.join(SIM, "run_benchmark.py")),
    ("Generating publication figures",     os.path.join(SIM, "generate_figures.py")),
]

t_total = time.perf_counter()
for desc, script in steps:
    print(f"\n{'─'*60}")
    print(f"  STEP: {desc}")
    print(f"{'─'*60}")
    t0 = time.perf_counter()
    result = subprocess.run([sys.executable, script], cwd=ROOT)
    if result.returncode != 0:
        print(f"\n[ERROR] Step failed: {script}")
        sys.exit(result.returncode)
    print(f"  ⏱  {time.perf_counter()-t0:.2f}s")

print(f"\n{'═'*60}")
print(f"  ✅  Pipeline complete in {time.perf_counter()-t_total:.2f}s")
print(f"  Outputs  → {os.path.join(ROOT, 'simulation', 'outputs')}")
print(f"  Figures  → {os.path.join(ROOT, 'simulation', 'graphs')}")
print(f"  Paper    → {os.path.join(ROOT, 'paper')}")
print(f"{'═'*60}")
