#!/bin/bash
# run_simulation.sh
# Automates the Laser Wake-on-Beacon IoT Switch simulation.

set -e

echo "=========================================================="
echo "Starting Laser Wake-on-Beacon Interplanetary Simulation..."
echo "=========================================================="
echo ""

# Create output directories if they do not exist
mkdir -p /home/jason/SPICE-ns-Project/SatWAKE-UP/results

# 1. Run Earth Transmitter Simulation
echo "Step 1: Running Earth Transmitter (Point-Ahead Calculations)..."
python3 /home/jason/SPICE-ns-Project/SatWAKE-UP/transmitter.py
echo "Earth Transmitter simulation complete."
echo ""

# 2. Run Mars Orbiter Satellite Receiver Simulation
echo "Step 2: Running Mars Satellite Receiver (FSM & Geometric Pointing Evaluation)..."
python3 /home/jason/SPICE-ns-Project/SatWAKE-UP/receiver.py
echo "Mars Satellite Receiver simulation complete."
echo ""

# 3. Run Analysis & Graph Generation
echo "Step 3: Analyzing Logs & Generating Publication-Quality Plots..."
python3 /home/jason/SPICE-ns-Project/SatWAKE-UP/analyze.py
echo "Analysis and plotting complete."
echo ""

# 4. Generate 3D Trajectory Animation
echo "Step 4: Generating 3D Trajectory Animation GIF..."
python3 /home/jason/SPICE-ns-Project/SatWAKE-UP/visualize_3d.py
echo "3D Trajectory Animation complete."
echo ""

# 5. Sync Artifacts
echo "Step 5: Synchronizing Plots and Animation to Conversation Artifacts..."
mkdir -p /home/jason/.gemini/antigravity/brain/fc4a0153-7a96-4df8-99a9-50d2dabbe582/artifacts
cp /home/jason/SPICE-ns-Project/SatWAKE-UP/results/*.png /home/jason/.gemini/antigravity/brain/fc4a0153-7a96-4df8-99a9-50d2dabbe582/artifacts/
cp /home/jason/SPICE-ns-Project/SatWAKE-UP/results/*.gif /home/jason/.gemini/antigravity/brain/fc4a0153-7a96-4df8-99a9-50d2dabbe582/artifacts/
echo "Sync complete."
echo ""

echo "=========================================================="
echo "Simulation Pipeline Finished Successfully!"
echo "All outputs, logs, and plots are available directly in the results folder."
echo "=========================================================="
