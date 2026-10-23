#!/usr/bin/env python3
"""
Orion Digital Twin - Phase 2 CAD Generation Launcher
Executes Blender 5.2 headlessly to generate all 3D CAD models, exports, and renders.
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CAD_SCRIPT = BASE_DIR / "cad" / "build_orion_cad.py"
ENV_FILE = BASE_DIR / "config" / ".env"

def get_blender_path():
    blender_path = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("BLENDER_EXE_PATH="):
                    p = line.split("=", 1)[1].strip()
                    if os.path.exists(p):
                        blender_path = p
    return blender_path

def run_cad_builder():
    blender_exe = get_blender_path()
    if not os.path.exists(blender_exe):
        print(f"[-] Error: Blender executable not found at '{blender_exe}'")
        return False

    cmd = [
        blender_exe,
        "--background",
        "--python", str(CAD_SCRIPT)
    ]

    print(f"[*] Launching Blender 5.2 headless CAD generator...")
    print(f"[*] Command: {' '.join(cmd)}")
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("--- Stderr Warnings ---")
        print(res.stderr)

    return res.returncode == 0

if __name__ == "__main__":
    success = run_cad_builder()
    sys.exit(0 if success else 1)
