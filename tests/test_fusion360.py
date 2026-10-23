#!/usr/bin/env python3
"""
Unit Test for Autodesk Fusion 360 Orion Digital Twin Script & Manifest
"""

import os
import sys
import ast
import json
import unittest
from pathlib import Path

ROAMING_DIR = Path(os.environ.get("APPDATA", "")) / "Autodesk" / "Autodesk Fusion 360" / "API" / "Scripts" / "Orion_Digital_Twin"
PROJECT_FUSION_DIR = Path(__file__).resolve().parent.parent / "cad" / "fusion360"

class TestFusion360Script(unittest.TestCase):

    def test_01_script_files_exist_in_roaming(self):
        py_file = ROAMING_DIR / "Orion_Digital_Twin.py"
        manifest_file = ROAMING_DIR / "Orion_Digital_Twin.manifest"
        self.assertTrue(py_file.exists(), "Orion_Digital_Twin.py must exist in Fusion 360 AppData directory")
        self.assertTrue(manifest_file.exists(), "Orion_Digital_Twin.manifest must exist in Fusion 360 AppData directory")

    def test_02_manifest_valid_json(self):
        manifest_file = ROAMING_DIR / "Orion_Digital_Twin.manifest"
        with open(manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("autodeskProduct"), "Fusion360")
        self.assertEqual(data.get("type"), "script")

    def test_03_python_syntax_and_symbols(self):
        py_file = ROAMING_DIR / "Orion_Digital_Twin.py"
        with open(py_file, "r", encoding="utf-8") as f:
            code = f.read()
        # Verify valid Python syntax
        tree = ast.parse(code)
        self.assertIsNotNone(tree)
        # Check required sub-assemblies and kinematic joint names
        self.assertIn("ASM_01_Crew_Module_Capsule", code)
        self.assertIn("ASM_02", code)
        self.assertIn("ASM_03_OMSE_Main_Engine", code)
        self.assertIn("ASM_05_Solar_Wing", code)
        self.assertIn("ASM_06_Launch_Abort_System", code)
        self.assertIn("Jnt_OMSE_Pitch_Gimbal", code)
        self.assertIn("Jnt_LAS_Tower_Jettison", code)
        self.assertIn("Jnt_CMSM_Staging_Separation", code)

if __name__ == "__main__":
    unittest.main()
