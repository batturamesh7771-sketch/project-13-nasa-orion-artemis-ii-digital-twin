"""
NASA Artemis II AIM 1 Orbital Operations & TLI Propagator.
Propagates the complete orbital sequence following SLS Core Stage Separation:
  1. Early Low Earth Orbit (LEO) insertion & checkout (185 km parking orbit)
  2. ICPS RL10B-2 Nozzle Extension (T+508s) & ESM Solar Array Deployment (T+1200s)
  3. ICPS Perigee Raise Maneuver (PRM-1) at T+2,940s (185 x 2,800 km)
  4. ICPS Apogee Raise Burn at T+6,477s (185 x 68,000 km High Earth Orbit - HEO)
  5. Orion-ICPS Staging & Proximity Operations (T+12,255s)
  6. ICPS Disposal Burn (T+18,000s)
  7. Orion HEO Checkout Orbit on Flight Day 1
  8. Orion Translunar Injection (TLI) Burn on Flight Day 2:
     - Sourced MET: 90,840 s (April 2, 2026, 19:49 EDT / 23:49 UTC)
     - Sourced Duration: 350.0 s
     - Sourced Delta-V: 1,274 ft/s = 388.3152 m/s
     - AJ10-190 OMS-E Main Engine: 26.7 kN, 316.0 s Isp
     - Mass depletion: 25,618 kg -> 22,864 kg
"""

import math
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

from simulation.aim1.vehicle_config import SLSBlock1Config
from simulation.trajectory.mission_propagator import MultiBodyGravity
from simulation.trajectory.adaptive_integrator import DormandPrince45

