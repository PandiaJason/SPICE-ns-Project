# -*- coding: utf-8 -*-
"""
Simulation/thermal.py - Thermal Control System Module
Models cabin, avionics, and radiator temperatures, accounting for crew activity,
equipment loads, and radiator efficiency degradation (Scenario A).
Includes an active cabin heating and cooling loop to stabilize temperature.
"""

import numpy as np

class ThermalSystem:
    def __init__(self, t_cab_init=21.0, t_av_init=35.0, t_rad_init=-10.0):
        # Temperatures in Celsius
        self.t_cab = t_cab_init
        self.t_av = t_av_init
        self.t_rad = t_rad_init
        
        # Heat capacities (J / K)
        self.c_cab = 1.5e5
        self.c_av = 5.0e4
        self.c_rad = 8.0e4
        
        # Heat transfer coefficients (W / K) - tuned for realistic coupling
        self.u_cab2rad = 15.0
        self.u_av2rad = 40.0
        
        # Radiator parameters
        self.a_rad = 18.0  # Area in m^2
        self.sigma = 5.670374e-8  # Stefan-Boltzmann constant (W/m^2/K^4)
        self.t_space_k = 3.0  # Deep space background temperature in Kelvin
        self.epsilon_nominal = 0.85
        self.epsilon = self.epsilon_nominal
        
    def get_state(self):
        return {
            "cabin_temperature": self.t_cab,
            "avionics_temperature": self.t_av,
            "radiator_temperature": self.t_rad,
            "radiator_efficiency": self.epsilon
        }
        
    def update(self, dt, crew_heat_w, avionics_heat_w, radiator_degradation_pct=0.0, correction_active=False):
        """
        Update temperatures by dt seconds.
        """
        # Set radiator emissivity based on degradation (non-accumulating)
        if radiator_degradation_pct > 0.0 and not correction_active:
            self.epsilon = self.epsilon_nominal * (1.0 - radiator_degradation_pct)
        else:
            self.epsilon = self.epsilon_nominal
            
        # Active Cooling: increase coupling to radiator if cabin temperature is high
        # This simulates active climate control valves opening under load
        u_cab2rad_eff = self.u_cab2rad
        if self.t_cab > 21.0:
            u_cab2rad_eff += 20.0 * (self.t_cab - 21.0)
            
        # Adjust heat transfer coefficients if correction is active (boost coolant pump)
        if correction_active:
            u_cab2rad_eff = max(u_cab2rad_eff * 2.0, 50.0)
            u_av2rad_eff = self.u_av2rad * 2.0
        else:
            u_av2rad_eff = self.u_av2rad
        
        # Convert to Kelvin for radiation calculations
        t_rad_k = self.t_rad + 273.15
        
        # Heat exchange rates
        q_cab2rad = u_cab2rad_eff * (self.t_cab - self.t_rad)
        q_av2rad = u_av2rad_eff * (self.t_av - self.t_rad)
        
        # Active Cabin Heater: attempts to maintain cabin temperature at 21.0 C
        # Adds up to 1500W to balance heat loss
        heater_w = 0.0
        if self.t_cab < 21.0:
            heater_w = min(1500.0, 10.0 * (21.0 - self.t_cab) + q_cab2rad - crew_heat_w)
            heater_w = max(0.0, heater_w)
            
        # Radiator heat rejection to deep space (Stefan-Boltzmann law)
        q_rad_out = self.epsilon * self.sigma * self.a_rad * (t_rad_k**4 - self.t_space_k**4)
        
        # Temperature derivatives (dT/dt = Q_net / C)
        dt_cab = (crew_heat_w + heater_w - q_cab2rad) / self.c_cab
        dt_av = (avionics_heat_w - q_av2rad) / self.c_av
        dt_rad = (q_cab2rad + q_av2rad - q_rad_out) / self.c_rad
        
        # Euler integration step
        self.t_cab += dt_cab * dt
        self.t_av += dt_av * dt
        self.t_rad += dt_rad * dt
        
        # Limit to physical boundaries
        self.t_cab = np.clip(self.t_cab, 10.0, 40.0)
        self.t_av = np.clip(self.t_av, 15.0, 80.0)
        self.t_rad = np.clip(self.t_rad, -100.0, 100.0)
        
        return self.get_state()
