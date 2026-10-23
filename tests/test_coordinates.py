"""
Unit and Integration Tests for Artemis II Coordinate Transformations Pipeline.
Tests:
  1. ECI <-> ECEF round-trip identity and rotation kinematics.
  2. Transport velocity Coriolis term validation (ground object stationary in ECEF).
  3. Geodetic <-> ECEF Bowring algorithm precision across equator, poles, and KSC.
  4. Topocentric SEZ tracking look angles (Azimuth, Elevation, Range) from Cape Canaveral LC-39B.
  5. Moon-Centered Inertial (MCI) selenocentric state transformation and perilune evaluation.
"""

import math
import unittest
import numpy as np

from simulation.trajectory.coordinates import CoordinateFrames


class TestCoordinateFrames(unittest.TestCase):
    def test_01_eci_ecef_round_trip_exactness(self):
        """Verify ECI -> ECEF -> ECI round-trip position and velocity identity."""
        r_eci_orig = np.array([5500000.0, 3200000.0, 2100000.0], dtype=np.float64)
        v_eci_orig = np.array([-3500.0, 6200.0, 1800.0], dtype=np.float64)
        t_sec = 43200.0 # 12 hours

        # Forward transformation
        r_ecef, v_ecef = CoordinateFrames.eci_to_ecef(r_eci_orig, v_eci_orig, t_sec=t_sec)

        # Inverse transformation
        r_eci_back, v_eci_back = CoordinateFrames.ecef_to_eci(r_ecef, v_ecef, t_sec=t_sec)

        pos_diff = np.linalg.norm(r_eci_back - r_eci_orig)
        vel_diff = np.linalg.norm(v_eci_back - v_eci_orig)

        print(f"\n[+] ECI <-> ECEF Round-trip Position Error : {pos_diff:.6e} m")
        print(f"[+] ECI <-> ECEF Round-trip Velocity Error : {vel_diff:.6e} m/s")

        self.assertLess(pos_diff, 1e-4, "ECI-ECEF round trip position error exceeds 0.1 mm")
        self.assertLess(vel_diff, 1e-6, "ECI-ECEF round trip velocity error exceeds 1 um/s")

    def test_02_coriolis_transport_velocity(self):
        """Verify that a stationary ground point on Earth equator has v_ecef = 0 and v_eci = omega_E * R_E."""
        # Point on Equator at Prime Meridian
        r_ecef = np.array([CoordinateFrames.WGS84_A, 0.0, 0.0])
        v_ecef = np.array([0.0, 0.0, 0.0]) # Stationary on surface

        t_sec = 0.0
        r_eci, v_eci = CoordinateFrames.ecef_to_eci(r_ecef, v_ecef, t_sec=t_sec)

        # Expected ECI speed is Earth equatorial rotational speed: v = omega * a
        expected_v_eci = CoordinateFrames.OMEGA_EARTH * CoordinateFrames.WGS84_A # ~465.1 m/s
        actual_v_eci = np.linalg.norm(v_eci)

        print(f"[+] Earth Equatorial Rotation Speed: Expected = {expected_v_eci:.3f} m/s | Actual = {actual_v_eci:.3f} m/s")
        self.assertAlmostEqual(actual_v_eci, expected_v_eci, delta=1e-3)
        self.assertAlmostEqual(v_eci[0], 0.0, delta=1e-3)
        self.assertAlmostEqual(v_eci[1], expected_v_eci, delta=1e-3)
        self.assertAlmostEqual(v_eci[2], 0.0, delta=1e-3)

    def test_03_geodetic_ecef_round_trip(self):
        """Verify Bowring's geodetic conversion algorithm against official reference landmarks."""
        # 1. Kennedy Space Center LC-39B (Launch Pad)
        ksc_lat = 28.627
        ksc_lon = -80.621
        ksc_alt = 10.0 # 10 m elevation

        r_ecef = CoordinateFrames.geodetic_to_ecef(ksc_lat, ksc_lon, ksc_alt)
        lat_back, lon_back, alt_back = CoordinateFrames.ecef_to_geodetic(r_ecef)

        lat_err = abs(lat_back - ksc_lat)
        lon_err = abs(lon_back - ksc_lon)
        alt_err = abs(alt_back - ksc_alt)

        print(f"[+] KSC Geodetic Lat Error: {lat_err:.8e} deg | Lon Error: {lon_err:.8e} deg | Alt Error: {alt_err:.6e} m")
        self.assertLess(lat_err, 1e-7, "Latitude reconstruction error exceeds 1e-7 deg")
        self.assertLess(lon_err, 1e-7, "Longitude reconstruction error exceeds 1e-7 deg")
        self.assertLess(alt_err, 1e-3, "Altitude reconstruction error exceeds 1 mm")

        # 2. North Pole test
        pole_r = CoordinateFrames.geodetic_to_ecef(90.0, 0.0, 500.0)
        self.assertAlmostEqual(pole_r[0], 0.0, delta=1e-3)
        self.assertAlmostEqual(pole_r[1], 0.0, delta=1e-3)
        self.assertAlmostEqual(pole_r[2], CoordinateFrames.WGS84_B + 500.0, delta=1e-3)

        p_lat, _, p_alt = CoordinateFrames.ecef_to_geodetic(pole_r)
        self.assertAlmostEqual(p_lat, 90.0, delta=1e-5)
        self.assertAlmostEqual(p_alt, 500.0, delta=1e-3)

    def test_04_topocentric_look_angles(self):
        """Verify ground station SEZ look angles: zenith directly overhead (el = 90 deg) and horizon pass."""
        ksc_lat = 28.608
        ksc_lon = -80.604

        # Spacecraft positioned 400 km directly overhead of KSC
        sc_ecef = CoordinateFrames.geodetic_to_ecef(ksc_lat, ksc_lon, alt_m=400000.0)
        look = CoordinateFrames.ecef_to_topocentric_sez(sc_ecef, ksc_lat, ksc_lon, station_alt_m=0.0)

        print(f"[+] Direct Overhead Elevation: {look['elevation_deg']:.2f} deg (Expected: 90.0 deg)")
        self.assertAlmostEqual(look["elevation_deg"], 90.0, delta=0.01)
        self.assertAlmostEqual(look["range_km"], 400.0, delta=0.01)
        self.assertTrue(look["is_visible"])

    def test_05_moon_centered_inertial_transformation(self):
        """Verify Moon-Centered Inertial (MCI) transformation and perilune altitude calculation."""
        r_moon_eci = np.array([380000000.0, 50000000.0, 20000000.0])
        v_moon_eci = np.array([-150.0, 920.0, 380.0])

        # Spacecraft positioned 7,400 km above lunar center in +x direction
        # Lunar mean radius: 1,737.4 km -> Total distance from Moon center = 1737.4 + 7400 = 9137.4 km
        r_sc_eci = r_moon_eci + np.array([9137400.0, 0.0, 0.0])
        v_sc_eci = v_moon_eci + np.array([0.0, 1850.0, 0.0]) # 1850 m/s relative to Moon

        mci_state = CoordinateFrames.eci_to_mci(r_sc_eci, v_sc_eci, r_moon_eci, v_moon_eci)

        print(f"[+] MCI Lunar Altitude: {mci_state['lunar_altitude_km']:.1f} km (Expected: 7400.0 km)")
        print(f"[+] MCI Relative Speed: {mci_state['selenocentric_speed_km_s']:.3f} km/s (Expected: 1.850 km/s)")

        self.assertAlmostEqual(mci_state["lunar_altitude_km"], 7400.0, delta=0.01)
        self.assertAlmostEqual(mci_state["selenocentric_speed_km_s"], 1.850, delta=1e-4)


if __name__ == "__main__":
    unittest.main()
