"""
Artemis II Mission State Machine & Shared State-Vector Data Contract.
Enforces:
  1. Strict typed state contract across physics engine, telemetry, and visualization.
  2. Physical and chronological phase transitions (guarded state machine).
  3. Provenance tracking: distinguishes [PHYSICS_SOLVER], [NASA_EPHEMERIS], and [CONFIGURABLE_ASSUMPTION].
"""

import math
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import numpy as np

class MissionPhase(str, Enum):
    SLS_ASCENT = "SLS_ASCENT"
    EARTH_ORBIT_CHECKOUT = "EARTH_ORBIT_CHECKOUT"
    TRANSLUNAR_INJECTION = "TRANSLUNAR_INJECTION"
    TRANSLUNAR_COAST = "TRANSLUNAR_COAST"
    LUNAR_FLYBY = "LUNAR_FLYBY"
    TRANS_EARTH_RETURN = "TRANS_EARTH_RETURN"
    ATMOSPHERIC_SKIP_ENTRY = "ATMOSPHERIC_SKIP_ENTRY"
    PARACHUTE_DESCENT_SPLASHDOWN = "PARACHUTE_DESCENT_SPLASHDOWN"
    MISSION_COMPLETE = "MISSION_COMPLETE"

@dataclass
class TrajectoryState:
    pos_eci_m: np.ndarray = field(default_factory=lambda: np.zeros(3))
    vel_eci_m_s: np.ndarray = field(default_factory=lambda: np.zeros(3))
    altitude_m: float = 0.0
    velocity_mag_m_s: float = 0.0
    mach_number: float = 0.0
    flight_path_angle_deg: float = 0.0
    dist_to_moon_m: float = 384400000.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pos_eci_km": [round(float(c) / 1000.0, 3) for c in self.pos_eci_m],
            "altitude_km": round(float(self.altitude_m) / 1000.0, 3),
            "velocity_m_s": round(float(self.velocity_mag_m_s), 2),
            "mach": round(float(self.mach_number), 2),
            "flight_path_deg": round(float(self.flight_path_angle_deg), 2),
            "dist_to_moon_km": round(float(self.dist_to_moon_m) / 1000.0, 1)
        }

@dataclass
class AttitudeState:
    quaternion: np.ndarray = field(default_factory=lambda: np.array([1.0, 0.0, 0.0, 0.0]))
    rates_deg_s: np.ndarray = field(default_factory=lambda: np.zeros(3))
    euler_angles_deg: np.ndarray = field(default_factory=lambda: np.zeros(3))
    bank_angle_deg: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quaternion": [round(float(q), 6) for q in self.quaternion],
            "roll_deg": round(float(self.euler_angles_deg[0]), 2),
            "pitch_deg": round(float(self.euler_angles_deg[1]), 2),
            "yaw_deg": round(float(self.euler_angles_deg[2]), 2),
            "rates_deg_s": [round(float(r), 4) for r in self.rates_deg_s],
            "bank_angle_deg": round(float(self.bank_angle_deg), 2)
        }

@dataclass
class AeroThermalState:
    g_load: float = 1.0
    dynamic_pressure_Pa: float = 0.0
    heat_flux_W_cm2: float = 0.0
    surface_temp_C: float = 20.0
    bondline_temp_C: float = 20.0
    surface_recession_mm: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "g_load": round(float(self.g_load), 2),
            "dynamic_pressure_kPa": round(float(self.dynamic_pressure_Pa) / 1000.0, 3),
            "heat_flux_W_cm2": round(float(self.heat_flux_W_cm2), 1),
            "surface_temp_C": round(float(self.surface_temp_C), 1),
            "bondline_temp_C": round(float(self.bondline_temp_C), 1),
            "recession_mm": round(float(self.surface_recession_mm), 2)
        }

@dataclass
class PropulsionPowerState:
    total_mass_kg: float = 25618.0
    propellant_remaining_kg: float = 8618.0
    omse_thrust_N: float = 0.0
    solar_power_W: float = 0.0
    battery_soc_pct: float = 100.0
    solar_array_tilt_deg: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_mass_kg": round(float(self.total_mass_kg), 1),
            "propellant_remaining_kg": round(float(self.propellant_remaining_kg), 1),
            "propellant_pct": round(float(self.propellant_remaining_kg) / 8618.0 * 100.0, 1),
            "omse_thrust_N": round(float(self.omse_thrust_N), 1),
            "solar_power_W": round(float(self.solar_power_W), 1),
            "solar_array_tilt_deg": round(float(self.solar_array_tilt_deg), 1),
            "battery_soc_pct": round(float(self.battery_soc_pct), 1)
        }

@dataclass
class RecoveryState:
    fbc_jettisoned: bool = False
    drogues_deployed: bool = False
    mains_deployed: bool = False
    splashdown: bool = False
    chute_state: str = "STOWED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fbc_jettisoned": self.fbc_jettisoned,
            "drogues_deployed": self.drogues_deployed,
            "mains_deployed": self.mains_deployed,
            "splashdown": self.splashdown,
            "chute_state": self.chute_state
        }

