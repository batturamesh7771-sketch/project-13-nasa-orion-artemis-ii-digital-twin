"""
Automated Unit and Integration Test Suite — Phase 5
Mission Visualization & Telemetry Dashboard for NASA Orion MPCV.
"""

import unittest
import asyncio
from pathlib import Path
from web.server import get_status, get_current_telemetry, get_mission_trajectory, get_spacecraft_specs, get_index
from web.telemetry_streamer import OrionTelemetryEngine

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class TestPhase5VisualizationAndDashboard(unittest.TestCase):
    def setUp(self):
        self.engine = OrionTelemetryEngine()

    def test_01_static_assets_integrity(self):
        """Verify all static frontend files, CSS, JS, and Three.js libraries exist."""
        static_dir = PROJECT_ROOT / "web" / "static"
        self.assertTrue(static_dir.exists(), "web/static directory missing!")
        
        required_files = [
            static_dir / "index.html",
            static_dir / "css" / "dashboard.css",
            static_dir / "js" / "three.min.js",
            static_dir / "js" / "OrbitControls.js",
            static_dir / "js" / "spacecraft3d.js",
            static_dir / "js" / "orbit3d.js",
            static_dir / "js" / "dashboard.js"
        ]
        
        for f in required_files:
            self.assertTrue(f.exists(), f"Missing frontend asset: {f}")
            self.assertGreater(f.stat().st_size, 100, f"Asset file is empty or corrupted: {f}")
            
        # Verify Three.js bundle size (> 500 KB)
        three_size = (static_dir / "js" / "three.min.js").stat().st_size
        self.assertGreater(three_size, 500000, "three.min.js appears truncated")

    def test_02_server_endpoints(self):
        """Verify FastAPI REST endpoints return status 200 and schema-compliant payloads."""
        # 1. Index HTML route
        idx = asyncio.run(get_index())
        self.assertEqual(idx.status_code, 200)
        self.assertIn("NASA Orion", idx.body.decode("utf-8"))
        self.assertIn("spacecraftCanvas", idx.body.decode("utf-8"))
        self.assertIn("orbitCanvas", idx.body.decode("utf-8"))
        self.assertIn("pfdCanvas", idx.body.decode("utf-8"))

        # 2. Server status endpoint
        status = asyncio.run(get_status())
        self.assertEqual(status["status"], "ONLINE")
        self.assertGreater(status["total_mission_sec"], 0.0)

        # 3. Current telemetry snapshot
        telem = asyncio.run(get_current_telemetry())
        self.assertIn("met_sec", telem)
        self.assertIn("trajectory", telem)
        self.assertIn("attitude", telem)
        self.assertIn("aero_thermal", telem)
        self.assertIn("propulsion_power", telem)
        self.assertIn("eclss", telem)
        self.assertIn("recovery", telem)
        self.assertIn("data_provenance", telem)

        # 4. Trajectory waypoints endpoint
        traj = asyncio.run(get_mission_trajectory())
        self.assertGreaterEqual(traj["count"], 100)
        self.assertIn("pos_eci_km", traj["waypoints"][0])

        # 5. Spacecraft specifications endpoint
        specs = asyncio.run(get_spacecraft_specs())
        self.assertEqual(specs["crew_module"]["base_diameter_m"], 5.029)
        self.assertEqual(specs["service_module"]["propellant_usable_kg"], 8618.0)

    def test_03_mission_timeline_progression(self):
        """Verify telemetry packets across all chronological Artemis mission phases."""
        # 1. SLS Ascent / LEO (t = 60s)
        p_ascent = self.engine.get_telemetry_packet(60.0)
        self.assertEqual(p_ascent["mission_stage"], "SLS_ASCENT_LEO")
        self.assertEqual(p_ascent["data_provenance"], "[HISTORICAL]")
        self.assertGreater(p_ascent["trajectory"]["altitude_km"], 0.0)
        self.assertLess(p_ascent["trajectory"]["altitude_km"], 200.0)

        # 2. TLI Burn (t = 240s)
        p_tli = self.engine.get_telemetry_packet(240.0)
        self.assertEqual(p_tli["mission_stage"], "TLI_MANEUVER")
        self.assertGreater(p_tli["trajectory"]["velocity_m_s"], 8000.0)

        # 3. Translunar Coast (t = 800s)
        p_coast = self.engine.get_telemetry_packet(800.0)
        self.assertEqual(p_coast["mission_stage"], "TRANSLUNAR_COAST")
        self.assertEqual(p_coast["data_provenance"], "[EPHEMERIS]")
        self.assertGreater(p_coast["trajectory"]["altitude_km"], 100000.0)

        # 4. Lunar Flyby (t = 1400s)
        p_flyby = self.engine.get_telemetry_packet(1400.0)
        self.assertEqual(p_flyby["mission_stage"], "LUNAR_FLYBY")
        self.assertLess(p_flyby["trajectory"]["dist_to_moon_km"], 5000.0) # Within 5,000 km

        # 5. Skip Re-entry & Splashdown (t = 2300s to 4060s)
        p_entry = self.engine.get_telemetry_packet(2300.0)
        self.assertIn("ENTRY", p_entry["mission_stage"])
        self.assertGreater(p_entry["aero_thermal"]["heat_flux_W_cm2"], 50.0)
        self.assertLess(p_entry["aero_thermal"]["g_load"], 8.0) # G-limiting guidance

        # 6. Splashdown (t = 4070s)
        p_splash = self.engine.get_telemetry_packet(4070.0)
        self.assertEqual(p_splash["mission_stage"], "OCEAN_SPLASHDOWN")
        self.assertTrue(p_splash["recovery"]["splashdown"])
        self.assertEqual(p_splash["trajectory"]["altitude_km"], 0.0)
        self.assertEqual(p_splash["trajectory"]["velocity_m_s"], 0.0)

    def test_04_data_provenance_tagging(self):
        """Verify strict data provenance tags for simulated, ephemeris, and historical telemetry."""
        valid_tags = {"[SIMULATED]", "[EPHEMERIS]", "[HISTORICAL]"}
        
        test_times = [10.0, 200.0, 750.0, 1350.0, 1800.0, 2500.0, 4080.0]
        for t in test_times:
            pkt = self.engine.get_telemetry_packet(t)
            self.assertIn(pkt["data_provenance"], valid_tags, f"Invalid provenance tag at MET {t}s")

if __name__ == "__main__":
    unittest.main()
