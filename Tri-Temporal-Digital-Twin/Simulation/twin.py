# -*- coding: utf-8 -*-
"""
Simulation/twin.py - Tri-Temporal Digital Twin Architecture Module
Implements Past Twin, Present Twin, and Future Twin models, along with the
Reconciliation Engine that calibrates twin parameters when delayed telemetry is received.
"""

import numpy as np
from Simulation.dynamics import OrbitalDynamics
from Simulation.thermal import ThermalSystem
from Simulation.power import PowerSystem
from Simulation.eclss import LifeSupportSystem
from Simulation.crew import CrewModel

class TwinState:
    """Represents a snapshot of the spacecraft state at a given time."""
    def __init__(self, t, r, v, m_sc, attitude_yaw, cabin_temp, avionics_temp, radiator_temp, battery_soc, o2, co2, humidity, pressure):
        self.t = t
        self.r = np.array(r, dtype=float)
        self.v = np.array(v, dtype=float)
        self.m_sc = m_sc
        self.attitude_yaw = attitude_yaw
        self.cabin_temperature = cabin_temp
        self.avionics_temperature = avionics_temp
        self.radiator_temperature = radiator_temp
        self.battery_soc = battery_soc
        self.oxygen = o2
        self.carbon_dioxide = co2
        self.humidity = humidity
        self.cabin_pressure = pressure

    @property
    def position_magnitude(self):
        return np.linalg.norm(self.r)

    @property
    def velocity_magnitude(self):
        return np.linalg.norm(self.v)

    def copy(self):
        return TwinState(
            self.t, self.r.copy(), self.v.copy(), self.m_sc, self.attitude_yaw,
            self.cabin_temperature, self.avionics_temperature, self.radiator_temperature,
            self.battery_soc, self.oxygen, self.carbon_dioxide, self.humidity, self.cabin_pressure
        )

