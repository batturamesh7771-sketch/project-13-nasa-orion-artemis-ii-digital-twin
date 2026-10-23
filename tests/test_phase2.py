#!/usr/bin/env python3
"""
Unit and Integration Tests for Orion Digital Twin — Phase 2: Autodesk Fusion 360 CAD Modeling
Validates native Fusion 360 CAD scripts, manifests, parametric assembly hierarchy, and mass properties.
"""

import os
import sys
import json
import ast
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

class TestPhase2FusionCAD(unittest.TestCase):

    def test_01_fusion_scripts_exist(self):
        new_script = BASE_DIR / "cad" / "exports" / "NewScript" / "NewScript.py"
        repo_script = BASE_DIR / "cad" / "fusion360" / "Orion_Digital_Twin.py"
        roaming_script = Path(os.environ.get("APPDATA", "")) / "Autodesk" / "Autodesk Fusion 360" / "API" / "Scripts" / "Orion_Digital_Twin" / "Orion_Digital_Twin.py"
        addin_script = Path(os.environ.get("APPDATA", "")) / "Autodesk" / "Autodesk Fusion 360" / "API" / "AddIns" / "Orion_Digital_Twin" / "Orion_Digital_Twin.py"

        self.assertTrue(new_script.exists(), "NewScript.py created by user in Fusion must exist")
        self.assertTrue(repo_script.exists(), "Repository Orion_Digital_Twin.py must exist")
        self.assertTrue(roaming_script.exists(), "Installed Scripts Orion_Digital_Twin.py must exist")
        self.assertTrue(addin_script.exists(), "Installed AddIns Orion_Digital_Twin.py must exist")

    def test_02_script_ast_and_symbols(self):
        repo_script = BASE_DIR / "cad" / "fusion360" / "Orion_Digital_Twin.py"
        with open(repo_script, "r", encoding="utf-8") as f:
            code = f.read()
        tree = ast.parse(code)
        self.assertIsNotNone(tree, "Script must be valid Python syntax")
        self.assertIn("ASM_01_Crew_Module_Capsule", code)
        self.assertIn("ASM_02_Service_Module_and_Tanks", code)
        self.assertIn("ASM_03_OMSE_Main_Engine", code)
        self.assertIn("ASM_04_SAJ_Peeling_Fairings", code)
        self.assertIn("ASM_05_Solar_Wing", code)
        self.assertIn("ASM_06_Launch_Abort_System", code)
        self.assertIn("Jnt_OMSE_Pitch_Gimbal", code)
        self.assertIn("Jnt_LAS_Tower_Jettison", code)
        self.assertIn("Jnt_CMSM_Staging_Separation", code)

    def test_03_mass_properties_physical_validation(self):
        mass_json = BASE_DIR / "cad" / "mass_properties.json"
        self.assertTrue(mass_json.exists(), "mass_properties.json must exist")
        with open(mass_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        cm = data.get("crew_module", {})
        self.assertAlmostEqual(cm.get("base_diameter_m", 0.0), 5.029, delta=0.01)
        self.assertAlmostEqual(cm.get("height_m", 0.0), 3.350, delta=0.01)
        self.assertAlmostEqual(cm.get("mass_dry_kg", 0.0), 9300.0, delta=100.0)

        esm = data.get("european_service_module", {})
        self.assertAlmostEqual(esm.get("diameter_m", 0.0), 5.000, delta=0.01)
        self.assertAlmostEqual(esm.get("height_m", 0.0), 4.000, delta=0.01)
        self.assertAlmostEqual(esm.get("propellant_usable_kg", 0.0), 8618.0, delta=50.0)

        solar = data.get("solar_arrays", {})
        self.assertEqual(solar.get("wing_count"), 4)
        self.assertAlmostEqual(solar.get("total_wingspan_m", 0.0), 19.00, delta=0.5)

        las = data.get("launch_abort_system", {})
        self.assertAlmostEqual(las.get("tower_height_m", 0.0), 15.24, delta=0.1)

        launch_stack = data.get("assemblies", {}).get("launch_stack", {})
        self.assertAlmostEqual(launch_stack.get("total_mass_kg", 0.0), 35380.0, delta=500.0)

if __name__ == "__main__":
    unittest.main()
