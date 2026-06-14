# -*- coding: utf-8 -*-
"""
Simulation/eclss.py - Environmental Control and Life Support System Module
Simulates cabin atmosphere (O2, CO2, humidity, pressure) and crew metabolism.
Includes CO2 scrubber degradation logic (Scenario C).
"""

import numpy as np

class LifeSupportSystem:
    def __init__(self, pressure_psi=14.7, o2_pct=20.9, co2_pct=0.04, humidity_pct=45.0, cabin_volume_m3=120.0):
        # Environmental variables
        self.pressure_psi = pressure_psi
        self.o2_pct = o2_pct
        self.co2_pct = co2_pct
        self.humidity_pct = humidity_pct
        
        # Cabin dimensions (m^3)
        self.cabin_volume = cabin_volume_m3  # m^3
        # Air mass calculation (approx 1.2 kg/m^3 at sea level)
        self.air_mass_kg = 120.0 * 1.2
        
        # Scrubber base parameters
        # Nominal CO2 removal rate is proportional to CO2 concentration (realistic)
        self.co2_nominal_removal_rate = 6.5e-5  # kg/s base at nominal CO2
        self.scrubber_efficiency = 1.0
        
    def get_state(self):
        return {
            "cabin_pressure": self.pressure_psi,
            "oxygen": self.o2_pct,
            "carbon_dioxide": self.co2_pct,
            "humidity": self.humidity_pct,
            "scrubber_efficiency": self.scrubber_efficiency
        }
        
    def update(self, dt, crew_o2_kg_s, crew_co2_kg_s, crew_h2o_kg_s,
               co2_scrubber_degradation_pct=0.0, backup_scrubber_active=False):
        """
        Update ECLSS state.
        co2_scrubber_degradation_pct: percentage loss of efficiency (Scenario C)
        backup_scrubber_active: backup scrubber activated
        """
        # Set scrubber efficiency
        # Non-accumulating degradation
        if co2_scrubber_degradation_pct > 0.0 and not backup_scrubber_active:
            self.scrubber_efficiency = 1.0 - co2_scrubber_degradation_pct
        else:
            self.scrubber_efficiency = 1.0
            
        # CO2 Scrubber Removal:
        # Removal rate increases with CO2 levels (mass action law)
        # If backup is active, efficiency is boosted by 50%
        eff_multiplier = 1.5 if backup_scrubber_active else self.scrubber_efficiency
        co2_removed_kg = self.co2_nominal_removal_rate * (self.co2_pct / 0.04) * eff_multiplier * dt
        
        # Calculate masses of O2 and CO2 in cabin
        o2_mass_kg = (self.o2_pct / 100.0) * self.air_mass_kg
        co2_mass_kg = (self.co2_pct / 100.0) * self.air_mass_kg
        
        # Update masses
        o2_mass_kg -= crew_o2_kg_s * dt
        co2_mass_kg += crew_co2_kg_s * dt - co2_removed_kg
        
        # Clamp masses to positive values
        o2_mass_kg = max(0.0, o2_mass_kg)
        co2_mass_kg = max(0.0, co2_mass_kg)
        
        # Re-calculate percentages
        self.o2_pct = (o2_mass_kg / self.air_mass_kg) * 100.0
        self.co2_pct = (co2_mass_kg / self.air_mass_kg) * 100.0
        
        # Keep CO2 in realistic range
        self.co2_pct = np.clip(self.co2_pct, 0.01, 2.0)
        
        # Humidity change: crew adds humidity, condensation control removes it
        h2o_removed_kg = 1.2 * crew_h2o_kg_s * dt  # condensation controller works proportionally
        # Simplistic humidity representation
        self.humidity_pct += (crew_h2o_kg_s * dt - h2o_removed_kg) * 0.1
        self.humidity_pct = np.clip(self.humidity_pct, 30.0, 70.0)
        
        # Pressure remains stable unless there is a leak (nominal 14.7 psi)
        return self.get_state()
