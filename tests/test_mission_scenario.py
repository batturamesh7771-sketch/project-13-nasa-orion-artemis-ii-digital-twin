"""
Unit and Integration Tests for Artemis II Mission Scenario & State Machine Architecture.
"""

import math
import unittest
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

from simulation.core.state_machine import (
    MissionPhase,
    VehicleState,
    TrajectoryState,
    AttitudeState,
    AeroThermalState,
    PropulsionPowerState,
    RecoveryState,
    ArtemisStateMachine
)
from simulation.scenarios.mission_scenario import ArtemisMissionScenario

class TestArtemisMissionScenario(unittest.TestCase):
    def setUp(self):
        self.scenario = ArtemisMissionScenario()
        self.sm = ArtemisStateMachine()

    def test_01_scenario_json_schema_and_metadata(self):
        """Verify scenario JSON schema, official NASA citations, and crew roster."""
        meta = self.scenario.metadata
        self.assertEqual(meta["mission_name"], "NASA Artemis II")
        self.assertIn("Orion MPCV", meta["spacecraft"])
        self.assertIn("SLS Block 1", meta["launch_vehicle"])

        crew = meta["crew"]
        self.assertEqual(len(crew), 4, "Artemis II must have exactly 4 astronauts")
        crew_names = [c["name"] for c in crew]
        self.assertIn("Reid Wiseman", crew_names)
        self.assertIn("Victor Glover", crew_names)
        self.assertIn("Christina Koch", crew_names)
        self.assertIn("Jeremy Hansen", crew_names)

        citations = meta["source_citations"]
        self.assertGreaterEqual(len(citations), 2, "Must cite public NASA technical documentation")
        doc_ids = [c.get("doc_id", "") for c in citations]
        self.assertTrue(any("NP-2023" in d or "AIAA" in d for d in doc_ids))

    def test_02_chronological_ordering_and_monotonicity(self):
        """Verify all 8 phases are monotonically contiguous and non-overlapping."""
        phases = self.scenario.phases
        self.assertEqual(len(phases), 8, "Expected 8 official flight phases")

        expected_phase_names = [
            "SLS_ASCENT",
            "EARTH_ORBIT_CHECKOUT",
            "TRANSLUNAR_INJECTION",
            "TRANSLUNAR_COAST",
            "LUNAR_FLYBY",
            "TRANS_EARTH_RETURN",
            "ATMOSPHERIC_SKIP_ENTRY",
            "PARACHUTE_DESCENT_SPLASHDOWN"
        ]

        prev_end = 0.0
        for i, phase in enumerate(phases):
            self.assertEqual(phase["phase_name"], expected_phase_names[i])
            start_t = phase["start_met_sec"]
            end_t = phase["end_met_sec"]
            self.assertGreaterEqual(start_t, prev_end - 1e-3, f"Phase {phase['phase_name']} starts before prior phase ends")
            self.assertGreater(end_t, start_t, f"Phase {phase['phase_name']} has non-positive duration")
            prev_end = end_t

        # Verify all events are strictly sorted by MET
        events = self.scenario.get_all_events()
        self.assertGreaterEqual(len(events), 20, "Should register at least 20 flight events")
        for j in range(len(events) - 1):
            self.assertLessEqual(events[j]["met_sec"], events[j+1]["met_sec"],
                                 f"Event {events[j]['event_name']} out of chronological order")

    def test_03_delta_v_and_mass_budget_consistency(self):
        """Verify TLI rocket equation mass depletion and propellant budget."""
        all_maneuvers = self.scenario.get_maneuvers()
        orion_maneuvers = self.scenario.get_orion_maneuvers()
        icps_maneuvers = self.scenario.get_icps_maneuvers()

        self.assertGreaterEqual(len(orion_maneuvers), 4, "Must register TLI and OTC/TCM correction burns for Orion")
        self.assertEqual(len(icps_maneuvers), 2, "Must register ICPS PRM and ARM burns")

        tli = next(m for m in orion_maneuvers if m["event_name"] == "TLI_BURN")
        delta_v_tli = tli["delta_v_m_s"] # 1015 m/s
        self.assertGreaterEqual(delta_v_tli, 800.0)
        self.assertLessEqual(delta_v_tli, 1500.0)

        # Spacecraft mass properties
        orion = self.scenario.vehicles["orion_integrated_stack_at_tli"]
        m0 = orion["total_mass_kg"] # 25,618 kg
        prop_avail = orion["esm_usable_propellant_kg"] # 8,618 kg
        isp = orion["main_engine"]["isp_vacuum_s"] # 316 s
        g0 = self.scenario.constants["g0_m_s2"]

        # Theoretical TLI propellant consumed: dm = m0 * (1 - exp(-dv / (isp * g0)))
        dm_tli_theoretical = m0 * (1.0 - math.exp(- delta_v_tli / (isp * g0)))
        self.assertAlmostEqual(dm_tli_theoretical, 7140.0, delta=150.0)

        # Total Orion delta-V budget across TLI + OTCs + TCMs
        orion_total_dv = sum(m["delta_v_m_s"] for m in orion_maneuvers)
        orion_prop_consumed = m0 * (1.0 - math.exp(- orion_total_dv / (isp * g0)))
        
        print(f"\n[+] Orion ESM Maneuvers Total Delta-V : {orion_total_dv:.1f} m/s")
        print(f"[+] Orion ESM Propellant Consumed     : {orion_prop_consumed:.1f} kg (Budget: {prop_avail:.1f} kg)")
        self.assertLess(orion_prop_consumed, prop_avail, "Orion mission maneuvers exceed usable propellant capacity!")

    def test_04_state_machine_guarded_transitions(self):
        """Verify state machine allows legal transitions and enforces physical guards."""
        sm = ArtemisStateMachine()
        state = VehicleState()

        # Step 1: Ascent to Orbit
        state.trajectory.altitude_m = 50000.0 # too low for orbit
        can, reason = sm.can_transition_to(MissionPhase.EARTH_ORBIT_CHECKOUT, state)
        self.assertFalse(can, "Should reject orbital insertion below 100 km")

        state.trajectory.altitude_m = 185000.0
        self.assertTrue(sm.transition_to(MissionPhase.EARTH_ORBIT_CHECKOUT, state))
        self.assertEqual(sm.current_phase, MissionPhase.EARTH_ORBIT_CHECKOUT)

        # Illegal skip attempt: Earth Orbit -> Splashdown
        can_skip, reason = sm.can_transition_to(MissionPhase.PARACHUTE_DESCENT_SPLASHDOWN, state)
        self.assertFalse(can_skip, "Should reject illegal skip transition from Earth Orbit to Splashdown")

        # Step 2: Orbit -> TLI -> Coast -> Flyby -> Return
        self.assertTrue(sm.transition_to(MissionPhase.TRANSLUNAR_INJECTION, state))
        self.assertTrue(sm.transition_to(MissionPhase.TRANSLUNAR_COAST, state))
        self.assertTrue(sm.transition_to(MissionPhase.LUNAR_FLYBY, state))
        self.assertTrue(sm.transition_to(MissionPhase.TRANS_EARTH_RETURN, state))

        # Step 3: Return -> Entry Interface (alt must be <= 150 km)
        state.trajectory.altitude_m = 300000.0 # too high
        can_entry, _ = sm.can_transition_to(MissionPhase.ATMOSPHERIC_SKIP_ENTRY, state)
        self.assertFalse(can_entry, "Should reject Entry Interface above 150 km")

        state.trajectory.altitude_m = 120000.0
        self.assertTrue(sm.transition_to(MissionPhase.ATMOSPHERIC_SKIP_ENTRY, state))

        # Step 4: Entry -> Parachutes (alt must be <= 10 km)
        state.trajectory.altitude_m = 7600.0
        self.assertTrue(sm.transition_to(MissionPhase.PARACHUTE_DESCENT_SPLASHDOWN, state))

        # Step 5: Parachutes -> Complete (must have splashdown true and alt near 0)
        state.recovery.splashdown = False
        can_done, _ = sm.can_transition_to(MissionPhase.MISSION_COMPLETE, state)
        self.assertFalse(can_done, "Should reject Mission Complete before splashdown")

        state.recovery.splashdown = True
        state.trajectory.altitude_m = 0.0
        self.assertTrue(sm.transition_to(MissionPhase.MISSION_COMPLETE, state))
        self.assertEqual(sm.current_phase, MissionPhase.MISSION_COMPLETE)

    def test_05_unified_state_vector_data_contract(self):
        """Verify unified VehicleState contract serializes cleanly to JSON telemetry."""
        state = VehicleState(
            met_sec=864000.0,
            phase=MissionPhase.ATMOSPHERIC_SKIP_ENTRY,
            data_provenance="[PHYSICS_SOLVER]"
        )
        state.trajectory.pos_eci_m = np.array([6378137.0 + 120000.0, 0.0, 0.0])
        state.trajectory.vel_eci_m_s = np.array([0.0, 11050.0, 0.0])
        state.trajectory.altitude_m = 120000.0
        state.trajectory.velocity_mag_m_s = 11050.0
        state.trajectory.mach_number = 32.5
        state.trajectory.flight_path_angle_deg = -5.85

        state.aero_thermal.g_load = 1.05
        state.aero_thermal.heat_flux_W_cm2 = 12.0
        state.aero_thermal.surface_temp_C = 850.0
        state.aero_thermal.bondline_temp_C = 25.0

        packet = state.to_telemetry_packet()
        self.assertEqual(packet["mission_stage"], "ATMOSPHERIC_SKIP_ENTRY")
        self.assertEqual(packet["data_provenance"], "[PHYSICS_SOLVER]")
        self.assertEqual(packet["met_str"], "T+240:00:00")
        self.assertEqual(packet["trajectory"]["altitude_km"], 120.0)
        self.assertEqual(packet["trajectory"]["velocity_m_s"], 11050.0)
        self.assertEqual(packet["trajectory"]["mach"], 32.5)
        self.assertEqual(packet["trajectory"]["flight_path_deg"], -5.85)

if __name__ == "__main__":
    unittest.main()
