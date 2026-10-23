"""
Unit tests for NASA Artemis II AIM 1 to AIM 2 Orbital Operations & Post-TLI Handoff.
Validates:
  1. ICPS orbital operations (PRM-1, Apogee Raise to 68,000 km, Orion separation).
  2. Orion Flight Day 2 TLI burn (90,840 s, 350 s duration, delta-v 388.3 m/s, mass drop 25,618 kg -> 22,864 kg).
  3. Strict validation against schemas/aim1_to_aim2_state.schema.json.
  4. Numerical injection into AIM 2 ArtemisMissionPropagator.
"""

import math
import unittest
import numpy as np

from simulation.aim1.vehicle_config import SLSBlock1Config
from simulation.aim1.ascent_dynamics import SLSAscentPropagator
from simulation.aim1.orbital_operations import OrbitalOperationsPropagator
from simulation.aim1.handoff_adapter import AIM1HandoffAdapter
from simulation.trajectory.mission_propagator import ArtemisMissionPropagator


class TestAIM1ToAIM2Handoff(unittest.TestCase):
    def setUp(self):
        self.config = SLSBlock1Config()
        self.ascent_prop = SLSAscentPropagator(config=self.config)
        self.orbital_prop = OrbitalOperationsPropagator(config=self.config)

    def test_01_orbital_operations_and_tli_burn(self):
        ascent_res = self.ascent_prop.propagate_ascent()
        insertion_state = ascent_res["insertion_state_t494"]

        orbital_res = self.orbital_prop.execute_complete_aim1_orbital_mission(insertion_state)
        self.assertEqual(orbital_res["status"], "PASS")

        post_tli = orbital_res["post_tli_state"]
        self.assertEqual(post_tli["epoch_utc"], "2026-04-02T23:54:50Z")
        self.assertEqual(post_tli["met_s"], 91190.0)
        self.assertEqual(post_tli["burn_duration_s"], 350.0)

        # Delta-V check: ~388.3 m/s (1,274 ft/s)
        self.assertAlmostEqual(post_tli["delta_v_scalar_m_s"], 388.32, delta=20.0)

        # Mass check: Orion wet mass 25,618 kg burns ~2,754-3,015 kg propellant -> ~22,600-22,864 kg
        self.assertAlmostEqual(post_tli["mass_kg"], 22864.0, delta=300.0)

        # Events check
        event_ids = [e["event_id"] for e in orbital_res["events"]]
        self.assertIn("icps_rl10_nozzle_extension", event_ids)
        self.assertIn("solar_array_deployment", event_ids)
        self.assertIn("perigee_raise_1", event_ids)
        self.assertIn("apogee_raise", event_ids)
        self.assertIn("orion_icps_separation", event_ids)
        self.assertIn("icps_disposal_burn", event_ids)
        self.assertIn("orion_tli_burn", event_ids)

    def test_02_handoff_adapter_schema_validation(self):
        sample_post_tli = {
            "epoch_utc": "2026-04-02T23:54:50Z",
            "met_s": 91190.0,
            "position_eci_m": [6500000.0, 100000.0, 200000.0],
            "velocity_eci_m_s": [1000.0, 10500.0, 500.0],
            "mass_kg": 22864.0,
            "delta_v_vector_m_s": [35.0, 385.0, 15.0],
            "burn_duration_s": 350.0
        }

        # Build payload
        payload = AIM1HandoffAdapter.build_handoff_payload(sample_post_tli)
        self.assertEqual(payload["schema_version"], "1.0.0")
        self.assertEqual(payload["mission_id"], "ARTEMIS_II")
        self.assertEqual(payload["handoff_event"], "POST_TLI_BURN")
        self.assertEqual(payload["vehicle_configuration"], "ORION_WITH_EUROPEAN_SERVICE_MODULE")
        self.assertEqual(payload["mass_kg"], 22864.0)

        # Validation should succeed
        self.assertTrue(AIM1HandoffAdapter.validate_handoff_payload(payload))

        # Extract state vector
        state_vec = AIM1HandoffAdapter.extract_state_vector(payload)
        self.assertEqual(len(state_vec), 7)
        self.assertEqual(state_vec[6], 22864.0)

        # Test failure on invalid payload
        invalid_payload = dict(payload)
        del invalid_payload["burn"]
        with self.assertRaises(ValueError):
            AIM1HandoffAdapter.validate_handoff_payload(invalid_payload)

    def test_03_injection_into_aim2_mission_propagator(self):
        # Create modeled post-TLI state vector
        r_earth = 6378137.0 + 185000.0
        inc_rad = math.radians(28.5)
        # Vis-viva speed post-TLI targeting lunar free-return trajectory: ~10,950 m/s
        v_tli = 10950.0
        pos = [r_earth * math.cos(inc_rad), 0.0, r_earth * math.sin(inc_rad)]
        vel = [0.0, v_tli, 0.0]
        mass = 22864.0

        sample_post_tli = {
            "epoch_utc": "2026-04-02T23:54:50Z",
            "met_s": 91190.0,
            "position_eci_m": pos,
            "velocity_eci_m_s": vel,
            "mass_kg": mass,
            "delta_v_vector_m_s": [0.0, 388.32, 0.0],
            "burn_duration_s": 350.0
        }

        payload = AIM1HandoffAdapter.build_handoff_payload(sample_post_tli)
        state_vec = AIM1HandoffAdapter.extract_state_vector(payload)

        # Propagate AIM 2 using this state vector with 1800s sampling step
        aim2_prop = ArtemisMissionPropagator()
        telemetry = aim2_prop.generate_full_mission_profile(sample_interval_sec=1800.0, initial_state=state_vec)

        self.assertGreater(len(telemetry), 20)
        # Verify first telemetry record preserves post-TLI state
        self.assertAlmostEqual(telemetry[0]["mass_kg"], 22864.0, delta=10.0)
        self.assertGreater(telemetry[0]["speed_earth_km_s"], 9.0)
        self.assertLess(telemetry[0]["speed_earth_km_s"], 11.5)


if __name__ == "__main__":
    unittest.main()
