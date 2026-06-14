# -*- coding: utf-8 -*-
"""
Simulation/dynamics.py - Orbital Dynamics and Attitude Module
Models Mars gravity, thruster acceleration, and propagates position, velocity,
and attitude using RK4 integration. Supports Scenario D (burn execution errors).
"""

import numpy as np

class OrbitalDynamics:
    # Mars gravitational parameter mu (km^3 / s^2)
    MU_MARS = 42828.37
    # Mars radius (km)
    R_MARS = 3396.2

    def __init__(self, r0=None, v0=None, m_sc=50000.0):
        """
        r0: Initial position vector [x, y, z] in km (Mars-centric inertial frame)
        v0: Initial velocity vector [vx, vy, vz] in km/s
        m_sc: Spacecraft mass in kg
        """
        if r0 is None:
            # Mars approach orbit insertion prep
            # High elliptical approach
            self.r = np.array([12000.0, 5000.0, 0.0]) # km
        else:
            self.r = np.array(r0, dtype=float)

        if v0 is None:
            self.v = np.array([-2.2, 1.1, 0.0]) # km/s
        else:
            self.v = np.array(v0, dtype=float)

        self.m_sc = m_sc  # kg
        self.attitude = np.array([1.0, 0.0, 0.0, 0.0])  # Quaternion [w, x, y, z]
        self.omega = np.array([0.0, 0.0, 0.0])  # Angular velocity (rad/s)
        self.nominal_thrust = 12000.0  # Newtons (12 kN thruster)
        self.isp = 320.0  # seconds

    def get_altitude(self):
        return np.linalg.norm(self.r) - self.R_MARS

    def get_state(self):
        return {
            "r": self.r.copy(),
            "v": self.v.copy(),
            "position_magnitude": np.linalg.norm(self.r),
            "velocity_magnitude": np.linalg.norm(self.v),
            "attitude_yaw": float(np.arctan2(2.0*(self.attitude[0]*self.attitude[3] + self.attitude[1]*self.attitude[2]), 
                                            1.0 - 2.0*(self.attitude[2]**2 + self.attitude[3]**2))), # yaw in rad
            "omega": self.omega.copy()
        }

    def derivatives(self, r, v, thrust_vector, mass):
        """
        Compute derivatives of position and velocity
        dr/dt = v
        dv/dt = a_gravity + a_thrust
        """
        r_mag = np.linalg.norm(r)
        a_grav = -self.MU_MARS / (r_mag**3) * r  # km/s^2
        # thrust_vector is in Newtons, convert to km/s^2: (N = kg*m/s^2, divide by mass in kg, then convert m to km)
        a_thrust = (thrust_vector / mass) / 1000.0  # km/s^2
        
        return v, a_grav + a_thrust

    def propagate(self, dt, thrust_active=False, thrust_error_pct=0.0, attitude_error_rad=0.0, correction_active=False):
        """
        Propagate state by dt seconds using RK4.
        Scenario D represents a trajectory burn under execution uncertainty.
        If thrust_error_pct > 0 or attitude_error_rad > 0, the burn will drift.
        If correction_active is true, it corrects the drift.
        """
        thrust_vector = np.array([0.0, 0.0, 0.0])
        
        if thrust_active:
            # Thrust direction nominal is tangent to velocity (prograde or retrograde)
            v_dir = self.v / np.linalg.norm(self.v)
            
            # Apply attitude error (Scenario D)
            if attitude_error_rad > 0.0 and not correction_active:
                # Rotate thrust vector slightly in the orbital plane
                c, s = np.cos(attitude_error_rad), np.sin(attitude_error_rad)
                v_dir_err = np.array([c*v_dir[0] - s*v_dir[1], s*v_dir[0] + c*v_dir[1], v_dir[2]])
                v_dir = v_dir_err / np.linalg.norm(v_dir_err)
                
            thrust_mag = self.nominal_thrust
            if thrust_error_pct > 0.0 and not correction_active:
                thrust_mag *= (1.0 - thrust_error_pct)
                
            thrust_vector = v_dir * thrust_mag
            
            # Fuel consumption
            mdot = thrust_mag / (self.isp * 9.80665)  # kg/s
            self.m_sc -= mdot * dt

        # RK4 Integration for orbital state
        r1, v1 = self.r, self.v
        dr1, dv1 = self.derivatives(r1, v1, thrust_vector, self.m_sc)

        r2 = r1 + 0.5 * dt * dr1
        v2 = v1 + 0.5 * dt * dv1
        dr2, dv2 = self.derivatives(r2, v2, thrust_vector, self.m_sc)

        r3 = r1 + 0.5 * dt * dr2
        v3 = v1 + 0.5 * dt * dv2
        dr3, dv3 = self.derivatives(r3, v3, thrust_vector, self.m_sc)

        r4 = r1 + dt * dr3
        v4 = v1 + dt * dv3
        dr4, dv4 = self.derivatives(r4, v4, thrust_vector, self.m_sc)

        self.r += (dt / 6.0) * (dr1 + 2.0*dr2 + 2.0*dr3 + dr4)
        self.v += (dt / 6.0) * (dv1 + 2.0*dv2 + 2.0*dv3 + dv4)

        # Propagate attitude (simple rotation update)
        # Pitch, yaw, roll rates (add slight noise or orbital rate)
        if thrust_active:
            # Minor attitude vibrations
            self.omega += np.random.normal(0, 0.0001, 3)
        else:
            # Damping
            self.omega = 0.95 * self.omega
            
        # Update quaternion (simple integration)
        theta = np.linalg.norm(self.omega) * dt
        if theta > 1e-8:
            axis = self.omega / np.linalg.norm(self.omega)
            dq = np.array([np.cos(theta/2), axis[0]*np.sin(theta/2), axis[1]*np.sin(theta/2), axis[2]*np.sin(theta/2)])
            # Multiply quaternions
            w0, x0, y0, z0 = self.attitude
            w1, x1, y1, z1 = dq
            self.attitude = np.array([
                w0*w1 - x0*x1 - y0*y1 - z0*z1,
                w0*x1 + x0*w1 + y0*z1 - z0*y1,
                w0*y1 - x0*z1 + y0*w1 + z0*x1,
                w0*z1 + x0*y1 - y0*x1 + z0*w1
            ])
            self.attitude /= np.linalg.norm(self.attitude)
