# Artemis II Digital Twin — AIM 1 Repository Audit & Interface Architecture Report

**Date:** 2026-10-20  
**Phase:** Gate 1 Implementation  
**Status:** AUDIT COMPLETE & VERIFIED  

---

## 1. System Environment & Installed Tool Availability

Direct verification executed on host system:

| Tool / Framework | Verified Status | Executable / Version Details | Role in Digital Twin |
| :--- | :--- | :--- | :--- |
| **Python** | **ONLINE** | `3.14.5 (AMD64, MSC v.1944)` | Host runtime |
| **NumPy** | **ONLINE** | `2.5.3` | Matrix / vector astrodynamics |
| **FastAPI** | **ONLINE** | `0.136.3` | Mission control REST API & WebSockets broker |
| **Uvicorn** | **ONLINE** | `0.48.0` | ASGI high-performance web server |
| **WebSockets** | **ONLINE** | `16.0` | 10 Hz real-time flight telemetry stream |
| **NASA GMAT** | **ONLINE** | `R2026a (Build: Mar 26 2026)` at `E:\NASA\GMAT-R2026a\bin\GmatConsole.exe` | Independent orbital and maneuver cross-validation |
| **SciPy** | **NOT INSTALLED** | Not present in Python 3.14 environment | Native pure-Python/NumPy adaptive integrators (`DormandPrince45`) utilized |
| **SPICE (SpiceyPy)** | **NOT INSTALLED** | Not present in Python 3.14 environment | Analytical DE440/Keplerian + JPL Horizons Hermite interpolation utilized |
| **simupy-flight** | **NOT INSTALLED** | Not present | Reference equation set only; not required for 3-DOF ascent |
| **Three.js** | **ONLINE** | `r128` bundled in `web/static/js/` | Real-time WebGL 3D mission control visualization |

---

## 2. Actual AIM 2 & AIM 3 Interface Contracts

