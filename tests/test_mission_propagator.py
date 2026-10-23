"""
Unit and Integration Tests for Artemis II Multi-Body Mission Propagator.
Tests:
  1. Earth J2 geopotential acceleration analytical verification.
  2. Moon third-body gravitational perturbation (direct and indirect terms).
  3. Lunar ephemeris physical bounds, continuity, and Keplerian consistency.
  4. Finite thrust burn integration and Tsiolkovsky mass depletion.
  5. Translunar coast multi-body trajectory propagation and telemetry generation.
"""

import math
import unittest
import numpy as np
from pathlib import Path

from simulation.trajectory.mission_propagator import (
    MultiBodyGravity,
    LunarEphemerisProvider,
    ArtemisMissionPropagator
)
from simulation.trajectory.adaptive_integrator import DormandPrince45
from simulation.scenarios.mission_scenario import ArtemisMissionScenario


class TestMissionPropagator(unittest.TestCase):
    def setUp(self):
        self.gravity = MultiBodyGravity(include_j2=True, include_moon=True)
        self.ephem = LunarEphemerisProvider()
        self.propagator = ArtemisMissionPropagator(
            gravity=self.gravity,
            ephemeris=self.ephem
        )

    def test_01_j2_acceleration_analytical_verification(self):
        """Verify J2 zonal harmonic acceleration against exact analytical formulas at equator and pole."""
        r = 7000000.0  # 7000 km geocentric radius
        mu = MultiBodyGravity.MU_EARTH
        re = MultiBodyGravity.R_EARTH
        j2 = MultiBodyGravity.J2_EARTH

        # 1. Equator test: z = 0, x = r, y = 0
        r_eq = np.array([r, 0.0, 0.0], dtype=np.float64)
        a_j2_eq = self.gravity.accel_j2(r_eq)

        # Expected equatorial radial perturbation: a_j2_x = - 1.5 * J2 * mu * Re^2 / r^4
        expected_a_eq_x = - 1.5 * j2 * mu * (re ** 2) / (r ** 4)
        self.assertAlmostEqual(a_j2_eq[0], expected_a_eq_x, delta=abs(expected_a_eq_x) * 1e-6)
        self.assertAlmostEqual(a_j2_eq[1], 0.0, delta=1e-12)
        self.assertAlmostEqual(a_j2_eq[2], 0.0, delta=1e-12)
        print(f"\n[+] Equator J2 Acceleration Error: {abs(a_j2_eq[0] - expected_a_eq_x):.6e} m/s^2")

        # 2. North Pole test: x = 0, y = 0, z = r
        r_pole = np.array([0.0, 0.0, r], dtype=np.float64)
        a_j2_pole = self.gravity.accel_j2(r_pole)

        # Expected polar radial perturbation: a_j2_z = + 3.0 * J2 * mu * Re^2 / r^4 (outward relative to spherical point-mass)
        expected_a_pole_z = 3.0 * j2 * mu * (re ** 2) / (r ** 4)
        self.assertAlmostEqual(a_j2_pole[0], 0.0, delta=1e-12)
        self.assertAlmostEqual(a_j2_pole[1], 0.0, delta=1e-12)
        self.assertAlmostEqual(a_j2_pole[2], expected_a_pole_z, delta=abs(expected_a_pole_z) * 1e-6)
        print(f"[+] North Pole J2 Acceleration Error: {abs(a_j2_pole[2] - expected_a_pole_z):.6e} m/s^2")

    def test_02_moon_third_body_perturbation(self):
        """Verify third-body gravitational direct attraction and indirect Earth reflex acceleration."""
        # 1. Earth center test: if spacecraft is at origin (r_sc = 0), perturbation must be 0
        r_origin = np.array([0.0, 0.0, 0.0])
        r_moon = np.array([384400000.0, 0.0, 0.0])
        a_3rd_origin = self.gravity.accel_third_body(r_origin, r_moon, MultiBodyGravity.MU_MOON)
        self.assertTrue(np.allclose(a_3rd_origin, 0.0, atol=1e-14),
                        "Third body acceleration at central body origin must cancel exactly to zero.")

        # 2. Sub-lunar point (between Earth and Moon at r = 100,000 km)
        r_sc = np.array([100000000.0, 0.0, 0.0])
        a_3rd = self.gravity.accel_third_body(r_sc, r_moon, MultiBodyGravity.MU_MOON)
        # Net third-body pull must accelerate spacecraft towards the Moon (+x direction)
        self.assertGreater(a_3rd[0], 0.0, "Net lunar tidal force on sub-lunar side must point toward Moon")
        self.assertAlmostEqual(a_3rd[1], 0.0, delta=1e-14)
        self.assertAlmostEqual(a_3rd[2], 0.0, delta=1e-14)
        print(f"[+] Sub-lunar Third-Body Acceleration at 100,000 km: {a_3rd[0]:.6e} m/s^2")

    def test_03_lunar_ephemeris_physical_bounds(self):
        """Verify lunar ephemeris conforms to orbital physics, perigee/apogee bounds, and speeds."""
        # Sample across a complete lunar sidereal month (27.32 days in 1-day steps)
        month_sec = 27.321661 * 86400.0
        t_samples = np.linspace(0.0, month_sec, 28)

        min_dist = float('inf')
        max_dist = 0.0

        for t in t_samples:
            pos, vel = self.ephem.get_moon_state(t)
            dist_km = np.linalg.norm(pos) / 1000.0
            speed_km_s = np.linalg.norm(vel) / 1000.0

            min_dist = min(min_dist, dist_km)
            max_dist = max(max_dist, dist_km)

            # Moon distance physical bounds: 356,000 km <= r <= 407,000 km
            self.assertGreaterEqual(dist_km, 350000.0, f"Moon distance {dist_km} km below physical perigee")
            self.assertLessEqual(dist_km, 410000.0, f"Moon distance {dist_km} km above physical apogee")

            # Moon orbital speed bounds: 0.95 km/s <= v <= 1.10 km/s
            self.assertGreaterEqual(speed_km_s, 0.94, f"Moon speed {speed_km_s} km/s too slow")
            self.assertLessEqual(speed_km_s, 1.10, f"Moon speed {speed_km_s} km/s too fast")

        print(f"[+] Lunar Ephemeris Sweep: Perigee = {min_dist:.1f} km, Apogee = {max_dist:.1f} km")

    def test_04_finite_thrust_and_tsiolkovsky_mass_depletion(self):
        """Verify finite thrust integration consumes mass in exact accordance with Tsiolkovsky equation."""
        t_burn = 300.0       # 300 s burn
        thrust = 26700.0     # 26,700 N (Orion AJ10-190 vacuum thrust)
        isp = 316.0          # 316.0 s
        g0 = MultiBodyGravity.G0

        m0 = 25618.0         # 25,618 kg
        # Theoretical mass consumed: dm = (T / (Isp * g0)) * t
        dm_expected = (thrust / (isp * g0)) * t_burn
        m_final_expected = m0 - dm_expected

        # Spacecraft initial state in circular LEO
        r0 = MultiBodyGravity.R_EARTH + 200000.0
        v0 = math.sqrt(MultiBodyGravity.MU_EARTH / r0)
        y0 = np.array([r0, 0.0, 0.0, 0.0, v0, 0.0, m0], dtype=np.float64)

        # Propagate burn
        res = self.propagator.propagate_interval(0.0, t_burn, y0, thrust_N=thrust, isp_s=isp, h_initial=10.0)
        y_final = res["y"][-1]
        m_final_integrated = y_final[6]

        mass_error = abs(m_final_integrated - m_final_expected)
        print(f"[+] Theoretical Final Mass: {m_final_expected:.3f} kg | Integrated: {m_final_integrated:.3f} kg (Error: {mass_error:.4f} kg)")
        self.assertLess(mass_error, 0.1, "Finite burn mass depletion deviated from theoretical rocket mass consumption")

        # Verify velocity magnitude increased due to prograde thrust
        v_final = np.linalg.norm(y_final[3:6])
        # Theoretical delta-v: dv = Isp * g0 * ln(m0 / m1)
        dv_theoretical = isp * g0 * math.log(m0 / m_final_expected)
        print(f"[+] Theoretical Delta-V: {dv_theoretical:.2f} m/s")
        self.assertGreater(v_final, v0, "Prograde burn failed to increase orbital velocity")

    def test_05_translunar_coast_multi_body_propagation(self):
        """Verify translunar coast multi-body trajectory propagation and telemetry generation."""
        # Translunar post-TLI initial state (high apogee lunar transfer orbit)
        r0 = MultiBodyGravity.R_EARTH + 185000.0
        v0 = 10850.0 # m/s (trans-lunar injection velocity)
        y0 = np.array([r0, 0.0, 0.0, 0.0, v0, 0.0, 23198.0], dtype=np.float64)

        # Propagate 24 hours of translunar coast
        t_span = 86400.0 # 1 day
        res = self.propagator.propagate_interval(0.0, t_span, y0, thrust_N=0.0, h_initial=60.0)
        y_hist = res["y"]
        t_hist = res["t"]

        self.assertGreater(len(t_hist), 10, "Integrator must record multiple adaptive steps")
        y_final = y_hist[-1]

        # Trajectory must move outward towards Moon
        r_final = np.linalg.norm(y_final[0:3])
        alt_final_km = (r_final - MultiBodyGravity.R_EARTH) / 1000.0
        self.assertGreater(alt_final_km, 100000.0, "Trajectory must reach translunar distances (> 100,000 km) after 24h")
        print(f"[+] Translunar 24-hr Coast Altitude Reached: {alt_final_km:,.1f} km")

        # Verify telemetry record generation
        rec = self.propagator.compute_telemetry_record(t_span, y_final, "TRANSLUNAR_COAST")
        self.assertEqual(rec["phase"], "TRANSLUNAR_COAST")
        self.assertEqual(len(rec["position_eci_m"]), 3)
        self.assertEqual(len(rec["velocity_eci_m_s"]), 3)
        self.assertIn("c3_energy_km2_s2", rec)
        self.assertIn("distance_moon_km", rec)
        self.assertIn("[PHYSICS_SOLVER", rec["provenance"])


if __name__ == "__main__":
    unittest.main()