class TriTemporalDigitalTwin:
    def __init__(self, initial_state: TwinState, one_way_delay=240.0):
        self.delay = one_way_delay
        self.crew_model = CrewModel()
        
        # Initialize the three twins
        # The Past Twin represents the state at t_current - delay
        self.past_twin = initial_state.copy()
        # The Present Twin represents the state at t_current
        self.present_twin = initial_state.copy()
        # The Future Twin represents the state at t_current + delay
        self.future_twin = initial_state.copy()
        
        # Calibration parameters (reconciled by the Reconciliation Engine)
        self.calibrated_radiator_efficiency = 0.85
        self.calibrated_battery_capacity = 20.0
        self.calibrated_scrubber_efficiency = 1.0
        
        # History of predictions to compare for reconciliation
        # Key: target_time, Value: predicted state
        self.predictions_history = {}
        
    def log_prediction(self, target_time, state: TwinState):
        self.predictions_history[int(target_time)] = state.copy()
        # Keep history bounded
        if len(self.predictions_history) > 50000:
            oldest = min(self.predictions_history.keys())
            del self.predictions_history[oldest]
            
    def reconcile(self, telemetry_time, telemetry_state: TwinState):
        """
        Reconciliation Engine.
        When telemetry from telemetry_time arrives (received at t_current = telemetry_time + delay):
        1. Compare telemetry with the previously predicted Future Twin for telemetry_time.
        2. Compute prediction errors (residuals).
        3. Dynamically adjust/calibrate the models' parameters (parameter estimation) to minimize future errors.
        4. Synchronize the Past Twin's state with the telemetry state.
        """
        # Find the prediction we made for this epoch
        t_key = int(telemetry_time)
        predicted_state = self.predictions_history.get(t_key)
        
        errors = {}
        if predicted_state is not None:
            errors["thermal"] = telemetry_state.cabin_temperature - predicted_state.cabin_temperature
            errors["power"] = telemetry_state.battery_soc - predicted_state.battery_soc
            errors["co2"] = telemetry_state.carbon_dioxide - predicted_state.carbon_dioxide
            errors["position"] = np.linalg.norm(telemetry_state.r - predicted_state.r)
            errors["velocity"] = np.linalg.norm(telemetry_state.v - predicted_state.v)
            
            # --- Parameter Calibration (Feedback loops) ---
            # Thermal calibration: adjust radiator efficiency estimate if temperatures diverge
            # If actual temp is higher than predicted temp, actual efficiency is lower than estimated
            # Update radiator efficiency estimate with a small gain
            thermal_gain = 0.005
            self.calibrated_radiator_efficiency -= thermal_gain * errors["thermal"]
            self.calibrated_radiator_efficiency = np.clip(self.calibrated_radiator_efficiency, 0.1, 1.0)
            
            # Power calibration: adjust battery capacity estimate
            # If actual SOC is lower than predicted, battery capacity or charge was lower
            power_gain = 0.01
            self.calibrated_battery_capacity += power_gain * errors["power"]
            self.calibrated_battery_capacity = np.clip(self.calibrated_battery_capacity, 10.0, 150.0)
            
            # Life support calibration: adjust scrubber efficiency
            # If actual CO2 is higher than predicted, scrubber efficiency is lower than estimated
            co2_gain = 0.05
            self.calibrated_scrubber_efficiency -= co2_gain * errors["co2"]
            self.calibrated_scrubber_efficiency = np.clip(self.calibrated_scrubber_efficiency, 0.0, 1.5)
        else:
            errors["thermal"] = 0.0
            errors["power"] = 0.0
            errors["co2"] = 0.0
            errors["position"] = 0.0
            errors["velocity"] = 0.0
            
        # Synchronize Past Twin with telemetry
        self.past_twin = telemetry_state.copy()
        
        return errors

    def propagate_twin(self, start_state: TwinState, duration_sec, is_future_projection=False,
                       active_anomaly=None, correction_commands=None):
        """
        Propagates a state forward by duration_sec.
        Uses physics-based dynamics, thermal, power, and life support models.
        Includes options to apply known/calibrated parameters.
        """
        state = start_state.copy()
        dt = 10.0  # 10-second step for faster execution
        steps = int(duration_sec / dt)
        
        # Instantiate temporary models for propagation
        dyn = OrbitalDynamics(r0=state.r, v0=state.v, m_sc=state.m_sc)
        # Set attitude from yaw (simplified)
        c, s = np.cos(state.attitude_yaw/2), np.sin(state.attitude_yaw/2)
        dyn.attitude = np.array([c, 0, 0, s])
        
        therm = ThermalSystem(t_cab_init=state.cabin_temperature, t_av_init=state.avionics_temperature, t_rad_init=state.radiator_temperature)
        therm.epsilon_nominal = 0.85
        
        # Calculate initial power correction and degradation state at state.t
        init_power_corr = False
        if correction_commands:
            for cmd in correction_commands:
                if state.t >= cmd["execution_time"] and cmd["command_type"] == "POWER_SHED":
                    init_power_corr = True
                    
        init_battery_degradation = 0.0
        if active_anomaly:
            for anom in active_anomaly:
                if state.t >= anom["start_time"] and anom["type"] == "BATTERY" and not init_power_corr:
                    init_battery_degradation = 0.35
                    
        pwr = PowerSystem(soc_init=state.battery_soc, capacity_kwh=20.0, degradation_pct=init_battery_degradation, load_shedding_active=init_power_corr)
        
        ecl = LifeSupportSystem(cabin_volume_m3=120.0)
        ecl.o2_pct = state.oxygen
        ecl.co2_pct = state.carbon_dioxide
        ecl.humidity_pct = state.humidity
        ecl.pressure_psi = state.cabin_pressure
        ecl.scrubber_nominal_efficiency = self.calibrated_scrubber_efficiency
        
        t_sim = state.t
        for _ in range(steps):
            # 1. Crew metabolic loads
            crew_loads = self.crew_model.get_metabolic_loads(t_sim)
            
            # Check active anomalies or corrections
            thermal_degradation = 0.0
            battery_degradation = 0.0
            scrubber_degradation = 0.0
            thrust_active = False
            thrust_error_pct = 0.0
            attitude_error_rad = 0.0
            
            # Flags for active corrections (from ground command history)
            thermal_corr = False
            power_corr = False
            eclss_corr = False
            orbit_corr = False
            
            if correction_commands:
                # Check if correction commands have arrived/executed at t_sim
                for cmd in correction_commands:
                    if t_sim >= cmd["execution_time"]:
                        if cmd["command_type"] == "TCS_BOOST":
                            thermal_corr = True
                        elif cmd["command_type"] == "POWER_SHED":
                            power_corr = True
                        elif cmd["command_type"] == "ECLSS_BACKUP":
                            eclss_corr = True
                        elif cmd["command_type"] == "ORBIT_CORR":
                            orbit_corr = True
            
            if active_anomaly:
                # Apply anomalies during propagation if they are active
                for anom in active_anomaly:
                    if t_sim >= anom["start_time"]:
                        if anom["type"] == "THERMAL" and not thermal_corr:
                            thermal_degradation = 0.60
                        elif anom["type"] == "BATTERY" and not power_corr:
                            battery_degradation = 0.35
                        elif anom["type"] == "ECLSS" and not eclss_corr:
                            scrubber_degradation = 0.50
            # Scheduled Trajectory Insertion Burn (Planned Event)
            burn_start = 40.0 * 3600
            burn_duration = 600.0
            thrust_active = False
            thrust_error_pct = 0.0
            attitude_error_rad = 0.0
            
            if burn_start <= t_sim < burn_start + burn_duration:
                thrust_active = True
                if not orbit_corr:
                    thrust_error_pct = 0.05
                    attitude_error_rad = 0.08
                                
            # 2. Propagate Orbital Dynamics
            dyn.propagate(dt, thrust_active=thrust_active, thrust_error_pct=thrust_error_pct,
                          attitude_error_rad=attitude_error_rad, correction_active=orbit_corr)
            dyn_state = dyn.get_state()
            
            # 3. Propagate Thermal
            therm.update(dt, crew_loads["heat_load"], 2500.0,
                         radiator_degradation_pct=thermal_degradation, correction_active=thermal_corr)
            therm_state = therm.get_state()
            
            # 4. Propagate Power
            pwr.update(dt, t_sim, crew_loads["power_demand"],
                       battery_degradation_pct=battery_degradation, load_shedding_active=power_corr)
            pwr_state = pwr.get_state()
            
            # 5. Propagate ECLSS
            ecl.update(dt, crew_loads["o2_cons"], crew_loads["co2_prod"], crew_loads["humidity_load"],
                       co2_scrubber_degradation_pct=scrubber_degradation, backup_scrubber_active=eclss_corr)
            ecl_state = ecl.get_state()
            
            t_sim += dt
            
        return TwinState(
            t_sim, dyn_state["r"], dyn_state["v"], dyn.m_sc, dyn_state["attitude_yaw"],
            therm_state["cabin_temperature"], therm_state["avionics_temperature"], therm_state["radiator_temperature"],
            pwr_state["battery_soc"], ecl_state["oxygen"], ecl_state["carbon_dioxide"], ecl_state["humidity"], ecl_state["cabin_pressure"]
        )

    def update_twins(self, t_current, active_anomalies_ground_belief, correction_commands):
        """
        Updates the Present Twin and Future Twin based on propagation.
        Present Twin is propagated from the Past Twin (telemetry at t_current - delay) to t_current.
        Future Twin is propagated from the Present Twin (t_current) to t_current + delay.
        """
        # 1. Update Present Twin by propagating Past Twin from t_current - delay to t_current
        self.present_twin = self.propagate_twin(
            self.past_twin, self.delay,
            active_anomaly=active_anomalies_ground_belief,
            correction_commands=correction_commands
        )
        
        # 2. Update Future Twin by propagating Present Twin from t_current to t_current + delay
        self.future_twin = self.propagate_twin(
            self.present_twin, self.delay, is_future_projection=True,
            active_anomaly=active_anomalies_ground_belief,
            correction_commands=correction_commands
        )
        
        # 3. Log the prediction made for t_current + delay (Future Twin)
        # This will be compared with telemetry that arrives in the future at t_current + 2*delay
        self.log_prediction(t_current + self.delay, self.future_twin)
