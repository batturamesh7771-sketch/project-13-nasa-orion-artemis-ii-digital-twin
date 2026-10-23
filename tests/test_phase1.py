#!/usr/bin/env python3
"""
Unit and Integration Tests for Orion Digital Twin — Phase 1
Verifies environment setup, API keys, documentation completeness, and ephemeris parsing.
"""

import os
import sys
import json
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.verify_environment import run_all_checks, load_env
from scripts.test_horizons_api import fetch_lunar_ephemeris

class TestPhase1(unittest.TestCase):

    def test_01_config_and_env(self):
        env_file = BASE_DIR / "config" / ".env"
        self.assertTrue(env_file.exists(), ".env configuration file must exist")
        env_vars = load_env(env_file)
        self.assertIn("NASA_API_KEY", env_vars, "NASA_API_KEY must be in .env")
        self.assertIn("JPL_HORIZONS_API_URL", env_vars, "JPL_HORIZONS_API_URL must be in .env")
        self.assertTrue(len(env_vars["NASA_API_KEY"]) > 10, "NASA_API_KEY must be a valid non-empty string")

    def test_02_documentation_completeness(self):
        docs_dir = BASE_DIR / "docs"
        required_docs = [
            "ARCHITECTURE.md",
            "SPECS.md",
            "TIMELINE.md",
            "ASSUMPTIONS_AND_LIMITATIONS.md",
            "ROADMAP.md"
        ]
        for doc in required_docs:
            doc_path = docs_dir / doc
            self.assertTrue(doc_path.exists(), f"Document {doc} must exist")
            size = doc_path.stat().st_size
            self.assertGreater(size, 800, f"Document {doc} must contain comprehensive content (>800 bytes)")

    def test_03_environment_check_execution(self):
        report = run_all_checks()
        self.assertIn("system", report)
        self.assertIn("tools", report)
        self.assertTrue(report["tools"]["matlab"]["exists"], "MATLAB executable path must exist")
        self.assertTrue(report["tools"]["blender"]["exists"], "Blender executable path must exist")
        self.assertTrue(report["nasa_api"]["success"], "NASA API check must return HTTP 200")
        self.assertTrue(report["jpl_horizons"]["success"], "JPL Horizons API check must succeed")
        self.assertTrue(report["phase_1_ready"], "Phase 1 readiness flag must be true")

    def test_04_horizons_ephemeris_parser(self):
        records = fetch_lunar_ephemeris("2026-10-14", "2026-10-15", "1d")
        self.assertGreater(len(records), 0, "Must parse at least one lunar ephemeris vector")
        sample = records[0]
        self.assertIn("position_m", sample)
        self.assertIn("velocity_mps", sample)
        dist_km = sample["position_m"]["distance_km"]
        # Distance to Moon from Earth center is typically ~360,000 to 405,000 km
        self.assertTrue(350000 <= dist_km <= 415000, f"Lunar distance {dist_km} km must be within physical orbital bounds")
        speed_mps = sample["velocity_mps"]["speed_mps"]
        # Orbital speed of Moon is ~1000 m/s (0.9 to 1.1 km/s)
        self.assertTrue(900 <= speed_mps <= 1150, f"Lunar orbital speed {speed_mps} m/s must be within physical bounds")

if __name__ == "__main__":
    unittest.main()
