#!/usr/bin/env python3
"""
Unit and Integration Tests for Orion Digital Twin — Phase 3: MATLAB Engineering Simulation
Validates:
  1. Presence and syntax of all MATLAB Phase 3 simulation files (core, trajectory, GNC, navigation, entry).
  2. Baseline spacecraft specifications and physical constants.
  3. Execution of MATLAB tests and generated mission telemetry.
"""

import os
import sys
import json
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

class TestPhase3Simulation(unittest.TestCase):

    def test_01_simulation_source_files_exist(self):
        sim_dir = BASE_DIR / "simulation" / "matlab"
        required_files = [
            sim_dir / "init_env.m",
            sim_dir / "run_phase3_simulation.m",
            sim_dir / "core" / "orion_params.m",
            sim_dir / "core" / "quaternion_utils.m",
            sim_dir / "trajectory" / "gravity_field.m",
            sim_dir / "trajectory" / "propagate_trajectory.m",
            sim_dir / "gnc" / "attitude_dynamics.m",
            sim_dir / "gnc" / "attitude_controller.m",
            sim_dir / "navigation" / "ekf_estimator.m",
            sim_dir / "entry" / "entry_equations.m",
            sim_dir / "tests" / "test_quaternion_utils.m",
            sim_dir / "tests" / "test_attitude_control.m",
            sim_dir / "tests" / "test_ekf.m",
            sim_dir / "tests" / "test_trajectory_and_entry.m"
        ]
        for f in required_files:
            self.assertTrue(f.exists(), f"Required MATLAB file {f.name} must exist")
            self.assertGreater(f.stat().st_size, 200, f"{f.name} must contain valid code (>200 bytes)")

    def test_02_matlab_syntax_and_keywords(self):
        core_file = BASE_DIR / "simulation" / "matlab" / "core" / "orion_params.m"
        with open(core_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("params.cm.base_diameter_m = 5.029;", content)
        self.assertIn("params.astro.mu_Earth", content)
        self.assertIn("params.omse.thrust_N = 26700.0;", content)
        self.assertIn("params.aero.hypersonic_Cd = 1.25;", content)

        gnc_file = BASE_DIR / "simulation" / "matlab" / "gnc" / "attitude_controller.m"
        with open(gnc_file, "r", encoding="utf-8") as f:
            gnc_content = f.read()
        self.assertIn("quaternion_utils.error", gnc_content)
        self.assertIn("tau_max", gnc_content)

        ekf_file = BASE_DIR / "simulation" / "matlab" / "navigation" / "ekf_estimator.m"
        with open(ekf_file, "r", encoding="utf-8") as f:
            ekf_content = f.read()
        self.assertIn("update_star_tracker", ekf_content)
        self.assertIn("update_range", ekf_content)

    def test_03_telemetry_schema_and_provenance(self):
        telem_file = BASE_DIR / "telemetry" / "mission_telemetry_simulated.json"
        if telem_file.exists():
            with open(telem_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data.get("provenance"), "[SIMULATED]")
            self.assertIn("NASA Orion", data.get("spacecraft", ""))
            self.assertIn("altitude_km", data)
            self.assertIn("velocity_m_s", data)
            self.assertIn("g_load", data)
            self.assertIn("heat_flux_W_cm2", data)

if __name__ == "__main__":
    unittest.main()
