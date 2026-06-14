# -*- coding: utf-8 -*-
"""
Simulation/run_all.py - Master Execution Script
Runs the simulator, the statistical analysis, and the plot generation scripts sequentially.
"""

import subprocess
import os
import sys

def main():
    sim_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=====================================================================")
    # 1. Run Simulator
    print("STEP 1: Running High-Fidelity 48-Hour Multi-Experiment Simulation...")
    sim_script = os.path.join(sim_dir, "simulator.py")
    res = subprocess.run([sys.executable, sim_script], check=True)
    if res.returncode != 0:
        print("Simulation failed. Aborting.")
        sys.exit(1)
        
    print("=====================================================================")
    # 2. Run Analysis
    print("STEP 2: Executing Statistical Analysis & Metrics Calculation...")
    analysis_script = os.path.join(sim_dir, "analysis.py")
    res = subprocess.run([sys.executable, analysis_script], check=True)
    if res.returncode != 0:
        print("Analysis failed. Aborting.")
        sys.exit(1)
        
    print("=====================================================================")
    # 3. Run Plot Generation
    print("STEP 3: Generating 12 Publication-Quality Figures (Vector & PNG)...")
    plots_script = os.path.join(sim_dir, "generate_plots.py")
    res = subprocess.run([sys.executable, plots_script], check=True)
    if res.returncode != 0:
        print("Plot generation failed. Aborting.")
        sys.exit(1)
        
    print("=====================================================================")
    print("SUCCESS: T3DT Simulation, Analysis, and Visualization pipeline finished.")
    print("=====================================================================")

if __name__ == "__main__":
    main()
