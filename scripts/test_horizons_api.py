#!/usr/bin/env python3
"""
Orion Digital Twin - JPL Horizons Ephemeris Fetch & Parser
Fetches high-precision state vectors (position and velocity in SI units)
for the Moon relative to Earth Center, saving to JSON for trajectory verification.
"""

import re
import json
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "telemetry"

def fetch_lunar_ephemeris(start_date="2026-10-14", stop_date="2026-10-16", step_size="1d"):
    """
    Queries JPL Horizons API for the Moon (NAIF ID: 301)
    relative to Earth Geocenter (500@399) in ICRF/J2000 reference frame.
    """
    url = "https://ssd.jpl.nasa.gov/api/horizons.api"
    params = {
        "format": "json",
        "COMMAND": "'301'",           # Target: Moon
        "EPHEM_TYPE": "VECTORS",       # State vectors [X, Y, Z, VX, VY, VZ]
        "CENTER": "'500@399'",         # Coordinate Center: Earth Geocenter
        "START_TIME": f"'{start_date}'",
        "STOP_TIME": f"'{stop_date}'",
        "STEP_SIZE": f"'{step_size}'",
        "VEC_TABLE": "'2'",            # Output table style (pos + vel)
        "REF_SYSTEM": "'ICRF'",
        "VEC_CORR": "'NONE'",
        "OUT_UNITS": "'KM-S'"          # Output units: km and km/s
    }

    print(f"[*] Querying JPL Horizons API for Target: Moon (301) from Earth (399)...")
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        raw_text = payload.get("result", "")
    except Exception as e:
        cached_file = OUTPUT_DIR / "sample_lunar_ephemeris.json"
        if cached_file.exists():
            print(f"[!] Network query failed ({e}), loading verified cached Horizons ephemeris...")
            with open(cached_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                return cached_data.get("records", [])
        raise
    
    # Parse vectors between $$SOE (Start of Ephemeris) and $$EOE (End of Ephemeris)
    soe = raw_text.find("$$SOE")
    eoe = raw_text.find("$$EOE")
    if soe == -1 or eoe == -1:
        raise ValueError("Could not locate $$SOE/$$EOE boundary in Horizons response.")

    ephem_block = raw_text[soe + 5 : eoe].strip()
    records = []

    # Regex to capture JDTDB and Date followed by X, Y, Z and VX, VY, VZ
    # Horizons vector format:
    # 2460601.500000000 = A.D. 2024-Oct-18 00:00:00.0000 TDB 
    #  X = 3.791550993077977E+05 Y = 1.258673523450700E+05 Z = 6.446824982635955E+04
    #  VX=-4.004144577884784E-01 VY= 8.878516527506992E-01 VZ= 3.993414878486016E-01
    entry_pattern = re.compile(
        r"(\d+\.\d+)\s*=\s*A\.D\.\s*([\d\w\-:\. ]+)\s*\n"
        r"\s*X\s*=\s*([+\-\d\.E]+)\s*Y\s*=\s*([+\-\d\.E]+)\s*Z\s*=\s*([+\-\d\.E]+)\s*\n"
        r"\s*VX\s*=\s*([+\-\d\.E]+)\s*VY\s*=\s*([+\-\d\.E]+)\s*VZ\s*=\s*([+\-\d\.E]+)",
        re.MULTILINE
    )

    for match in entry_pattern.finditer(ephem_block):
        jd = float(match.group(1))
        date_str = match.group(2).strip()
        x_km = float(match.group(3))
        y_km = float(match.group(4))
        z_km = float(match.group(5))
        vx_kms = float(match.group(6))
        vy_kms = float(match.group(7))
        vz_kms = float(match.group(8))

        # Convert to SI units (meters and m/s)
        record = {
            "julian_date": jd,
            "utc_date": date_str,
            "position_m": {
                "x": x_km * 1000.0,
                "y": y_km * 1000.0,
                "z": z_km * 1000.0,
                "distance_km": (x_km**2 + y_km**2 + z_km**2)**0.5
            },
            "velocity_mps": {
                "vx": vx_kms * 1000.0,
                "vy": vy_kms * 1000.0,
                "vz": vz_kms * 1000.0,
                "speed_mps": (vx_kms**2 + vy_kms**2 + vz_kms**2)**0.5 * 1000.0
            },
            "provenance": "[EPHEMERIS DATA: NASA JPL Horizons]"
        }
        records.append(record)

    output_file = OUTPUT_DIR / "sample_lunar_ephemeris.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "target": "Moon (301)",
            "center": "Earth Geocenter (399)",
            "record_count": len(records),
            "records": records
        }, f, indent=2)

    print(f"[+] Successfully fetched and parsed {len(records)} lunar ephemeris records.")
    print(f"[+] Ephemeris saved to: {output_file}")
    if records:
        r0 = records[0]
        print(f"[*] Sample: Date={r0['utc_date']} | Dist={r0['position_m']['distance_km']:.1f} km | Speed={r0['velocity_mps']['speed_mps']:.1f} m/s")

    return records

if __name__ == "__main__":
    fetch_lunar_ephemeris()
