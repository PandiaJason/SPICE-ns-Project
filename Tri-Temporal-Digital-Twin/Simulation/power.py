# -*- coding: utf-8 -*-
"""
Simulation/power.py - Electrical Power System Module
Simulates battery capacity, state of charge (SOC), solar generation, and load,
handling battery capacity degradation (Scenario B).
"""

import numpy as np

class PowerSystem:
    def __init__(self, soc_init=90.0, capacity_kwh=20.0, degradation_pct=0.0, load_shedding_active=False):
        # Battery capacity parameters
        self.capacity_kwh_nominal = capacity_kwh  # kWh
        self.capacity_j_nominal = capacity_kwh * 3.6e6  # Joules
        
        actual_degradation = degradation_pct if not load_shedding_active else (degradation_pct * 0.3)
        current_capacity_j = self.capacity_j_nominal * (1.0 - actual_degradation)
        
        self.soc = soc_init  # percent (0 to 100)
        self.charge_j = (soc_init / 100.0) * current_capacity_j  # Joules
        
        self.p_solar_max = 12000.0  # Watts max solar power
        self.p_base_load = 2500.0  # Watts baseline system load
        
    def get_solar_generation(self, t_sec):
        """
        Solar generation is periodic as the spacecraft orbits Mars (period 120 minutes = 7200s).
        Generates power during sun exposure, 0 in shadow.
        """
        # Orbit period: 7200 seconds
        exposure = np.cos(2.0 * np.pi * t_sec / 7200.0)
        if exposure < -0.1:
            # Shadow
            return 0.0
        elif exposure < 0.2:
            # Penumbra transition
            return self.p_solar_max * (exposure + 0.1) / 0.3
        else:
            # Full sunlight
            return self.p_solar_max * min(1.0, exposure)
            
    def get_state(self):
        return {
            "battery_soc": self.soc,
            "battery_charge_j": self.charge_j
        }
        
    def update(self, dt, t_sec, crew_power_w, battery_degradation_pct=0.0, load_shedding_active=False):
        """
        Update power state.
        battery_degradation_pct: percentage capacity loss (Scenario B)
        load_shedding_active: power-shedding command is active
        """
        # Calculate capacity based on degradation (non-accumulating)
        actual_degradation_pct = battery_degradation_pct if not load_shedding_active else (battery_degradation_pct * 0.3)
        current_capacity_j = self.capacity_j_nominal * (1.0 - actual_degradation_pct)
        
        # Clamp charge if capacity has shrunk
        if self.charge_j > current_capacity_j:
            self.charge_j = current_capacity_j
            
        # Solar generation
        p_gen = self.get_solar_generation(t_sec)
        
        # Load power
        # If load shedding is active, reduce base load by 40%
        base_load = self.p_base_load * 0.6 if load_shedding_active else self.p_base_load
        p_load = base_load + crew_power_w
        
        # Net power
        p_net = p_gen - p_load
        
        # Integrate charge
        self.charge_j += p_net * dt
        self.charge_j = np.clip(self.charge_j, 0.0, current_capacity_j)
        
        # Update SOC
        self.soc = (self.charge_j / current_capacity_j) * 100.0
        
        return self.get_state()
