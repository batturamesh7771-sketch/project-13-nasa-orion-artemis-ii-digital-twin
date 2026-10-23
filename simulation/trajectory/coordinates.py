"""
NASA Artemis II Coordinate Transformation and Tracking Frame Pipeline.
Provides transformations between:
  1. ECI (Earth-Centered Inertial, J2000 / EarthMJ2000Eq)
  2. ECEF (Earth-Centered, Earth-Fixed, WGS-84)
  3. Geodetic Coordinates (WGS-84 Latitude, Longitude, Ellipsoidal Height)
  4. MCI (Moon-Centered Inertial, MoonMJ2000Eq)
  5. Topocentric Horizon SEZ (South-East-Zenith, Azimuth, Elevation, Range)
"""

import math
from typing import Tuple, Dict, Any, Optional
import numpy as np


class CoordinateFrames:
    # WGS-84 Ellipsoid Physical Parameters
    WGS84_A = 6378137.0                      # Semi-major axis (equatorial radius) [m]
    WGS84_F = 1.0 / 298.257223563            # Flattening [-]
    WGS84_B = WGS84_A * (1.0 - WGS84_F)      # Semi-minor axis (polar radius) [m]
    WGS84_E2 = 2.0 * WGS84_F - WGS84_F ** 2  # First eccentricity squared [-]
    WGS84_EP2 = WGS84_E2 / (1.0 - WGS84_E2)  # Second eccentricity squared [-]

    # Earth Sidereal Rotation Parameters
    OMEGA_EARTH = 7.2921150e-5               # Earth nominal angular velocity [rad/s]
    SIDEREAL_DAY_SEC = 86164.0905            # One sidereal day [s]

    # Moon Mean Physical Parameters
    R_MOON = 1737400.0                       # Moon mean radius [m]

    @staticmethod
    def greenwich_mean_sidereal_time(t_sec: float, theta0_rad: float = 0.0) -> float:
        """
        Calculates Earth rotation angle theta_GMST at mission elapsed time t_sec.
        theta(t) = (theta0 + omega_E * t) mod 2*pi [rad].
        """
        return (theta0_rad + CoordinateFrames.OMEGA_EARTH * t_sec) % (2.0 * math.pi)

    @classmethod
    def eci_to_ecef(cls,
                    r_eci: np.ndarray,
                    v_eci: Optional[np.ndarray] = None,
                    t_sec: float = 0.0,
                    theta0_rad: float = 0.0) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Transform position (and optional velocity) from ECI (J2000) to ECEF (WGS84).
        Accounts for Earth sidereal rotation and transport velocity Coriolis term:
          r_ecef = Rz(theta) * r_eci
          v_ecef = Rz(theta) * v_eci - omega_E x r_ecef
        """
        theta = cls.greenwich_mean_sidereal_time(t_sec, theta0_rad)
        cos_t, sin_t = math.cos(theta), math.sin(theta)

        Rz = np.array([
            [cos_t,  sin_t, 0.0],
            [-sin_t, cos_t, 0.0],
            [0.0,    0.0,   1.0]
        ], dtype=np.float64)

        r_ecef = Rz @ r_eci

        if v_eci is not None:
            omega_vec = np.array([0.0, 0.0, cls.OMEGA_EARTH], dtype=np.float64)
            v_transport = np.cross(omega_vec, r_ecef)
            v_ecef = (Rz @ v_eci) - v_transport
            return r_ecef, v_ecef

        return r_ecef, None

    @classmethod
    def ecef_to_eci(cls,
                    r_ecef: np.ndarray,
                    v_ecef: Optional[np.ndarray] = None,
                    t_sec: float = 0.0,
                    theta0_rad: float = 0.0) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Inverse transformation from ECEF (WGS84) to ECI (J2000).
          r_eci = Rz(-theta) * r_ecef
          v_eci = Rz(-theta) * (v_ecef + omega_E x r_ecef)
        """
        theta = cls.greenwich_mean_sidereal_time(t_sec, theta0_rad)
        cos_t, sin_t = math.cos(theta), math.sin(theta)

        # Rz(-theta) = Rz(theta)^T
        Rz_inv = np.array([
            [cos_t, -sin_t, 0.0],
            [sin_t,  cos_t, 0.0],
            [0.0,    0.0,   1.0]
        ], dtype=np.float64)

        r_eci = Rz_inv @ r_ecef

        if v_ecef is not None:
            omega_vec = np.array([0.0, 0.0, cls.OMEGA_EARTH], dtype=np.float64)
            v_transport = np.cross(omega_vec, r_ecef)
            v_eci = Rz_inv @ (v_ecef + v_transport)
            return r_eci, v_eci

        return r_eci, None

    @classmethod
    def ecef_to_geodetic(cls, r_ecef: np.ndarray) -> Tuple[float, float, float]:
        """
        Convert Cartesian ECEF position [X, Y, Z] to WGS-84 Geodetic Coordinates:
        Returns: (latitude_deg, longitude_deg, altitude_meters).
        Uses Bowring's closed-form vector algorithm (sub-millimeter precision).
        """
        x, y, z = float(r_ecef[0]), float(r_ecef[1]), float(r_ecef[2])
        p = math.hypot(x, y)

        if p < 1e-6:
            # Polar singularity
            lat_deg = 90.0 if z > 0.0 else -90.0
            lon_deg = 0.0
            alt_m = abs(z) - cls.WGS84_B
            return lat_deg, lon_deg, alt_m

        # Geodetic longitude
        lon_rad = math.atan2(y, x)
        lon_deg = math.degrees(lon_rad)

        # Bowring's auxiliary angle theta
        theta = math.atan2(z * cls.WGS84_A, p * cls.WGS84_B)

        # Bowring's formula for geodetic latitude
        numerator = z + cls.WGS84_EP2 * cls.WGS84_B * (math.sin(theta) ** 3)
        denominator = p - cls.WGS84_E2 * cls.WGS84_A * (math.cos(theta) ** 3)
        lat_rad = math.atan2(numerator, denominator)
        lat_deg = math.degrees(lat_rad)

        # Radius of curvature in the prime vertical N(phi)
        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        N = cls.WGS84_A / math.sqrt(1.0 - cls.WGS84_E2 * (sin_lat ** 2))

        # Height above ellipsoid
        alt_m = (p / cos_lat) - N if abs(cos_lat) > 1e-4 else (z / sin_lat) - N * (1.0 - cls.WGS84_E2)

        return lat_deg, lon_deg, alt_m

    @classmethod
    def geodetic_to_ecef(cls, lat_deg: float, lon_deg: float, alt_m: float = 0.0) -> np.ndarray:
        """
        Convert WGS-84 Geodetic Coordinates (lat, lon, alt) to Cartesian ECEF [X, Y, Z] in meters.
        """
        lat_rad = math.radians(lat_deg)
        lon_rad = math.radians(lon_deg)

        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        sin_lon = math.sin(lon_rad)
        cos_lon = math.cos(lon_rad)

        N = cls.WGS84_A / math.sqrt(1.0 - cls.WGS84_E2 * (sin_lat ** 2))

        x = (N + alt_m) * cos_lat * cos_lon
        y = (N + alt_m) * cos_lat * sin_lon
        z = (N * (1.0 - cls.WGS84_E2) + alt_m) * sin_lat

        return np.array([x, y, z], dtype=np.float64)

    @classmethod
    def eci_to_mci(cls,
                   r_sc_eci: np.ndarray,
                   v_sc_eci: np.ndarray,
                   r_moon_eci: np.ndarray,
                   v_moon_eci: np.ndarray) -> Dict[str, Any]:
        """
        Transform spacecraft state into Moon-Centered Inertial (MCI / MoonMJ2000Eq).
        Computes selenocentric Cartesian states, distance, selenocentric speed,
        and perilune altitude.
        """
        r_mci = r_sc_eci - r_moon_eci
        v_mci = v_sc_eci - v_moon_eci

        dist_m = float(np.linalg.norm(r_mci))
        speed_m_s = float(np.linalg.norm(v_mci))
        alt_moon_km = (dist_m - cls.R_MOON) / 1000.0

        # Lunar latitude and longitude (inertial)
        x_m, y_m, z_m = r_mci[0], r_mci[1], r_mci[2]
        lunar_lat_deg = math.degrees(math.atan2(z_m, math.hypot(x_m, y_m)))
        lunar_lon_deg = math.degrees(math.atan2(y_m, x_m))

        return {
            "position_mci_m": r_mci,
            "velocity_mci_m_s": v_mci,
            "lunar_distance_km": dist_m / 1000.0,
            "lunar_altitude_km": alt_moon_km,
            "selenocentric_speed_km_s": speed_m_s / 1000.0,
            "lunar_inertial_lat_deg": lunar_lat_deg,
            "lunar_inertial_lon_deg": lunar_lon_deg
        }

    @classmethod
    def ecef_to_topocentric_sez(cls,
                                r_sc_ecef: np.ndarray,
                                station_lat_deg: float,
                                station_lon_deg: float,
                                station_alt_m: float = 0.0) -> Dict[str, float]:
        """
        Transform ECEF position to Topocentric Horizon Frame (South, East, Zenith - SEZ)
        relative to a tracking ground station. Computes Look Angles:
        Returns: {range_km, azimuth_deg, elevation_deg, is_visible}
        """
        # Ground station position in ECEF
        r_station_ecef = cls.geodetic_to_ecef(station_lat_deg, station_lon_deg, station_alt_m)

        # Range vector relative to station
        rho_ecef = r_sc_ecef - r_station_ecef
        rho_mag = float(np.linalg.norm(rho_ecef))

        phi = math.radians(station_lat_deg)
        lam = math.radians(station_lon_deg)

        sin_phi, cos_phi = math.sin(phi), math.cos(phi)
        sin_lam, cos_lam = math.sin(lam), math.cos(lam)

        # ECEF to SEZ rotation matrix
        R_sez = np.array([
            [sin_phi * cos_lam,  sin_phi * sin_lam, -cos_phi],
            [-sin_lam,           cos_lam,           0.0     ],
            [cos_phi * cos_lam,  cos_phi * sin_lam,  sin_phi]
        ], dtype=np.float64)

        rho_sez = R_sez @ rho_ecef
        s, e, z = float(rho_sez[0]), float(rho_sez[1]), float(rho_sez[2])

        # Elevation angle: arcsin(Z / rho)
        el_rad = math.asin(max(-1.0, min(1.0, z / rho_mag)))
        el_deg = math.degrees(el_rad)

        # Azimuth angle: measured clockwise from North (+S is South, +E is East)
        # In SEZ, North is -S, East is +E: az = atan2(E, -S)
        az_rad = math.atan2(e, -s)
        az_deg = (math.degrees(az_rad) + 360.0) % 360.0

        return {
            "range_km": rho_mag / 1000.0,
            "azimuth_deg": az_deg,
            "elevation_deg": el_deg,
            "is_visible": el_deg >= 0.0 # Line of sight above local horizon
        }
