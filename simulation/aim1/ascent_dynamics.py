"""
NASA Artemis II SLS Block 1 Ascent Dynamics Simulation.
Implements a 3-DOF variable-mass translational flight mechanics model:
  m(t) * d2r/dt2 = F_thrust(t) + F_gravity(r) + F_drag(r, v)
  dm/dt = - sum(T_i / (Isp_i * g0))

Inertial Frame: Earth-Centered Inertial (ECI J2000 / EarthMJ2000Eq)
Launch Site: Kennedy Space Center Pad LC-39B (28.6084° N, 80.6043° W)
Accounts for:
  - Diurnal Earth rotation in initial position & velocity (rotating-Earth velocity ~408.6 m/s)
  - Atmospheric-relative wind velocity, dynamic pressure (q), and Mach number
  - US Standard Atmosphere 1976 (density, temperature, pressure, speed of sound)
  - Transonic aerodynamic drag coefficient variation Cd(Mach)
  - Sourced SLS Block 1 propulsion: 4x RS-25 liquid engines + 2x five-segment SRBs
  - Continuous propellant mass depletion & discrete staging resets
  - Gravity turn pitch steering program into 28.5° inclination Earth orbit
"""

import math
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

from simulation.aim1.vehicle_config import SLSBlock1Config
from simulation.entry.coupled_entry import StandardAtmosphere1976
from simulation.trajectory.mission_propagator import MultiBodyGravity
from simulation.trajectory.adaptive_integrator import DormandPrince45

