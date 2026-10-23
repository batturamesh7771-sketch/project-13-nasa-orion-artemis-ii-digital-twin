"""
Unit tests for NASA Artemis II AIM 1 SLS Block 1 Ascent Dynamics Simulation.
Validates:
  1. SLS Block 1 configuration and truth classes
  2. Rotating-Earth pad initial state (LC-39B)
  3. US76 atmospheric density and transonic drag coefficient Cd(M)
  4. Powered ascent integration and staging events (SRB sep, LAS sep, MECO)
"""

import math
import unittest
import numpy as np

from simulation.aim1.vehicle_config import SLSBlock1Config
from simulation.aim1.ascent_dynamics import SLSAscentPropagator
from simulation.entry.coupled_entry import StandardAtmosphere1976

class TestAIM1Ascent(unittest.TestCase):
    def setUp(self):
        self.config = SLSBlock1Config()
        self.propagator = SLSAscentPropagator(config=self.config)

    def test_01_sls_block1_config_truth(self):
        self.assertEqual(self.config.TOTAL_STACK_HEIGHT_M, 98.27)
        self.assertEqual(self.config.LIFTOFF_MASS_KG, 2604000.0)
        self.assertEqual(self.config.RS25_ENGINE_COUNT, 4)
        self.assertEqual(self.config.SRB_COUNT, 2)
        self.assertAlmostEqual(self.config.LAUNCH_LAT_DEG, 28.608389, places=4)

        # Test JSON loaders
        sources = self.config.load_source_registry()
        self.assertIn("sources", sources)
        self.assertGreaterEqual(len(sources["sources"]), 10)

        events = self.config.load_launch_events()
        self.assertIn("ascent_events", events)
        self.assertIn("tli_reference", events)

    def test_02_launch_site_initial_state_earth_rotation(self):
        pos0, vel0 = self.propagator.get_launch_site_initial_state()

        r0_mag = float(np.linalg.norm(pos0))
        # Check pad radius: Earth radius + pad altitude
        self.assertTrue(6370000.0 < r0_mag < 6385000.0)

        # Diurnal rotational velocity at KSC (28.6 deg lat): v = omega * r * cos(lat) ~ 408.6 m/s
        v0_mag = float(np.linalg.norm(vel0))
        self.assertTrue(400.0 < v0_mag < 420.0)
        # Velocity must be primarily eastward (positive in inertial tangent)
        self.assertEqual(vel0[2], 0.0) # Pure equatorial spin around Z axis

    def test_03_aerodynamic_cd_transonic_curve(self):
        # Subsonic
        cd_sub = SLSAscentPropagator.get_aerodynamic_cd(0.5)
        self.assertEqual(cd_sub, 0.28)

        # Transonic peak near Mach 1.05 - 1.2
        cd_trans = SLSAscentPropagator.get_aerodynamic_cd(1.05)
        self.assertAlmostEqual(cd_trans, 0.46, places=2)

        # Hypersonic decay
        cd_hyper = SLSAscentPropagator.get_aerodynamic_cd(10.0)
        self.assertEqual(cd_hyper, 0.26)

    def test_04_propagate_ascent_end_to_end(self):
        res = self.propagator.propagate_ascent()

        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["model_fidelity"], "3DOF_REDUCED_ORDER")

        # Check Max-Q detection
        max_q = res["max_q"]
        self.assertGreater(max_q["value_kpa"], 25.0)
        self.assertTrue(50.0 <= max_q["met_s"] <= 90.0)

        # Check Staging Events
        event_ids = [e["event_id"] for e in res["events"]]
        self.assertIn("liftoff", event_ids)
        self.assertIn("max_q", event_ids)
        self.assertIn("srb_separation", event_ids)
        self.assertIn("las_jettison", event_ids)
        self.assertIn("core_meco", event_ids)
        self.assertIn("core_separation", event_ids)

        # Check MECO altitude and velocity
        insertion = res["insertion_state_t494"]
        self.assertGreater(insertion["altitude_km"], 140.0)
        self.assertGreater(insertion["velocity_m_s"], 7400.0)
        # Verify mass dropped appropriately from 2.6M kg liftoff
        self.assertLess(insertion["mass_kg"], 70000.0) # ICPS + Orion stack


if __name__ == "__main__":
    unittest.main()
