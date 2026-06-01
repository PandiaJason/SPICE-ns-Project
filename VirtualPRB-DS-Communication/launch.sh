#!/usr/bin/env bash
# =============================================================================
#  PTB Web-based Simulation Launcher
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIM_DIR="$SCRIPT_DIR/simulation"

if [ "$1" == "record" ]; then
    echo "======================================================"
    echo "  Predictive Temporal Bridge (PTB) — RECORD MODE"
    echo "======================================================"
    echo "  Running fast-forward simulation to generate metrics..."
    python3 "$SIM_DIR/generate_plots.py"
    echo "  Done! Graphs saved to root and paper directories."
    echo "======================================================"
elif [ "$1" == "display" ] || [ -z "$1" ]; then
    echo "======================================================"
    echo "  Predictive Temporal Bridge (PTB) — WEB SIMULATION"
    echo "======================================================"
    echo "  Starting Flask server backend..."
    echo "  Once running, open: http://localhost:5000 in your browser."
    echo "  Press Ctrl+C to terminate the simulation."
    echo "======================================================"
    python3 "$SIM_DIR/server.py"
else
    echo "Usage: bash launch.sh [record|display]"
    echo "  record  : Fast-forward simulation, generates and saves analytical graphs for paper."
    echo "  display : Starts interactive web server simulation on localhost:5000."
fi