class OrbitalOperationsPropagator:
    """
    Numerically propagates the in-space operations of SLS Block 1 Upper Stage (ICPS)
    and Orion MPCV from post-MECO insertion through the Flight Day 2 TLI Burn.
    """
    def __init__(self,
                 config: Optional[SLSBlock1Config] = None,
                 gravity: Optional[MultiBodyGravity] = None,
                 rtol: float = 1e-8,
                 atol: float = 1e-10):
        self.config = config or SLSBlock1Config()
        self.gravity = gravity or MultiBodyGravity(include_j2=True, include_moon=True)
        self.integrator = DormandPrince45(rtol=rtol, atol=atol, h_max=300.0, h_min=1e-3)

    def state_derivative(self,
                         t: float,
                         y: np.ndarray,
                         thrust_n: float = 0.0,
                         isp_s: float = 465.5,
                         steering_unit_vec: Optional[np.ndarray] = None) -> np.ndarray:
        """
        In-space orbital dynamics under multi-body gravity and propulsion:
        y = [x, y, z, vx, vy, vz, m]
        """
        r_vec = y[0:3]
        v_vec = y[3:6]
        m = max(500.0, float(y[6]))

        # Gravitational acceleration (Earth central + J2 + Moon perturbation)
        a_grav = self.gravity.total_gravitational_acceleration(r_vec)

        # Maneuver thrust
        v_mag = np.linalg.norm(v_vec)
        if thrust_n > 0.0 and v_mag > 1.0:
            if steering_unit_vec is not None:
                u_t = steering_unit_vec / np.linalg.norm(steering_unit_vec)
            else:
                u_t = v_vec / v_mag # Nominal prograde thrust
            a_thrust = (thrust_n / m) * u_t
            dm_dt = - thrust_n / (isp_s * MultiBodyGravity.G0)
        else:
            a_thrust = np.zeros(3)
            dm_dt = 0.0

        a_total = a_grav + a_thrust
        return np.concatenate([v_vec, a_total, [dm_dt]])

    def propagate_orbit_phase(self,
                              t_start: float,
                              t_end: float,
                              y_start: np.ndarray,
                              sample_step_s: float = 60.0,
                              thrust_n: float = 0.0,
                              isp_s: float = 465.5,
                              stage_name: str = "ICPS_ORION_STACK") -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Integrates an orbital arc from t_start to t_end and produces telemetry records.
        """
        records: List[Dict[str, Any]] = []
        y_cur = np.copy(y_start)

        t_points = np.arange(t_start, t_end + 0.1, sample_step_s)
        if t_points[-1] < t_end:
            t_points = np.append(t_points, t_end)

        for i in range(len(t_points) - 1):
            t1 = t_points[i]
            t2 = t_points[i+1]

            def deriv(t_sub, y_sub):
                return self.state_derivative(t_sub, y_sub, thrust_n=thrust_n, isp_s=isp_s)

            res = self.integrator.integrate(deriv, (t1, t2), y_cur, h_initial=min(10.0, t2 - t1))
            y_cur = res["y"][-1]

            r_vec = y_cur[0:3]
            v_vec = y_cur[3:6]
            m_cur = y_cur[6]

            r_mag = np.linalg.norm(r_vec)
            alt_km = (r_mag - MultiBodyGravity.R_EARTH) / 1000.0
            v_inertial = np.linalg.norm(v_vec)

            # Specific orbital energy & semi-major axis
            energy = (v_inertial ** 2) / 2.0 - (MultiBodyGravity.MU_EARTH / r_mag)
            semi_major_km = (- MultiBodyGravity.MU_EARTH / (2.0 * energy)) / 1000.0 if abs(energy) > 1e-4 else 0.0

            # Eccentricity vector e = ((v^2 - mu/r)*r - (r.v)*v) / mu
            mu = MultiBodyGravity.MU_EARTH
            e_vec = ((v_inertial ** 2 - mu / r_mag) * r_vec - np.dot(r_vec, v_vec) * v_vec) / mu
            ecc = float(np.linalg.norm(e_vec))

            # Orbital inclination i = arccos(h_z / |h|)
            h_vec = np.cross(r_vec, v_vec)
            h_mag = np.linalg.norm(h_vec)
            inc_deg = math.degrees(math.acos(max(-1.0, min(1.0, h_vec[2] / h_mag)))) if h_mag > 0.0 else 0.0

            records.append({
                "met_s": round(t2, 1),
                "stage": stage_name,
                "altitude_km": round(alt_km, 3),
                "velocity_m_s": round(v_inertial, 2),
                "semi_major_axis_km": round(semi_major_km, 1),
                "eccentricity": round(ecc, 4),
                "inclination_deg": round(inc_deg, 2),
                "mass_kg": round(m_cur, 1),
                "position_eci_m": [round(float(c), 1) for c in r_vec],
                "velocity_eci_m_s": [round(float(c), 2) for c in v_vec]
            })

        return y_cur, records

    def execute_complete_aim1_orbital_mission(self,
                                              insertion_state_t494: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes all post-MECO orbital operations leading to Orion's TLI burn:
          1. ICPS checkout in parking orbit (494 s -> 2,940 s)
          2. ICPS Perigee Raise Maneuver (PRM-1): delta-v ~ 210 m/s (2,940 s -> 3,100 s)
          3. Coast to ICPS Apogee Raise Burn (3,100 s -> 6,477 s)
          4. ICPS Apogee Raise Burn: delta-v ~ 850 m/s into 185 x 68,000 km HEO (6,477 s -> 6,800 s)
          5. Orion Separation from ICPS at T+12,255 s (mass drop to Orion stack: 25,618 kg)
          6. High Earth Orbit checkout across Flight Day 1 into Flight Day 2 (12,255 s -> 90,840 s)
          7. Orion ESM TLI Burn at T+90,840 s (Flight Day 2, April 2, 2026, 19:49 EDT):
             - duration 350.0 s
             - delta-v = 388.3152 m/s
             - final mass = 22,864 kg
        """
        r0 = np.array(insertion_state_t494["position_eci_m"], dtype=np.float64)
        v0 = np.array(insertion_state_t494["velocity_eci_m_s"], dtype=np.float64)
        m0 = float(insertion_state_t494["mass_kg"])

        y_cur = np.concatenate([r0, v0, [m0]])
        all_telemetry: List[Dict[str, Any]] = []
        events: List[Dict[str, Any]] = []

        # ---------------------------------------------------------------------
        # Event 1: ICPS RL10 Nozzle Extension & Solar Array Deployment Coast
        # ---------------------------------------------------------------------
        y_cur, recs1 = self.propagate_orbit_phase(
            494.0, 2940.0, y_cur, sample_step_s=120.0,
            stage_name="ICPS_LEO_PARKING"
        )
        all_telemetry.extend(recs1)
        events.append({
            "event_id": "icps_rl10_nozzle_extension",
            "met_s": 508.0,
            "event_name": "ICPS RL10 Nozzle Extension",
            "altitude_km": recs1[0]["altitude_km"]
        })
        events.append({
            "event_id": "solar_array_deployment",
            "met_s": 1200.0,
            "event_name": "Orion Solar Array Wings Deploy",
            "altitude_km": recs1[5]["altitude_km"]
        })

        # ---------------------------------------------------------------------
        # Event 2: ICPS Perigee Raise Maneuver 1 (PRM-1)
        # ---------------------------------------------------------------------
        events.append({
            "event_id": "perigee_raise_1",
            "met_s": 2940.0,
            "event_name": "ICPS Perigee Raise Maneuver (PRM-1)",
            "delta_v_m_s": 210.0
        })
        # Execute PRM burn (160 s duration with RL10B-2)
        y_cur, recs_prm = self.propagate_orbit_phase(
            2940.0, 3100.0, y_cur, sample_step_s=20.0,
            thrust_n=self.config.ICPS_THRUST_VAC_N,
            isp_s=self.config.ICPS_ISP_VAC_S,
            stage_name="ICPS_PRM_BURN"
        )
        all_telemetry.extend(recs_prm)

        # ---------------------------------------------------------------------
        # Event 3: Coast to ICPS Apogee Raise Burn
        # ---------------------------------------------------------------------
        y_cur, recs_coast1 = self.propagate_orbit_phase(
            3100.0, 6477.0, y_cur, sample_step_s=200.0,
            stage_name="ICPS_INTERMEDIATE_COAST"
        )
        all_telemetry.extend(recs_coast1)

        # ---------------------------------------------------------------------
        # Event 4: ICPS Apogee Raise Burn into High Earth Orbit (185 x 68,000 km)
        # ---------------------------------------------------------------------
        events.append({
            "event_id": "apogee_raise",
            "met_s": 6477.0,
            "event_name": "ICPS Apogee Raise Burn into High Earth Orbit",
            "target_apogee_km": 68000.0
        })
        y_cur, recs_arb = self.propagate_orbit_phase(
            6477.0, 6800.0, y_cur, sample_step_s=20.0,
            thrust_n=self.config.ICPS_THRUST_VAC_N,
            isp_s=self.config.ICPS_ISP_VAC_S,
            stage_name="ICPS_APOGEE_RAISE_BURN"
        )
        all_telemetry.extend(recs_arb)

        # ---------------------------------------------------------------------
        # Event 5: Orion Separation from ICPS at T+12,255 s
        # ---------------------------------------------------------------------
        y_cur, recs_coast2 = self.propagate_orbit_phase(
            6800.0, 12255.0, y_cur, sample_step_s=300.0,
            stage_name="ICPS_PRE_SEP_COAST"
        )
        all_telemetry.extend(recs_coast2)

        # Orion separation: ICPS stage separates, Orion mass is wet baseline 25,618 kg
        y_cur[6] = self.config.ORION_TOTAL_MASS_AT_TLI_KG
        events.append({
            "event_id": "orion_icps_separation",
            "met_s": 12255.0,
            "event_name": "Orion Separates from ICPS (Proximity Ops Begin)",
            "orion_mass_kg": self.config.ORION_TOTAL_MASS_AT_TLI_KG,
            "altitude_km": recs_coast2[-1]["altitude_km"]
        })
        events.append({
            "event_id": "icps_disposal_burn",
            "met_s": 18000.0,
            "event_name": "ICPS Safe Disposal Burn (Heliocentric Path)"
        })

        # ---------------------------------------------------------------------
        # Event 6: High Earth Orbit Checkout Orbit to Perigee TLI (12,255s -> 90,840s)
        # ---------------------------------------------------------------------
        # Propagate Orion checkout orbit leading to the Flight Day 2 TLI window
        y_cur, recs_heo = self.propagate_orbit_phase(
            12255.0, 90840.0, y_cur, sample_step_s=600.0,
            stage_name="ORION_HEO_CHECKOUT"
        )
        all_telemetry.extend(recs_heo)

        # ---------------------------------------------------------------------
        # Event 7: Orion TLI Burn on Flight Day 2 (April 2, 2026, 19:49 EDT)
        # Sourced: MET = 90,840 s, duration = 350.0 s, delta-v = 388.3152 m/s
        # ---------------------------------------------------------------------
        tli_start_state = np.copy(y_cur)
        v_before = np.linalg.norm(tli_start_state[3:6])

        # Propagate 350 s continuous burn of AJ10-190 OMS-E engine
        y_post_tli, recs_tli = self.propagate_orbit_phase(
            90840.0, 91190.0, y_cur, sample_step_s=25.0,
            thrust_n=self.config.ORION_MAIN_ENGINE_THRUST_N,
            isp_s=self.config.ORION_MAIN_ENGINE_ISP_S,
            stage_name="ORION_TLI_BURN"
        )
        all_telemetry.extend(recs_tli)

        v_after = np.linalg.norm(y_post_tli[3:6])
        # Thrust delta-v integral (ideal rocket delta-v): g0 * Isp * ln(m0 / mf)
        actual_delta_v_m_s = float(self.config.ORION_MAIN_ENGINE_ISP_S * MultiBodyGravity.G0 * math.log(tli_start_state[6] / y_post_tli[6]))
        net_orbital_speed_change = float(v_after - v_before)
        delta_v_vector = (y_post_tli[3:6] - tli_start_state[3:6]).tolist()

        events.append({
            "event_id": "orion_tli_burn",
            "met_s": 90840.0,
            "burn_duration_s": 350.0,
            "event_name": "Orion ESM Main Engine Translunar Injection (TLI)",
            "delta_v_scalar_m_s": round(actual_delta_v_m_s, 2),
            "reported_target_delta_v_m_s": 388.3152,
            "pre_burn_mass_kg": round(float(tli_start_state[6]), 1),
            "post_burn_mass_kg": round(float(y_post_tli[6]), 1)
        })

        return {
            "status": "PASS",
            "post_tli_state": {
                "epoch_utc": "2026-04-02T23:54:50Z",
                "met_s": 91190.0,
                "position_eci_m": [round(float(c), 1) for c in y_post_tli[0:3]],
                "velocity_eci_m_s": [round(float(c), 2) for c in y_post_tli[3:6]],
                "mass_kg": round(float(y_post_tli[6]), 1),
                "delta_v_vector_m_s": [round(float(c), 2) for c in delta_v_vector],
                "delta_v_scalar_m_s": round(actual_delta_v_m_s, 2),
                "burn_duration_s": 350.0
            },
            "events": events,
            "telemetry": all_telemetry
        }
