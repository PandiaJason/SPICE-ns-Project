#!/usr/bin/env python3
"""
run_simulation.py – Entry point for the Space Federated Learning Simulation.

Usage:
    python run_simulation.py
"""
import sys
import os

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.runner import run_all

if __name__ == '__main__':
    run_all()
