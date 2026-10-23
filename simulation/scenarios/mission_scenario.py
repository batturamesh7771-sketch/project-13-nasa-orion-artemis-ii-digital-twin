"""
Artemis II Mission Scenario Manager & Event Registry.
Loads and enforces the official machine-readable Artemis II mission profile (artemis_ii_scenario.json).
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from simulation.core.state_machine import MissionPhase

SCENARIO_JSON_PATH = Path(__file__).resolve().parent / "artemis_ii_scenario.json"

class ArtemisMissionScenario:
    def __init__(self, scenario_path: Path = SCENARIO_JSON_PATH):
        self.scenario_path = scenario_path
        with open(scenario_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.metadata = self.data["mission_metadata"]
        self.constants = self.data["physical_constants"]
        self.vehicles = self.data["vehicle_configurations"]
        self.phases = self.data["chronological_flight_phases"]

        self._validate_scenario()

    def _validate_scenario(self):
        """Verify chronological causality, time monotonicity, and phase completeness."""
        prev_end = 0.0
        for i, phase in enumerate(self.phases):
            p_name = phase["phase_name"]
            start_t = phase["start_met_sec"]
            end_t = phase["end_met_sec"]

            if start_t > end_t:
                raise ValueError(f"Phase {p_name} has invalid duration: start {start_t} > end {end_t}")

            if i > 0 and start_t < prev_end - 1e-3:
                raise ValueError(f"Phase {p_name} overlaps previous phase: start {start_t} < prev_end {prev_end}")

            prev_end = end_t

            # Verify events inside phase
            prev_evt_t = start_t
            for evt in phase.get("events", []):
                evt_t = evt["met_sec"]
                if evt_t < prev_evt_t - 1e-3 or evt_t > end_t + 1e-3:
                    raise ValueError(f"Event {evt.get('event_name')} at {evt_t}s violates phase bounds [{start_t}, {end_t}]")
                prev_evt_t = evt_t

    def get_phase_at_met(self, met_sec: float) -> Dict[str, Any]:
        """Find the corresponding phase for a given Mission Elapsed Time in seconds."""
        t = max(0.0, met_sec)
        for phase in self.phases:
            if phase["start_met_sec"] <= t <= phase["end_met_sec"]:
                return phase
        return self.phases[-1]

    def get_phase_enum_at_met(self, met_sec: float) -> MissionPhase:
        p_dict = self.get_phase_at_met(met_sec)
        return MissionPhase(p_dict["phase_name"])

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Flatten and return all chronological flight milestones."""
        events = []
        for phase in self.phases:
            for evt in phase.get("events", []):
                evt_copy = evt.copy()
                evt_copy["phase_name"] = phase["phase_name"]
                events.append(evt_copy)
        return sorted(events, key=lambda x: x["met_sec"])

    def get_maneuvers(self) -> List[Dict[str, Any]]:
        """Return all delta-v maneuver burns across all stages."""
        return [evt for evt in self.get_all_events() if "delta_v_m_s" in evt]

    def get_orion_maneuvers(self) -> List[Dict[str, Any]]:
        """Return delta-v maneuver burns executed by Orion's European Service Module."""
        return [evt for evt in self.get_maneuvers() if evt.get("stage") == "ORION_ESM"]

    def get_icps_maneuvers(self) -> List[Dict[str, Any]]:
        """Return delta-v maneuver burns executed by the SLS ICPS stage."""
        return [evt for evt in self.get_maneuvers() if evt.get("stage") == "ICPS"]

    def get_total_mission_duration_sec(self) -> float:
        return float(self.phases[-1]["end_met_sec"])
