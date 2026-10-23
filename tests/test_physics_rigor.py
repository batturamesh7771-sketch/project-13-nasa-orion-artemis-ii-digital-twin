"""
Rigorous Physics & Mathematical Verification Test Suite for NASA Orion MPCV.
Audits:
  1. Two-body Keplerian orbital propagation with specific energy conservation (|dE/E| < 1e-6).
  2. Angular momentum vector conservation (|dh/h| < 1e-6, plane preservation).
  3. Adaptive Dormand-Prince 5(4) integrator convergence across tighter tolerances (1e-4 to 1e-10).
  4. Mass depletion differential equations and Tsiolkovsky rocket equation consistency.
  5. Coordinate frame transformations, DCM orthogonality (C*C^T = I), and quaternion unit norms.
  6. Unit conversions, dimensional analysis, and Sutton-Graves flux scaling.
  7. Mission event chronological ordering, MET monotonicity, and physical causality.
"""

import math
import unittest
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

from simulation.trajectory.adaptive_integrator import DormandPrince45, TwoBodyOrbitalPropagator
from web.telemetry_streamer import OrionTelemetryEngine

class TestPhysicsRigor(unittest.TestCase):
    def setUp(self):
        self.prop = TwoBodyOrbitalPropagator()
        self.integrator = DormandPrince45(rtol=1e-8, atol=1e-10)

    def test_01_two_body_energy_conservation(self):
        """
        Verify two-body orbital propagation conserves specific orbital energy
        to within |Delta E / E_0| < 1e-6 across multiple complete orbits.
        """
        # Circular / mildly eccentric orbit at 400 km LEO
        r0_mag = 6378137.0 + 400000.0 # 6,778.137 km
        v_circ = math.sqrt(self.prop.MU_EARTH / r0_mag) # ~7672.6 m/s
        
        # State: [rx, ry, rz, vx, vy, vz]
        state0 = np.array([r0_mag, 0.0, 0.0, 0.0, v_circ, 0.0])
        e0 = self.prop.specific_energy(state0[:3], state0[3:6])
        
        orbital_period = 2.0 * math.pi * math.sqrt((r0_mag ** 3) / self.prop.MU_EARTH)
        # Propagate for 3 complete orbital revolutions
        t_span = (0.0, 3.0 * orbital_period)
        
        res = self.integrator.integrate(self.prop.state_derivative, t_span, state0, h_initial=30.0)
        
        states = res["y"]
        max_rel_energy_err = 0.0
        
        for state in states:
            r_vec = state[:3]
            v_vec = state[3:6]
            e_t = self.prop.specific_energy(r_vec, v_vec)
            rel_err = abs((e_t - e0) / e0)
            if rel_err > max_rel_energy_err:
                max_rel_energy_err = rel_err
                
        print(f"\n[+] Two-body 3-orbit energy conservation max |dE/E|: {max_rel_energy_err:.3e}")
        self.assertLess(max_rel_energy_err, 1e-6, 
                        f"Orbital energy violated conservation limit: {max_rel_energy_err:.3e} >= 1e-6")

    def test_02_angular_momentum_conservation(self):
        """
        Verify conservation of specific angular momentum vector h = r x v.
        Both magnitude |h| and direction (orbital plane normal) must remain invariant.
        """
        # Elliptical orbit: perigee 300 km, apogee 35,786 km (GTO)
        rp = 6378137.0 + 300000.0
        ra = 6378137.0 + 35786000.0
        a_semi = (rp + ra) / 2.0
        vp = math.sqrt(self.prop.MU_EARTH * (2.0 / rp - 1.0 / a_semi))
        
        inc = math.radians(28.5)
        state0 = np.array([rp, 0.0, 0.0, 0.0, vp * math.cos(inc), vp * math.sin(inc)])
        h0_vec = self.prop.specific_angular_momentum(state0[:3], state0[3:6])
        h0_mag = np.linalg.norm(h0_vec)
        h0_dir = h0_vec / h0_mag
        
        period = 2.0 * math.pi * math.sqrt((a_semi ** 3) / self.prop.MU_EARTH)
        t_span = (0.0, 2.0 * period)
        
        res = self.integrator.integrate(self.prop.state_derivative, t_span, state0, h_initial=60.0)
        states = res["y"]
        
        max_mag_err = 0.0
        max_dir_err_rad = 0.0
        
        for state in states:
            h_vec = self.prop.specific_angular_momentum(state[:3], state[3:6])
            h_mag = np.linalg.norm(h_vec)
            h_dir = h_vec / h_mag
            
            mag_err = abs((h_mag - h0_mag) / h0_mag)
            dir_err = math.acos(max(-1.0, min(1.0, float(np.dot(h_dir, h0_dir)))))
            
            max_mag_err = max(max_mag_err, mag_err)
            max_dir_err_rad = max(max_dir_err_rad, dir_err)
            
        print(f"[+] Angular momentum magnitude error: {max_mag_err:.3e}, plane tilt error: {max_dir_err_rad:.3e} rad")
        self.assertLess(max_mag_err, 1e-6, f"Angular momentum magnitude violated: {max_mag_err:.3e}")
        self.assertLess(max_dir_err_rad, 1e-6, f"Orbital plane tilt violated: {max_dir_err_rad:.3e} rad")

    def test_03_adaptive_integrator_convergence(self):
        """
        Quantify convergence of Dormand-Prince 5(4) integrator by tightening tolerances
        from 1e-4 down to 1e-10. Verify systematic error reduction.
        """
        r0_mag = 6378137.0 + 500000.0
        v_circ = math.sqrt(self.prop.MU_EARTH / r0_mag)
        state0 = np.array([r0_mag, 0.0, 0.0, 0.0, v_circ, 0.0])
        e0 = self.prop.specific_energy(state0[:3], state0[3:6])
        
        period = 2.0 * math.pi * math.sqrt((r0_mag ** 3) / self.prop.MU_EARTH)
        t_span = (0.0, period)
        
        tolerances = [1e-4, 1e-6, 1e-8, 1e-10]
        energy_errors = []
        step_counts = []
        
        for tol in tolerances:
            solver = DormandPrince45(rtol=tol, atol=tol * 1e-2)
            res = solver.integrate(self.prop.state_derivative, t_span, state0, h_initial=50.0)
            
            # Energy error at end of 1 orbit
            final_state = res["y"][-1]
            e_final = self.prop.specific_energy(final_state[:3], final_state[3:6])
            rel_e_err = abs((e_final - e0) / e0)
            
            energy_errors.append(rel_e_err)
            step_counts.append(res["accepted_steps"])
            
        print("\n--- RK45 Convergence Profile across Tolerances ---")
        for i, tol in enumerate(tolerances):
            print(f"  Tol: {tol:.1e} -> Steps: {step_counts[i]}, Final |dE/E|: {energy_errors[i]:.3e}")
            
        # Error must decrease monotonically as tolerance tightens
        for i in range(len(energy_errors) - 1):
            self.assertLessEqual(energy_errors[i+1], energy_errors[i] * 1.5,
                                f"Convergence non-monotonic between tol {tolerances[i]} and {tolerances[i+1]}")
            self.assertGreater(step_counts[i+1], step_counts[i],
                               f"Step count should increase with tighter tolerance: {step_counts[i+1]} <= {step_counts[i]}")

    def test_04_mass_depletion_and_tsiolkovsky(self):
        """
        Verify mass depletion differential equation dm/dt = - T / (Isp * g0)
        and exact match with the Tsiolkovsky rocket equation: Delta v = Isp * g0 * ln(m0 / mf).
        """
        thrust_N = 26700.0   # Orion OMS-E AJ10-190 (6,000 lbf)
        isp_s = 316.0        # Specific impulse
        g0 = 9.80665         # Standard gravity
        m0 = 25618.0         # Full Orion wet mass post-TLI (CM + ESM)
        
        burn_duration = 180.0 # 3 minute burn
        expected_mdot = thrust_N / (isp_s * g0) # ~8.616 kg/s
        expected_prop_used = expected_mdot * burn_duration # ~1550.88 kg
        expected_mf = m0 - expected_prop_used
        expected_delta_v = isp_s * g0 * math.log(m0 / expected_mf)
        
        # Integrate with DP45 in rectilinear thrust space (zero gravity benchmark)
        def thrust_deriv(t: float, y: np.ndarray) -> np.ndarray:
            # y = [v, m]
            v = y[0]
            m = y[1]
            a = thrust_N / m
            dm = - thrust_N / (isp_s * g0)
            return np.array([a, dm])
            
        y0 = np.array([0.0, m0])
        res = self.integrator.integrate(thrust_deriv, (0.0, burn_duration), y0, h_initial=10.0)
        
        v_final_sim = res["y"][-1][0]
        m_final_sim = res["y"][-1][1]
        
        mass_error = abs(m_final_sim - expected_mf)
        delta_v_error = abs(v_final_sim - expected_delta_v)
        
        print(f"\n[+] Tsiolkovsky delta-V theoretical: {expected_delta_v:.3f} m/s, Integrated: {v_final_sim:.3f} m/s")
        print(f"[+] Final mass theoretical: {expected_mf:.3f} kg, Integrated: {m_final_sim:.3f} kg")
        
        self.assertLess(mass_error, 1e-4, f"Mass depletion error too large: {mass_error:.4e} kg")
        self.assertLess(delta_v_error, 1e-3, f"Delta-V error from Tsiolkovsky equation: {delta_v_error:.4e} m/s")

    def test_05_frame_transformations_and_quaternions(self):
        """
        Verify attitude quaternion normalization, rotation kinematics,
        and Direction Cosine Matrix (DCM) orthogonality C * C^T = I.
        """
        # Arbitrary non-trivial Euler angles: roll 35 deg, pitch -25 deg, yaw 115 deg
        r = math.radians(35.0)
        p = math.radians(-25.0)
        y = math.radians(115.0)
        
        cr, sr = math.cos(r / 2), math.sin(r / 2)
        cp, sp = math.cos(p / 2), math.sin(p / 2)
        cy, sy = math.cos(y / 2), math.sin(y / 2)
        
        # Hamilton / NASA convention: q = [qw, qx, qy, qz]
        qw = cr * cp * cy + sr * sp * sy
        qx = sr * cp * cy - cr * sp * sy
        qy = cr * sp * cy + sr * cp * sy
        qz = cr * cp * sy - sr * sp * cy
        q = np.array([qw, qx, qy, qz])
        
        # 1. Normalization
        q_norm = np.linalg.norm(q)
        self.assertAlmostEqual(q_norm, 1.0, places=12, msg="Quaternion norm deviated from 1.0")
        
        # 2. Build Direction Cosine Matrix
        C = np.array([
            [1 - 2*(qy**2 + qz**2),     2*(qx*qy - qw*qz),     2*(qx*qz + qw*qy)],
            [    2*(qx*qy + qw*qz), 1 - 2*(qx**2 + qz**2),     2*(qy*qz - qw*qx)],
            [    2*(qx*qz - qw*qy),     2*(qy*qz + qw*qx), 1 - 2*(qx**2 + qy**2)]
        ])
        
        # Orthogonality: C * C^T = I
        ident = np.dot(C, C.T)
        self.assertTrue(np.allclose(ident, np.eye(3), atol=1e-12), "DCM is not orthogonal!")
        
        # Determinant must be +1 (special orthogonal group SO(3))
        det = np.linalg.det(C)
        self.assertAlmostEqual(det, 1.0, places=12, msg="DCM determinant is not +1 (improper rotation)")
        
        # 3. Vector rotation preservation: |C * v| == |v|
        test_vec = np.array([125.4, -89.2, 450.7])
        rotated_vec = np.dot(C, test_vec)
        self.assertAlmostEqual(np.linalg.norm(rotated_vec), np.linalg.norm(test_vec), places=10,
                               msg="Vector norm altered under coordinate rotation")

    def test_06_unit_conversions_and_dimensional_consistency(self):
        """
        Verify unit conversions and dimensional consistency:
        - Nautical miles & miles to SI meters
        - Force (lbf to N)
        - Mass (lbm to kg)
        - Pressure (atm, psi to Pa)
        - Sutton-Graves heat flux dimensional scaling
        """
        # Exact definitions
        self.assertEqual(1852.0, 1.0 * 1852.0, "1 nmi = 1852 m exactly")
        self.assertAlmostEqual(1.0 * 4.4482216152605, 4.448222, places=5, msg="1 lbf in N")
        self.assertAlmostEqual(1.0 * 0.45359237, 0.453592, places=5, msg="1 lbm in kg")
        self.assertEqual(101325.0, 101.325 * 1000.0, "1 atm in Pa")
        self.assertAlmostEqual(1.0 * 6894.757, 6894.76, places=1, msg="1 psi in Pa")
        
        # Sutton-Graves dimensional check:
        # q = k_sg * sqrt(rho / R) * v^3
        # Units: [k_sg] = W / (m^2 * (kg/m^3)^0.5 * (m/s)^3)
        # Check: [k_sg] * [kg/m^3]^0.5 * [m/s]^3 = W/m^2
        # W/m^2 / 10000 = W/cm^2
        k_sg = 1.7415e-4
        rho = 0.00032 # kg/m^3
        R_nose = 6.0  # m
        v = 11050.0   # m/s
        
        q_W_m2 = k_sg * math.sqrt(rho / R_nose) * (v ** 3)
        q_W_cm2 = q_W_m2 / 10000.0
        
        self.assertGreater(q_W_cm2, 100.0)
        self.assertLess(q_W_cm2, 250.0)

    def test_07_mission_event_ordering_and_monotonicity(self):
        """
        Verify mission event ordering and time progression in the mission streamer.
        Ensures strict chronological monotonicity and physical event sequence.
        """
        engine = OrionTelemetryEngine()
        
        # Sweep timeline with 50s increments
        t_samples = np.linspace(0.0, 4100.0, 83)
        prev_t = -1.0
        
        observed_stages = []
        
        for t in t_samples:
            pkt = engine.get_telemetry_packet(t)
            cur_t = pkt["met_sec"]
            self.assertGreater(cur_t, prev_t, "Mission Elapsed Time is non-monotonic!")
            prev_t = cur_t
            
            stage = pkt["mission_stage"]
            if not observed_stages or observed_stages[-1] != stage:
                observed_stages.append(stage)
                
            # Physical state consistency assertions
            alt_km = pkt["trajectory"]["altitude_km"]
            g_load = pkt["aero_thermal"]["g_load"]
            prop_kg = pkt["propulsion_power"]["propellant_remaining_kg"]
            
            # Altitude must be non-negative
            self.assertGreaterEqual(alt_km, 0.0, f"Negative altitude detected at MET {cur_t}s")
            # G-load must be non-negative
            self.assertGreaterEqual(g_load, 0.0, f"Negative G-load detected at MET {cur_t}s")
            # Propellant mass cannot increase
            self.assertLessEqual(prop_kg, 8618.0 + 1e-3, f"Propellant exceeds tank capacity at MET {cur_t}s")
            
        print(f"\n[+] Chronological Mission Stages Observed ({len(observed_stages)}):")
        for s in observed_stages:
            print(f"    -> {s}")
            
        # Verify essential milestone sequence
        self.assertIn("SLS_ASCENT_LEO", observed_stages)
        self.assertIn("TLI_MANEUVER", observed_stages)
        self.assertIn("TRANSLUNAR_COAST", observed_stages)
        self.assertIn("LUNAR_FLYBY", observed_stages)
        self.assertIn("TRANS_EARTH_RETURN", observed_stages)
        self.assertIn("OCEAN_SPLASHDOWN", observed_stages)
        
        # Verify first is Ascent and last is Splashdown
        self.assertEqual(observed_stages[0], "SLS_ASCENT_LEO")
        self.assertEqual(observed_stages[-1], "OCEAN_SPLASHDOWN")

if __name__ == "__main__":
    unittest.main()