@dataclass
class VehicleState:
    """
    Unified, authoritative state vector contract for the Artemis II Digital Twin.
    """
    met_sec: float = 0.0
    timestamp_utc: str = "2026-09-15T14:00:00Z"
    phase: MissionPhase = MissionPhase.SLS_ASCENT
    data_provenance: str = "[PHYSICS_SOLVER]"
    trajectory: TrajectoryState = field(default_factory=TrajectoryState)
    attitude: AttitudeState = field(default_factory=AttitudeState)
    aero_thermal: AeroThermalState = field(default_factory=AeroThermalState)
    propulsion_power: PropulsionPowerState = field(default_factory=PropulsionPowerState)
    recovery: RecoveryState = field(default_factory=RecoveryState)

    def to_telemetry_packet(self) -> Dict[str, Any]:
        hours = int(self.met_sec // 3600)
        minutes = int((self.met_sec % 3600) // 60)
        secs = int(self.met_sec % 60)
        met_str = f"T+{hours:02d}:{minutes:02d}:{secs:02d}"

        return {
            "met_sec": round(self.met_sec, 2),
            "met_str": met_str,
            "timestamp_utc": self.timestamp_utc,
            "mission_stage": self.phase.value,
            "data_provenance": self.data_provenance,
            "trajectory": self.trajectory.to_dict(),
            "attitude": self.attitude.to_dict(),
            "aero_thermal": self.aero_thermal.to_dict(),
            "propulsion_power": self.propulsion_power.to_dict(),
            "recovery": self.recovery.to_dict()
        }


class ArtemisStateMachine:
    """
    Finite state machine governing Artemis II mission phase progression.
    Guards ensure state transitions satisfy physical and chronological laws.
    """
    ALLOWED_TRANSITIONS = {
        MissionPhase.SLS_ASCENT: {MissionPhase.EARTH_ORBIT_CHECKOUT},
        MissionPhase.EARTH_ORBIT_CHECKOUT: {MissionPhase.TRANSLUNAR_INJECTION},
        MissionPhase.TRANSLUNAR_INJECTION: {MissionPhase.TRANSLUNAR_COAST},
        MissionPhase.TRANSLUNAR_COAST: {MissionPhase.LUNAR_FLYBY},
        MissionPhase.LUNAR_FLYBY: {MissionPhase.TRANS_EARTH_RETURN},
        MissionPhase.TRANS_EARTH_RETURN: {MissionPhase.ATMOSPHERIC_SKIP_ENTRY},
        MissionPhase.ATMOSPHERIC_SKIP_ENTRY: {MissionPhase.PARACHUTE_DESCENT_SPLASHDOWN},
        MissionPhase.PARACHUTE_DESCENT_SPLASHDOWN: {MissionPhase.MISSION_COMPLETE},
        MissionPhase.MISSION_COMPLETE: set()
    }

    def __init__(self, initial_phase: MissionPhase = MissionPhase.SLS_ASCENT):
        self.current_phase = initial_phase
        self.phase_history = [(0.0, initial_phase)]

    def can_transition_to(self, new_phase: MissionPhase, current_state: VehicleState) -> Tuple[bool, str]:
        if new_phase == self.current_phase:
            return True, "Already in target phase"

        allowed = self.ALLOWED_TRANSITIONS.get(self.current_phase, set())
        if new_phase not in allowed:
            return False, f"Illegal transition from {self.current_phase.value} to {new_phase.value}"

        # Physical guard conditions
        if new_phase == MissionPhase.EARTH_ORBIT_CHECKOUT:
            if current_state.trajectory.altitude_m < 100000.0:
                return False, f"Altitude {current_state.trajectory.altitude_m}m too low for orbital insertion"
        elif new_phase == MissionPhase.ATMOSPHERIC_SKIP_ENTRY:
            if current_state.trajectory.altitude_m > 150000.0:
                return False, f"Spacecraft altitude {current_state.trajectory.altitude_m}m too high for entry interface"
        elif new_phase == MissionPhase.PARACHUTE_DESCENT_SPLASHDOWN:
            if current_state.trajectory.altitude_m > 10000.0:
                return False, f"Altitude {current_state.trajectory.altitude_m}m too high for parachute deployment"
        elif new_phase == MissionPhase.MISSION_COMPLETE:
            if not current_state.recovery.splashdown or current_state.trajectory.altitude_m > 5.0:
                return False, "Cannot complete mission before verified ocean splashdown"

        return True, "Transition valid"

    def transition_to(self, new_phase: MissionPhase, current_state: VehicleState) -> bool:
        can_trans, reason = self.can_transition_to(new_phase, current_state)
        if not can_trans:
            raise ValueError(f"State transition rejected: {reason}")

        if new_phase != self.current_phase:
            self.current_phase = new_phase
            current_state.phase = new_phase
            self.phase_history.append((current_state.met_sec, new_phase))
            return True
        return False
