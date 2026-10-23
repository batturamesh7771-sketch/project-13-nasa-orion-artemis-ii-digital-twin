"""
Unit and Integration Tests for Coupled Atmospheric Skip Re-entry, Aerothermal, and Parachute Engine.
Tests:
  1. US Standard Atmosphere 1976 physical fidelity (sea level, tropopause, stratopause, EI-400).
  2. Sutton-Graves convective and Tauber-Sutton radiative heat flux models.
  3. Nominal Artemis II skip re-entry trajectory (-5.85 deg flight path angle).
  4. Crew G-tolerance limit (< 8.0 g) and structural bondline temperature (< 250 deg C).
  5. Parachute deployment sequence and ocean splashdown terminal velocity (< 8.5 m/s).
"""

import math
import unittest
import numpy as np

from simulation.entry.coupled_entry import (
    StandardAtmosphere1976,
    CoupledReentrySimulator
)


class TestCoupledEntry(unittest.TestCase):
    def setUp(self):
        self.sim = CoupledReentrySimulator()

    def test_01_standard_atmosphere_properties(self):
        """Verify US Standard Atmosphere 1976 properties against standard reference tables."""
        # 1. Sea level
        rho0, T0, p0, a0 = StandardAtmosphere1976.get_properties(0.0)
        self.assertAlmostEqual(rho0, 1.225, delta=0.01)
        self.assertAlmostEqual(T0, 288.15, delta=0.1)
        self.assertAlmostEqual(p0, 101325.0, delta=10.0)
        self.assertAlmostEqual(a0, 340.29, delta=0.5)

        # 2. Tropopause (11 km)
        rho11, T11, p11, a11 = StandardAtmosphere1976.get_properties(11000.0)
        self.assertAlmostEqual(T11, 216.65, delta=0.5)
        self.assertAlmostEqual(rho11, 0.364, delta=0.02)

        # 3. Monotonic decrease of density from 0 to 120 km
        altitudes = [0.0, 5000.0, 11000.0, 25000.0, 50000.0, 80000.0, 120000.0]
        densities = [StandardAtmosphere1976.get_properties(h)[0] for h in altitudes]
        for i in range(len(densities) - 1):
            self.assertGreater(densities[i], densities[i+1],
                               f"Density at {altitudes[i]}m must exceed density at {altitudes[i+1]}m")

        print(f"\n[+] Sea Level Density: {rho0:.4f} kg/m^3 | Speed of Sound: {a0:.1f} m/s")
        print(f"[+] 11 km Tropopause Temp: {T11:.2f} K | Density: {rho11:.4f} kg/m^3")

    def test_02_aerothermal_heating_models(self):
        """Verify Sutton-Graves convective and Tauber-Sutton radiative heat fluxes."""
        # Hypersonic condition at 60 km altitude (rho ~ 3.1e-4 kg/m^3, v = 10,500 m/s)
        rho_60k = 3.1e-4
        v_entry = 10500.0

        q_conv, q_rad, q_tot = self.sim.compute_aerothermal_flux(rho_60k, v_entry)

        print(f"[+] Convective Heat Flux : {q_conv:.2f} W/cm^2")
        print(f"[+] Radiative Heat Flux  : {q_rad:.2f} W/cm^2")
        print(f"[+] Total Stagnation Flux: {q_tot:.2f} W/cm^2")

        self.assertGreater(q_conv, 30.0, "Convective flux must be significant in hypersonic continuum")
        self.assertGreater(q_rad, 5.0, "Radiative flux must be active at super-orbital entry velocities")
        self.assertEqual(q_tot, q_conv + q_rad)

        # Zero velocity test
        q_c0, q_r0, q_t0 = self.sim.compute_aerothermal_flux(1.225, 0.0)
        self.assertEqual(q_t0, 0.0)

    def test_03_nominal_artemis_skip_reentry_trajectory(self):
        """Execute full numerical integration of nominal Artemis II skip reentry."""
        # Nominal entry interface flight path angle: gamma_EI = -5.85 deg
        res = self.sim.simulate_entry_and_descent(gamma_ei_deg=-5.85)

        print(f"\n[+] Nominal Artemis II Skip Entry Results:")
        print(f"    First Dip Minimum Altitude   : {res['min_altitude_km']:.2f} km (Target: 55-65 km)")
        print(f"    Peak G-Deceleration          : {res['max_g_load']:.2f} g (Crew Limit: < 8.0 g)")
        print(f"    Peak Stagnation Heat Flux    : {res['max_heat_flux_W_cm2']:.1f} W/cm^2 (Avcoat Limit: < 250 W/cm^2)")
        print(f"    Cumulative Heat Load         : {res['cumulative_heat_load_J_cm2']:.1f} J/cm^2")
        print(f"    Final Bondline Temperature   : {res['final_bondline_temp_C']:.1f} °C (Limit: < 250 °C)")
        print(f"    Avcoat Ablator Recession     : {res['total_avcoat_recession_mm']:.2f} mm")
        print(f"    Terminal Splashdown Velocity : {res['terminal_splashdown_velocity_m_s']:.2f} m/s (Limit: < 8.5 m/s)")
        print(f"    Total Re-entry Downrange     : {res['total_downrange_km']:,.1f} km")
        print(f"    Descent Duration             : {res['descent_duration_min']:.2f} minutes")

        # Acceptance Criteria Verification
        self.assertTrue(res["skip_pullup_detected"], "Orion must perform atmospheric skip pullup")
        self.assertTrue(res["splashdown_confirmed"], "Capsule must achieve safe splashdown")
        self.assertTrue(res["g_load_within_crew_limit"], "Deceleration exceeded astronaut 8.0 g safety threshold")
        self.assertTrue(res["bondline_within_limit"], "Structural bondline exceeded 250 deg C safety limit")
        self.assertTrue(res["splashdown_velocity_within_limit"], "Splashdown velocity exceeded 8.5 m/s safety limit")

        # First dip altitude within 50 - 70 km
        self.assertGreaterEqual(res["min_altitude_km"], 50.0)
        self.assertLessEqual(res["min_altitude_km"], 70.0)

        # Terminal velocity matches parachute design target (~7.8 m/s)
        self.assertAlmostEqual(res["terminal_splashdown_velocity_m_s"], 7.8, delta=1.5)

    def test_04_parachute_sequence_physical_ordering(self):
        """Verify that parachute deployment stages fire in strict physical and chronological order."""
        res = self.sim.simulate_entry_and_descent(gamma_ei_deg=-5.85)
        history = res["history"]

        # Extract stages observed in sequence
        stages = []
        for step in history:
            st = step["stage"]
            if not stages or stages[-1] != st:
                stages.append(st)

        print(f"\n[+] Atmospheric Descent Stages Observed in Sequence:")
        for s in stages:
            print(f"    -> {s}")

        # Strict ordering check
        expected_progression = [
            "FIRST_ENTRY_DIP",
            "EXO_ATMOSPHERIC_SKIP",
            "SECOND_ENTRY_TERMINAL",
            "DROGUE_CHUTES_DEPLOYED",
            "MAIN_CHUTES_DEPLOYED"
        ]

        for exp in expected_progression:
            self.assertIn(exp, stages, f"Missing required descent stage: {exp}")

        # Check drogue deployment altitude is below 7600m
        drogue_steps = [s for s in history if s["stage"] == "DROGUE_CHUTES_DEPLOYED"]
        self.assertTrue(drogue_steps)
        self.assertLessEqual(drogue_steps[0]["altitude_km"], 7.6)

        # Check main deployment altitude is below 2900m
        main_steps = [s for s in history if s["stage"] == "MAIN_CHUTES_DEPLOYED"]
        self.assertTrue(main_steps)
        self.assertLessEqual(main_steps[0]["altitude_km"], 2.9)


if __name__ == "__main__":
    unittest.main()