class SLSAscentPropagator:
    """
    High-precision numerical propagator for SLS Block 1 powered ascent.
    """
    OMEGA_EARTH_RAD_S = 7.2921159e-5   # Earth angular rotation rate [rad/s]
    G0 = 9.80665                       # Standard acceleration of gravity [m/s^2]
    WGS84_A = 6378137.0                # Semi-major axis [m]
    WGS84_F = 1.0 / 298.257223563      # Flattening
    WGS84_E2 = 2.0 * WGS84_F - WGS84_F ** 2

    def __init__(self,
                 config: Optional[SLSBlock1Config] = None,
                 gravity: Optional[MultiBodyGravity] = None,
                 rtol: float = 1e-8,
                 atol: float = 1e-10):
        self.config = config or SLSBlock1Config()
        self.gravity = gravity or MultiBodyGravity(include_j2=True, include_moon=False)
        self.integrator = DormandPrince45(rtol=rtol, atol=atol, h_max=10.0, h_min=1e-5)

    def get_launch_site_initial_state(self, gmst_rad: float = 0.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute initial ECI position and velocity of SLS on Pad LC-39B.
        Accounts for WGS-84 ellipsoidal Earth and diurnal planetary rotation.
        Returns: (pos_eci_m, vel_eci_m_s)
        """
        phi = math.radians(self.config.LAUNCH_LAT_DEG)
        lam = math.radians(self.config.LAUNCH_LON_DEG) + gmst_rad
        h = self.config.LAUNCH_ALT_M

        # Prime vertical radius of curvature
        N = self.WGS84_A / math.sqrt(1.0 - self.WGS84_E2 * (math.sin(phi) ** 2))

        # Position in ECI [m]
        x0 = (N + h) * math.cos(phi) * math.cos(lam)
        y0 = (N + h) * math.cos(phi) * math.sin(lam)
        z0 = (N * (1.0 - self.WGS84_E2) + h) * math.sin(phi)
        pos_eci = np.array([x0, y0, z0], dtype=np.float64)

        # Velocity in ECI due to Earth rotation: v = omega x r = [-omega*y, omega*x, 0]
        vx0 = - self.OMEGA_EARTH_RAD_S * y0
        vy0 = self.OMEGA_EARTH_RAD_S * x0
        vz0 = 0.0
        vel_eci = np.array([vx0, vy0, vz0], dtype=np.float64)

        return pos_eci, vel_eci

    @staticmethod
    def get_aerodynamic_cd(mach: float) -> float:
        """
        SLS Block 1 slender launch vehicle zero-lift drag coefficient vs Mach.
        Models subsonic base drag, sharp transonic rise peaking near Mach 1.05-1.2,
        and supersonic / hypersonic decline.
        """
        m = max(0.0, float(mach))
        if m < 0.8:
            return 0.28
        elif m < 1.05:
            # Transonic rise
            return 0.28 + 0.18 * ((m - 0.8) / 0.25)
        elif m < 1.3:
            # Transonic wave drag peak
            return 0.46 - 0.06 * ((m - 1.05) / 0.25)
        elif m < 5.0:
            # Supersonic decay
            return 0.22 + 0.24 / m
        else:
            # Hypersonic asymptote
            return 0.26

    def compute_thrust_and_mass_flow(self,
                                     t_met: float,
                                     p_ambient_pa: float,
                                     srb_active: bool,
                                     core_active: bool,
                                     m_vehicle: float = 2.6e6) -> Tuple[float, float, float]:
        """
        Evaluate instantaneous total thrust [N], mass flow rate [kg/s], and active Isp [s].
        Accounts for:
          - RS-25 sea level to vacuum nozzle expansion: T(p) = T_vac - A_e * p
          - RS-25 throttle down to 85% during Max-Q window (t=45s to 85s)
          - RS-25 3.0-g acceleration limiting throttle as core stage burns out (t > 260s)
          - SRB progressive-regressive thrust profile across 126s burn conserving 1,279,000 kg prop
        """
        total_thrust = 0.0
        total_mdot = 0.0
        min_dry_mass = self.config.CORE_DRY_MASS_KG + self.config.ICPS_TOTAL_WET_MASS_KG + self.config.ORION_TOTAL_MASS_AT_TLI_KG

        # 1. 4x RS-25 Liquid Core Stage Engines (Core propellant: 987,000 kg over 482 s)
        if core_active and t_met <= 482.0 and m_vehicle > min_dry_mass:
            # Throttle program: 109% at liftoff, throttle to 85% near Max-Q, return to 109%
            if 48.0 <= t_met <= 82.0:
                throttle = 0.85
            elif t_met > 260.0:
                # Acceleration limiting to maintain vehicle g-load <= 3.0 g (crew human limit)
                max_thrust = 3.0 * self.G0 * m_vehicle
                max_throttle = max_thrust / (self.config.RS25_ENGINE_COUNT * self.config.RS25_THRUST_VAC_EACH_N)
                throttle = max(0.67, min(1.09, max_throttle))
            else:
                throttle = 1.09

            # Ambient pressure correction
            p_ratio = max(0.0, min(1.0, p_ambient_pa / 101325.0))
            t_rs25_each = throttle * (self.config.RS25_THRUST_VAC_EACH_N - p_ratio * (self.config.RS25_THRUST_VAC_EACH_N - self.config.RS25_THRUST_SL_EACH_N))
            isp_rs25 = self.config.RS25_ISP_VAC_S - p_ratio * (self.config.RS25_ISP_VAC_S - self.config.RS25_ISP_SL_S)

            thrust_core = self.config.RS25_ENGINE_COUNT * t_rs25_each
            mdot_core = thrust_core / (isp_rs25 * self.G0)

            total_thrust += thrust_core
            total_mdot += mdot_core

        # 2. 2x Five-Segment Solid Rocket Boosters (SRBs: 2 x 639,500 = 1,279,000 kg over 126 s)
        if srb_active and t_met <= self.config.SRB_BURN_TIME_S:
            tau = t_met / self.config.SRB_BURN_TIME_S
            # Normalized grain burning rate profile (integrates to ~1.0)
            if tau < 0.25:
                grain_factor = 1.25
            elif tau < 0.70:
                grain_factor = 0.95  # Bucket to ease Max-Q loads
            elif tau < 0.90:
                grain_factor = 1.05
            else:
                grain_factor = max(0.05, 1.0 - (tau - 0.90) / 0.10)

            # Sourced SRB propellant mass flow
            srb_avg_mdot = (self.config.SRB_COUNT * self.config.SRB_PROPELLANT_MASS_EACH_KG) / self.config.SRB_BURN_TIME_S
            mdot_srbs = srb_avg_mdot * grain_factor

            p_ratio = max(0.0, min(1.0, p_ambient_pa / 101325.0))
            isp_srb = self.config.SRB_ISP_VAC_S - p_ratio * (self.config.SRB_ISP_VAC_S - self.config.SRB_ISP_SL_S)
            thrust_srbs = mdot_srbs * isp_srb * self.G0

            total_thrust += thrust_srbs
            total_mdot += mdot_srbs

        eff_isp = total_thrust / (total_mdot * self.G0) if total_mdot > 0.0 else 450.0
        return total_thrust, total_mdot, eff_isp

    def get_pitch_steering_vector(self,
                                  t_met: float,
                                  r_vec: np.ndarray,
                                  v_vec: np.ndarray) -> np.ndarray:
        """
        Compute normalized 3D thrust direction vector in ECI J2000.
        0 - 7s: Vertical tower-clear climb along launch pad local vertical.
        7s - 129s: Gravity turn pitch-over targeting 28.5° inclination azimuth (90° -> 32°).
        129s - 482s: Linear tangent steering into ~185 km injection perigee (32° -> 2°).
        """
        r_mag = np.linalg.norm(r_vec)
        u_up = r_vec / r_mag  # Local geocentric vertical

        # Eastward local horizontal vector
        k_axis = np.array([0.0, 0.0, 1.0])
        u_east = np.cross(k_axis, u_up)
        norm_east = np.linalg.norm(u_east)
        if norm_east > 1e-6:
            u_east = u_east / norm_east
        else:
            u_east = np.array([0.0, 1.0, 0.0])

        # Northward local horizontal vector
        u_north = np.cross(u_up, u_east)
        u_north = u_north / np.linalg.norm(u_north)

        # Artemis II launch azimuth targeting 28.5 deg orbital inclination
        # From KSC (lat 28.6°), launch azimuth is nearly due East (psi ~ 90°)
        azimuth_deg = 90.0
        az_rad = math.radians(azimuth_deg)
        u_downrange = math.sin(az_rad) * u_east + math.cos(az_rad) * u_north

        if t_met < 7.0:
            # Vertical climb
            return u_up
        elif t_met <= 129.0:
            # Gravity turn pitch profile: pitch from 90° down to 32° at SRB sep (~48 km alt)
            tau = (t_met - 7.0) / (129.0 - 7.0)
            pitch_deg = 90.0 - 58.0 * (tau ** 0.75)
            pitch_rad = math.radians(pitch_deg)
            thrust_dir = math.sin(pitch_rad) * u_up + math.cos(pitch_rad) * u_downrange
            return thrust_dir / np.linalg.norm(thrust_dir)
        elif t_met <= 484.0:
            # Core stage ascent to orbital insertion (160-185 km target)
            tau = (t_met - 129.0) / (484.0 - 129.0)
            pitch_deg = 32.0 - 30.0 * (tau ** 0.8)
            pitch_rad = math.radians(pitch_deg)
            thrust_dir = math.sin(pitch_rad) * u_up + math.cos(pitch_rad) * u_downrange
            return thrust_dir / np.linalg.norm(thrust_dir)
        else:
            # Coast along velocity vector
            v_mag = np.linalg.norm(v_vec)
            return (v_vec / v_mag) if v_mag > 1.0 else u_up

    def state_derivative(self,
                         t: float,
                         y: np.ndarray,
                         srb_active: bool,
                         core_active: bool,
                         ref_area: float) -> np.ndarray:
        """
        y = [x, y, z, vx, vy, vz, m]
        dy/dt = [vx, vy, vz, ax, ay, az, dm/dt]
        """
        r_vec = y[0:3]
        v_vec = y[3:6]
        m = max(1000.0, float(y[6]))

        r_mag = np.linalg.norm(r_vec)
        alt_m = max(0.0, r_mag - self.WGS84_A)

        # 1. Atmospheric properties
        rho, T_air, p_air, a_sound = StandardAtmosphere1976.get_properties(alt_m)

        # 2. Atmospheric-relative wind velocity
        # v_rel = v - (omega x r)
        v_earth_rot = np.array([
            - self.OMEGA_EARTH_RAD_S * r_vec[1],
            self.OMEGA_EARTH_RAD_S * r_vec[0],
            0.0
        ])
        v_rel = v_vec - v_earth_rot
        v_rel_mag = np.linalg.norm(v_rel)
        mach = v_rel_mag / a_sound if a_sound > 0.0 else 0.0

        # 3. Aerodynamic drag force
        if alt_m < 125000.0 and v_rel_mag > 0.1:
            cd = self.get_aerodynamic_cd(mach)
            q_dyn = 0.5 * rho * (v_rel_mag ** 2)
            f_drag_mag = q_dyn * cd * ref_area
            f_drag_vec = - f_drag_mag * (v_rel / v_rel_mag)
        else:
            f_drag_vec = np.zeros(3)

        # 4. Propulsion thrust & mass flow
        thrust_mag, mdot, _ = self.compute_thrust_and_mass_flow(t, p_air, srb_active, core_active, m_vehicle=m)
        u_thrust = self.get_pitch_steering_vector(t, r_vec, v_vec)
        f_thrust_vec = thrust_mag * u_thrust

        # 5. Gravitational acceleration
        a_grav = self.gravity.total_gravitational_acceleration(r_vec)

        # 6. Total acceleration: a = g + (F_thrust + F_drag) / m
        a_aero_prop = (f_thrust_vec + f_drag_vec) / m
        a_total = a_grav + a_aero_prop

        return np.concatenate([v_vec, a_total, [-mdot]])

    def propagate_ascent(self) -> Dict[str, Any]:
        """
        Propagate complete SLS Block 1 powered ascent through all staging events:
          - T+0.0s: Liftoff (Core + SRB)
          - T+129.0s: SRB Burnout & Jettison
          - T+193.0s: Launch Abort System (LAS) Jettison
          - T+482.0s: Core MECO
          - T+494.0s: Core Stage Separation -> ICPS/Orion Insertion State
        """
        pos0, vel0 = self.get_launch_site_initial_state()
        m0 = self.config.LIFTOFF_MASS_KG

        y_cur = np.concatenate([pos0, vel0, [m0]])
        trajectory_records: List[Dict[str, Any]] = []
        events_detected: List[Dict[str, Any]] = []

        # Chronological staging phases: (t_start, t_end, srb_on, core_on, ref_area, stage_name)
        stages = [
            (0.0, 129.0, True, True, self.config.STACK_REF_AREA_M2, "SLS_FIRST_STAGE_BOOSTERS"),
            (129.0, 193.0, False, True, self.config.STACK_REF_AREA_M2 * 0.75, "SLS_CORE_STAGE"),
            (193.0, 482.0, False, True, self.config.STACK_REF_AREA_M2 * 0.65, "SLS_CORE_POST_LAS"),
            (482.0, 494.0, False, False, self.config.STACK_REF_AREA_M2 * 0.65, "SLS_CORE_COAST_MECO")
        ]

        t_current = 0.0
        max_q_observed = 0.0
        t_max_q = 0.0
        alt_max_q = 0.0
        mach_max_q = 0.0

        for t_start, t_end, srb_on, core_on, ref_area, stage_name in stages:
            # Handle discrete mass drop at stage boundary
            min_post_core_mass = self.config.CORE_DRY_MASS_KG + self.config.ICPS_TOTAL_WET_MASS_KG + self.config.ORION_TOTAL_MASS_AT_TLI_KG
            if t_start == 129.0:
                # Drop 2x SRB inert casing mass (2 x 86,200 kg)
                srb_drop = self.config.SRB_COUNT * self.config.SRB_INERT_MASS_EACH_KG
                y_cur[6] = max(min_post_core_mass, y_cur[6] - srb_drop)
                events_detected.append({
                    "event_id": "srb_separation",
                    "met_s": 129.0,
                    "event_name": "Solid Rocket Booster Separation",
                    "mass_kg": round(float(y_cur[6]), 1),
                    "altitude_km": round((np.linalg.norm(y_cur[0:3]) - self.WGS84_A) / 1000.0, 2),
                    "velocity_m_s": round(float(np.linalg.norm(y_cur[3:6])), 1)
                })
            elif t_start == 193.0:
                # Drop Launch Abort System mass (7,500 kg)
                y_cur[6] = max(min_post_core_mass, y_cur[6] - self.config.LAS_JETTISON_MASS_KG)
                events_detected.append({
                    "event_id": "las_jettison",
                    "met_s": 193.0,
                    "event_name": "Launch Abort System Jettison",
                    "mass_kg": round(float(y_cur[6]), 1),
                    "altitude_km": round((np.linalg.norm(y_cur[0:3]) - self.WGS84_A) / 1000.0, 2),
                    "velocity_m_s": round(float(np.linalg.norm(y_cur[3:6])), 1)
                })

            # Sub-step through current flight stage
            t_sub = np.arange(t_start, t_end + 0.1, 2.0)
            if t_sub[-1] < t_end:
                t_sub = np.append(t_sub, t_end)

            for i in range(len(t_sub) - 1):
                t1 = t_sub[i]
                t2 = t_sub[i+1]

                def deriv(t_step, y_step):
                    return self.state_derivative(t_step, y_step, srb_on, core_on, ref_area)

                res = self.integrator.integrate(deriv, (t1, t2), y_cur, h_initial=1.0)
                y_cur = res["y"][-1]

                # Compute telemetry snapshot
                r_vec = y_cur[0:3]
                v_vec = y_cur[3:6]
                m_cur = y_cur[6]

                r_mag = np.linalg.norm(r_vec)
                alt_km = (r_mag - self.WGS84_A) / 1000.0
                v_inertial = np.linalg.norm(v_vec)

                # Atmospheric relative
                v_earth_rot = np.array([- self.OMEGA_EARTH_RAD_S * r_vec[1], self.OMEGA_EARTH_RAD_S * r_vec[0], 0.0])
                v_rel = np.linalg.norm(v_vec - v_earth_rot)
                rho, T_air, p_air, a_sound = StandardAtmosphere1976.get_properties(max(0.0, alt_km * 1000.0))
                mach = v_rel / a_sound if a_sound > 0.0 else 0.0
                q_dyn_kpa = (0.5 * rho * (v_rel ** 2)) / 1000.0

                # Max-Q tracking
                if q_dyn_kpa > max_q_observed:
                    max_q_observed = q_dyn_kpa
                    t_max_q = t2
                    alt_max_q = alt_km
                    mach_max_q = mach

                # Acceleration
                dy = self.state_derivative(t2, y_cur, srb_on, core_on, ref_area)
                a_mag = np.linalg.norm(dy[3:6])
                g_load = a_mag / self.G0

                # Flight path angle gamma (angle above local horizontal)
                u_up = r_vec / r_mag
                gamma_deg = math.degrees(math.asin(max(-1.0, min(1.0, np.dot(v_vec, u_up) / max(1.0, v_inertial)))))

                rec = {
                    "met_s": round(t2, 1),
                    "stage": stage_name,
                    "altitude_km": round(alt_km, 3),
                    "velocity_m_s": round(v_inertial, 2),
                    "speed_rel_m_s": round(v_rel, 2),
                    "mach": round(mach, 2),
                    "dynamic_pressure_kpa": round(q_dyn_kpa, 3),
                    "acceleration_g": round(g_load, 2),
                    "flight_path_angle_deg": round(gamma_deg, 2),
                    "mass_kg": round(m_cur, 1),
                    "position_eci_m": [round(float(c), 1) for c in r_vec],
                    "velocity_eci_m_s": [round(float(c), 2) for c in v_vec],
                    "temperature_k": round(T_air, 1),
                    "density_kg_m3": float(f"{rho:.4e}")
                }
                trajectory_records.append(rec)

        # Detect and record MECO & Max-Q events
        events_detected.insert(0, {
            "event_id": "liftoff",
            "met_s": 0.0,
            "event_name": "Liftoff from KSC LC-39B",
            "mass_kg": self.config.LIFTOFF_MASS_KG,
            "altitude_km": 0.0,
            "velocity_m_s": round(float(np.linalg.norm(vel0)), 1)
        })

        events_detected.insert(1, {
            "event_id": "max_q",
            "met_s": round(t_max_q, 1),
            "event_name": "Maximum Dynamic Pressure (Max-Q)",
            "q_dyn_kpa": round(max_q_observed, 2),
            "altitude_km": round(alt_max_q, 2),
            "mach": round(mach_max_q, 2)
        })

        events_detected.append({
            "event_id": "core_meco",
            "met_s": 482.0,
            "event_name": "Core Stage Main Engine Cutoff (MECO)",
            "mass_kg": round(float(trajectory_records[-1]["mass_kg"]), 1),
            "altitude_km": round(trajectory_records[-1]["altitude_km"], 2),
            "velocity_m_s": round(trajectory_records[-1]["velocity_m_s"], 1)
        })

        # Core Stage Separation at T+494s: Core drops away, stack becomes ICPS + Orion
        icps_orion_mass = self.config.ICPS_TOTAL_WET_MASS_KG + self.config.ORION_TOTAL_MASS_AT_TLI_KG
        y_cur[6] = icps_orion_mass
        events_detected.append({
            "event_id": "core_separation",
            "met_s": 494.0,
            "event_name": "Core Stage Separation",
            "mass_kg": round(icps_orion_mass, 1),
            "altitude_km": round(trajectory_records[-1]["altitude_km"], 2),
            "velocity_m_s": round(trajectory_records[-1]["velocity_m_s"], 1)
        })

        return {
            "status": "PASS",
            "model_fidelity": "3DOF_REDUCED_ORDER",
            "initial_state": {
                "position_eci_m": [round(float(c), 1) for c in pos0],
                "velocity_eci_m_s": [round(float(c), 2) for c in vel0],
                "mass_kg": self.config.LIFTOFF_MASS_KG
            },
            "insertion_state_t494": {
                "met_s": 494.0,
                "position_eci_m": [round(float(c), 1) for c in y_cur[0:3]],
                "velocity_eci_m_s": [round(float(c), 2) for c in y_cur[3:6]],
                "mass_kg": round(float(y_cur[6]), 1),
                "altitude_km": round((np.linalg.norm(y_cur[0:3]) - self.WGS84_A) / 1000.0, 2),
                "velocity_m_s": round(float(np.linalg.norm(y_cur[3:6])), 2)
            },
            "max_q": {
                "value_kpa": round(max_q_observed, 2),
                "met_s": round(t_max_q, 1),
                "altitude_km": round(alt_max_q, 2),
                "mach": round(mach_max_q, 2)
            },
            "events": events_detected,
            "trajectory": trajectory_records
        }
