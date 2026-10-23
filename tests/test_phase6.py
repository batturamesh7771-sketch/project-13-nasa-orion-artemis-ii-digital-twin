"""
Automated Unit and Integration Test Suite — Phase 6: System Integration & End-to-End Verification
Validates Monte Carlo landing dispersion, statistical recovery ellipses, end-to-end integration,
and master demo harness for the NASA Orion MPCV Digital Twin.
"""

import os
import sys
import json
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from simulation.entry.monte_carlo_dispersion import OrionMonteCarloDispersion

class TestPhase6IntegrationAndVerification(unittest.TestCase):
    def setUp(self):
        self.mc_solver = OrionMonteCarloDispersion()

    def test_01_monte_carlo_execution_and_statistics(self):
        """Verify Monte Carlo stochastic flight dynamics and 100% splashdown safety."""
        # Run fast 30-sample Monte Carlo test
        res = self.mc_solver.run_monte_carlo(num_samples=30, seed=42)
        stats = res["statistics"]

        # 1. Total samples & 100% safe splashdown rate
        self.assertEqual(res["num_samples"], 30, "Incorrect sample count executed")
        self.assertEqual(res["success_rate_pct"], 100.0, "Mission recovery success rate was not 100%")

        # 2. Peak deceleration G-load limit (< 8.0 g human safety threshold)
        self.assertLess(stats["max_g_load"]["max"], 8.0, "Peak G-load exceeded NASA astronaut limit")
        self.assertGreater(stats["max_g_load"]["mean"], 3.0, "Deceleration too low for skip re-entry")

        # 3. Peak stagnation aerothermal heat flux (< 250 W/cm^2 Avcoat TPS limit)
        self.assertLess(stats["max_heat_flux_W_cm2"]["max"], 250.0, "Heat flux exceeded Avcoat TPS capability")
        self.assertGreater(stats["max_heat_flux_W_cm2"]["mean"], 100.0, "Heat flux unrealistically low for 11 km/s entry")

        # 4. Terminal parachute splashdown velocity (< 8.5 m/s)
        self.assertLessEqual(stats["terminal_velocity_m_s"]["max"], 8.5, "Terminal velocity exceeded parachute limit")
        self.assertGreater(stats["terminal_velocity_m_s"]["mean"], 6.5, "Terminal velocity unrealistically low")

    def test_02_dispersion_ellipse_and_recovery_zone(self):
        """Verify 3-sigma landing dispersion ellipse geometry and Pacific recovery zone capture."""
        res = self.mc_solver.run_monte_carlo(num_samples=30, seed=42)
        ellipse = res["dispersion_ellipse_3sigma"]
        stats = res["statistics"]

        # 1. Ellipse positive axes
        self.assertGreater(ellipse["semi_major_axis_km"], 0.0, "Semi-major axis must be positive")
        self.assertGreater(ellipse["semi_minor_axis_km"], 0.0, "Semi-minor axis must be positive")

        # 2. Semi-major should align along downrange (major >= minor)
        self.assertGreaterEqual(ellipse["semi_major_axis_km"], ellipse["semi_minor_axis_km"])

        # 3. Crossrange 3-sigma semi-minor axis bounded within recovery zone (< 20 km)
        self.assertLess(ellipse["semi_minor_axis_km"], 20.0, "Crossrange 3-sigma exceeded 20 km recovery boundary")

        # 4. Circular Error Probable (CEP - 50%) < 10 km
        self.assertLess(ellipse["cep_50_km"], 10.0, "CEP exceeded 10 km operational threshold")
        self.assertTrue(ellipse["recovery_zone_compliant"], "Recovery zone compliance flag was false")

    def test_03_exported_dispersion_telemetry(self):
        """Verify exported monte_carlo_dispersion.json telemetry structure and provenance."""
        mc_path = BASE_DIR / "telemetry" / "monte_carlo_dispersion.json"
        self.assertTrue(mc_path.exists(), "telemetry/monte_carlo_dispersion.json does not exist")

        with open(mc_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("statistics", data)
        self.assertIn("dispersion_ellipse_3sigma", data)
        self.assertIn("pacific_target", data)
        self.assertIn("runs", data)
        self.assertGreaterEqual(len(data["runs"]), 50, "Exported Monte Carlo should contain at least 50 runs")

        pacific = data["pacific_target"]
        self.assertIn("Pacific Ocean", pacific["landing_site"])
        self.assertIn("USS Portland", pacific["recovery_ship"])

    def test_04_end_to_end_project_deliverables(self):
        """Verify presence and integrity of all integrated artifacts from Phases 1 through 6."""
        required_files = [
            # Phase 1
            BASE_DIR / "config" / "environment_report.json",
            BASE_DIR / "docs" / "ARCHITECTURE.md",
            BASE_DIR / "docs" / "SPECS.md",
            BASE_DIR / "docs" / "TIMELINE.md",
            # Phase 2
            BASE_DIR / "cad" / "mass_properties.json",
            BASE_DIR / "cad" / "fusion360" / "Orion_Digital_Twin.py",
            BASE_DIR / "simulation" / "cfd" / "orion_capsule_reentry_cfd.stl",
            # Phase 3
            BASE_DIR / "simulation" / "matlab" / "core" / "orion_params.m",
            BASE_DIR / "telemetry" / "sample_lunar_ephemeris.json",
            BASE_DIR / "telemetry" / "mission_telemetry_simulated.json",
            # Phase 4
            BASE_DIR / "simulation" / "aero" / "modified_newtonian.py",
            BASE_DIR / "simulation" / "thermal" / "aerothermal_heating.py",
            BASE_DIR / "simulation" / "structures" / "pressure_vessel_analysis.py",
            BASE_DIR / "simulation" / "entry" / "entry_corridor_analysis.py",
            # Phase 5
            BASE_DIR / "web" / "server.py",
            BASE_DIR / "web" / "telemetry_streamer.py",
            BASE_DIR / "web" / "static" / "index.html",
            BASE_DIR / "web" / "static" / "js" / "spacecraft3d.js",
            # Phase 6
            BASE_DIR / "simulation" / "entry" / "monte_carlo_dispersion.py"
        ]

        for p in required_files:
            self.assertTrue(p.exists(), f"Required Phase asset missing: {p.relative_to(BASE_DIR)}")

if __name__ == "__main__":
    unittest.main()
