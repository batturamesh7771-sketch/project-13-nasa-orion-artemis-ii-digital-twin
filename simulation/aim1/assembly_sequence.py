"""
NASA Artemis II AIM 1 Assembly Sequence & Hardware Reconstruction.
Provides the deterministic 5-stage reconstruction workflow specified in:
  data/aim1_asset_manifest.json

Scenes:
  1. manufacturing_parts: Major hardware components and motor segments
  2. stack_in_vab: High Bay 3 stacking sequence on Mobile Launcher 1
  3. rollout: 4.2-mile Crawler-Transporter 2 rollout to LC-39B
  4. pad_ready: Terminal countdown and service tower configuration
  5. flight: Active numerical launch and ascent simulation
"""

from typing import Dict, List, Any


class AssemblySequenceManager:
    """
    State machine and component manifest for educational 3D reconstruction
    and assembly workflow of Artemis II SLS Block 1.
    """

    SCENES: List[Dict[str, Any]] = [
        {
            "scene_id": "manufacturing_parts",
            "title": "Major Hardware Components",
            "category": "EDUCATIONAL_RECONSTRUCTION",
            "status": "documented visual reconstruction",
            "description": "Exploded view of the primary SLS Block 1 flight elements prior to stacking.",
            "components": [
                {
                    "id": "srb_left",
                    "name": "Left Solid Rocket Booster (5-segment PBAN)",
                    "mass_kg": 725700,
                    "height_m": 53.9,
                    "manufacturer": "Northrop Grumman",
                    "facility": "Promontory, Utah"
                },
                {
                    "id": "srb_right",
                    "name": "Right Solid Rocket Booster (5-segment PBAN)",
                    "mass_kg": 725700,
                    "height_m": 53.9,
                    "manufacturer": "Northrop Grumman",
                    "facility": "Promontory, Utah"
                },
                {
                    "id": "core_stage",
                    "name": "SLS Core Stage (LOX/LH2)",
                    "mass_kg": 1072270,
                    "height_m": 64.6,
                    "manufacturer": "Boeing",
                    "facility": "Michoud Assembly Facility, New Orleans"
                },
                {
                    "id": "rs25_engines",
                    "name": "4x RS-25 Core Engines (E2047, E2059, E2062, E2063)",
                    "thrust_total_lbf": 2049200,
                    "manufacturer": "Aerojet Rocketdyne",
                    "facility": "Stennis Space Center, MS"
                },
                {
                    "id": "icps",
                    "name": "Interim Cryogenic Propulsion Stage (RL10B-2)",
                    "mass_kg": 30900,
                    "height_m": 13.7,
                    "manufacturer": "Boeing / United Launch Alliance",
                    "facility": "Decatur, Alabama"
                },
                {
                    "id": "orion_mpcv",
                    "name": "Orion Spacecraft (CM-003 Crew Module + ESM-2)",
                    "mass_kg": 25618,
                    "height_m": 7.9,
                    "manufacturer": "Lockheed Martin / ESA / Airbus",
                    "facility": "O&C Building, KSC / Bremen, Germany"
                },
                {
                    "id": "las",
                    "name": "Launch Abort System & Fairing Covers",
                    "mass_kg": 7500,
                    "height_m": 15.2,
                    "manufacturer": "Lockheed Martin",
                    "facility": "MPPF / LASF, KSC"
                }
            ]
        },
        {
            "scene_id": "stack_in_vab",
            "title": "VAB High Bay 3 Stacking Sequence",
            "category": "EDUCATIONAL_RECONSTRUCTION",
            "status": "educational reconstruction based on public descriptions/images",
            "description": "Integration on Mobile Launcher 1 inside Vehicle Assembly Building High Bay 3.",
            "steps": [
                {"step": 1, "name": "SRB Aft Skirts & Segments Stacked on ML-1", "duration_days": 45},
                {"step": 2, "name": "Core Stage Lifted & Mated Between Boosters", "duration_days": 14},
                {"step": 3, "name": "Launch Vehicle Stage Adapter (LVSA) Placed", "duration_days": 3},
                {"step": 4, "name": "ICPS Upper Stage Stacked on LVSA", "duration_days": 5},
                {"step": 5, "name": "Orion Spacecraft & LAS Mated to Stack", "duration_days": 7},
                {"step": 6, "name": "Integrated Modal Testing & Umbilical Verification", "duration_days": 21}
            ]
        },
        {
            "scene_id": "rollout",
            "title": "Mobile Launcher Rollout to LC-39B",
            "category": "DOCUMENTED_RECONSTRUCTION",
            "status": "documented visual reconstruction",
            "description": "Crawler-Transporter 2 carrying Mobile Launcher 1 and fully stacked SLS Block 1 across 4.2 miles of crushed river rock.",
            "metrics": {
                "distance_miles": 4.2,
                "distance_km": 6.8,
                "speed_mph": 0.8,
                "crawler_weight_lbs": 6650000,
                "total_rollout_mass_lbs": 21400000,
                "transit_time_hrs": 10.5
            }
        },
        {
            "scene_id": "pad_ready",
            "title": "LC-39B Pad Ready & Terminal Countdown",
            "category": "LAUNCH_OPERATIONS",
            "status": "sequence from public launch-day material; ground mechanics simplified",
            "description": "Pad LC-39B configured for Artemis II with sound suppression water, cryogenic loading, and terminal count.",
            "key_milestones": [
                {"time": "T-600s", "event": "Ground Launch Sequencer begins terminal count"},
                {"time": "T-480s", "event": "Crew Access Arm (CAA) retracts from Orion hatch"},
                {"time": "T-10s", "event": "Core-stage engine start commanded"},
                {"time": "T-6.36s", "event": "4x RS-25 engines startup sequence"},
                {"time": "T-0s", "event": "Twin SRB ignition, umbilical release, liftoff"}
            ]
        },
        {
            "scene_id": "flight",
            "title": "Numerical Launch & Ascent Flight",
            "category": "NUMERICAL_SIMULATION",
            "status": "must be driven by actual numerical state model",
            "description": "Active numerical 3-DOF Runge-Kutta simulation through staging, MECO, and orbital insertion."
        }
    ]

    @classmethod
    def get_scenes(cls) -> List[Dict[str, Any]]:
        return cls.SCENES

    @classmethod
    def get_scene(cls, scene_id: str) -> Dict[str, Any]:
        for s in cls.SCENES:
            if s["scene_id"] == scene_id:
                return s
        return cls.SCENES[0]