### AIM 2 (Earth–Moon Free-Return Trajectory) Contract:
- **Module:** [`simulation/trajectory/mission_propagator.py`](file:///C:/Users/user/.gemini/antigravity/scratch/orion-digital-twin/simulation/trajectory/mission_propagator.py)
- **Reference Frame:** Earth-Centered Inertial (ECI J2000 / `EarthMJ2000Eq`), origin at Earth center of mass.
- **State Vector Layout:** SI units `y = [x, y, z, vx, vy, vz, mass]` where:
  - Position: meters $[x, y, z]$
  - Velocity: meters/second $[v_x, v_y, v_z]$
  - Mass: kilograms $[m]$
- **Epoch & Time Scale:** UTC epoch `2026-04-01T22:35:00Z` (Liftoff at 6:35 p.m. EDT April 1, 2026).
- **Handoff Requirement:** AIM 2 begins immediately following the Orion TLI burn on Flight Day 2 ($\text{MET} \approx 90,840 - 91,190\text{ s}$). The initial AIM 2 state must be the modeled post-burn Orion + European Service Module (ESM) state.

### AIM 3 (Atmospheric Reentry & Recovery) Contract:
- **Module:** [`simulation/entry/coupled_entry.py`](file:///C:/Users/user/.gemini/antigravity/scratch/orion-digital-twin/simulation/entry/coupled_entry.py)
- **Entry Interface (EI-400):** Altitude $h_{\text{ei}} = 120,000\text{ m}$ ($120\text{ km}$ / $400,000\text{ ft}$), inertial velocity $v_{\text{ei}} \approx 11,050\text{ m/s}$, flight path angle $\gamma_{\text{ei}} \approx -5.85^\circ$.
- **Separation Guard:** European Service Module (ESM) jettisoned prior to entry interface; only Crew Module ($9,300\text{ kg}$) enters the atmospheric skip corridor.
- **Parachute Triggers:** Forward Bay Cover jettison at $7.9\text{ km}$ ($M < 0.75$), dual drogue mortars at $7.6\text{ km}$, triple main ringsails at $2.9\text{ km}$ with terminal splashdown target $7.8\text{ m/s} < 8.5\text{ m/s}$.

---

## 3. Data File Integrity & Gate 1 Pack Verification
All Gate 1 source files validated against schema:
- `data/aim1_source_registry.json` (15 verified sources with truth classes)
- `data/aim1_launch_event_reference.json` (5 countdown/launch events, 14 ascent/orbit events, 1 TLI event)
- `data/aim1_asset_manifest.json` (3 3D visual assets, 5 assembly scene stages)
- `schemas/aim1_to_aim2_state.schema.json` (canonical SI contract for post-TLI handoff)

Pack check result: **PASS** (`python artemis_aim1_gate1/tools/validate_gate1_pack.py`).

---

## 4. Repository File Map

```text
orion-digital-twin/
├── data/                                  # Sourced parameter registries & event reference tables
│   ├── aim1_asset_manifest.json
│   ├── aim1_launch_event_reference.json
│   └── aim1_source_registry.json
├── schemas/                               # Contract schemas
│   └── aim1_to_aim2_state.schema.json
├── simulation/
│   ├── aim1/                              # BOUNDED AIM 1 ASCENT & LAUNCH ENGINE (New)
│   │   ├── __init__.py
│   │   ├── vehicle_config.py              # Sourced SLS Block 1 + Orion mass & engine properties
│   │   ├── ascent_dynamics.py             # 3-DOF variable-mass ascent ODE solver
│   │   ├── staging_manager.py             # Event detection & stage mass dropoff
│   │   ├── orbital_operations.py          # ICPS PRM, Apogee Raise, Orion Sep & TLI burn
│   │   ├── handoff_adapter.py             # Canonical post-TLI handoff adapter into AIM 2
│   │   └── assembly_sequence.py           # VAB / Rollout / Pad deterministic visual sequence
│   ├── core/
│   │   ├── state_machine.py               # Artemis II mission phase state machine
│   │   └── __init__.py
│   ├── entry/
│   │   ├── coupled_entry.py               # AIM 3 3-DOF skip reentry & parachute engine
│   │   ├── entry_corridor_analysis.py
│   │   └── monte_carlo_dispersion.py
│   ├── scenarios/
│   │   ├── artemis_ii_scenario.json       # Official mission timeline & parameters
│   │   └── mission_scenario.py            # Scenario loader & phase resolver
│   └── trajectory/
│       ├── adaptive_integrator.py         # Dormand-Prince 5(4) / 8(5,3) RK integrators
│       ├── coordinates.py                 # ECI, ECEF, MCI transformations
│       └── mission_propagator.py          # AIM 2 multi-body astrodynamics propagator
├── telemetry/                             # Ephemeris & dispersion caches
├── tests/                                 # Unit & regression test suite (51 tests passing)
│   ├── test_aim1_ascent.py                # Dedicated AIM 1 tests (New)
│   ├── test_aim1_to_aim2_handoff.py       # Handoff continuity tests (New)
│   ├── test_gmat_aim1_orbit.py            # GMAT matched orbit insertion benchmark (New)
│   └── ...
├── tools/                                 # Build & CDP automation scripts
│   ├── gmat/                              # GMAT scripts & output comparison tools
│   └── test_all_features_live.py          # Full-stack headless browser CDP test suite
└── web/
    ├── server.py                          # FastAPI mission control server
    ├── telemetry_streamer.py              # 10 Hz telemetry broker
    └── static/
        ├── css/dashboard.css              # NASA HUD styles
        ├── js/
        │   ├── dashboard.js               # UI controller & tab switcher
        │   ├── orbit3d.js                 # 3D Earth-Moon trajectory & flight theater
        │   ├── launch3d.js                # AIM 1 SLS Launch & Pad 3D visualizer (New)
        │   └── spacecraft3d.js            # 3D Orion model viewer
        └── index.html                     # Unified Mission Control Web App
```
