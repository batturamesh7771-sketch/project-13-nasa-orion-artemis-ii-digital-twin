#!/usr/bin/env python3
"""
Launcher script for NASA Orion Digital Twin Mission Control Dashboard.
Starts FastAPI backend server on http://127.0.0.1:8000
"""

import sys
import uvicorn
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def main():
    print("=" * 65)
    print("   NASA ORION MPCV DIGITAL TWIN — MISSION CONTROL DASHBOARD   ")
    print("=" * 65)
    print("[*] Starting FastAPI WebSockets Telemetry Server...")
    print("[*] Web Dashboard URL: http://127.0.0.1:8000")
    print("[*] Press Ctrl+C to terminate server.")
    print("=" * 65)
    
    uvicorn.run("web.server:app", host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
