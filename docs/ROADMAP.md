# Orion Digital Twin Project Roadmap & Execution Plan

This roadmap governs the progressive development of the Orion Digital Twin project across six tightly-coupled engineering phases. Each phase is independently testable, self-verifying, and requires formal user sign-off prior to progressing.

---

## Phase Overview & Acceptance Gates

```
+---------------------------------------------------------------------------------+
| Phase 1: Research, Architecture & Environment Setup  [COMPLETED & VERIFIED]     |
| - Environment inspection, verified NASA/Horizons API connectivity               |
| - System specs, mission timeline, architecture & assumptions documentation      |
| - Test suite: Automated environment & API validation harness                    |
+---------------------------------------------------------------------------------+
                                        |
                                        v  [Sign-off Gate 1: PASSED]
+---------------------------------------------------------------------------------+
| Phase 2: 3D Spacecraft Modeling (Blender 5.2 Parametric Scripting) [COMPLETED]  |
| - Parametric geometry: Crew Module, Heat Shield, ESM, Solar Arrays, LAS         |
| - Proper SI dimensions (5.029m base, 3.35m height, 19m solar wingspan)          |
| - Automated Blender headless execution, multi-format export (.gltf, .obj, .stl) |
| - Calculated volume and dry mass center-of-gravity (CG) properties              |
+---------------------------------------------------------------------------------+
                                        |
                                        v  [Sign-off Gate 2: PASSED]
+---------------------------------------------------------------------------------+
| Phase 3: MATLAB Engineering Simulation (6-DOF GNC & Trajectory) [COMPLETED]     |
| - Automated `.m` scripts and master test harness (run_phase3_simulation.m)       |
| - Trajectory propagation: TLI (dV = 3142 m/s), Lunar flyby (2662.5 km altitude) |
| - Closed-loop 6-DOF attitude control with quaternion error feedback (<0.001 deg)|
| - Extended Kalman Filter (EKF) sensor fusion (IMU + Star Tracker converged)     |
| - Skip re-entry guidance & parachute descent verified (terminal vel 8.20 m/s)   |
+---------------------------------------------------------------------------------+
                                        |
                                        v  [Sign-off Gate 3: PASSED]
+---------------------------------------------------------------------------------+
| Phase 4: Lightweight Aerodynamic, Thermal & Structural Solvers [COMPLETED]      |
| - Modified Newtonian hypersonic aerodynamic solver (CD=1.45, CL=0.44, L/D=0.30)  |
| - Stagnation aerothermal heating (Sutton-Graves) & 1D Avcoat conduction (<250 C)|
| - Thin-walled Al-Li 2195 pressure vessel stress and launch load margin (MS > 0) |
| - Skip re-entry corridor calculation & staged parachute descent deceleration    |
+---------------------------------------------------------------------------------+
                                        |
                                        v  [Sign-off Gate 4: PASSED]
+---------------------------------------------------------------------------------+
| Phase 5: Mission Visualization & Telemetry Dashboard [COMPLETED & VERIFIED]     |
| - FastAPI + WebSockets telemetry server streaming at 10 Hz                      |
| - Interactive WebGL 3D spacecraft view (Three.js) with live attitude/solar tilt |
| - Earth-Moon 3D orbit viewer, timeline slider, telemetry charts, event logs     |
| - Strict data provenance tagging: SIMULATED vs EPHEMERIS vs HISTORICAL          |
+---------------------------------------------------------------------------------+
                                        |
                                        v  [Sign-off Gate 5: PASSED]
+---------------------------------------------------------------------------------+
| Phase 6: System Integration, End-to-End Verification & Demo [COMPLETED]         |
| - End-to-end integration: CAD assets -> MATLAB/Python physics -> Live Dashboard |
| - Monte Carlo landing dispersion (100 runs, CEP = 7.67 km < 10 km, 100% capture)|
| - Master runner: run_end_to_end_demo.py & run_demo.bat one-click execution      |
| - 25/25 automated unit and integration tests passing across all 6 phases        |
+---------------------------------------------------------------------------------+
```

---

## Detailed Phase Breakdown

### Phase 1 — Research, Architecture & Environment Setup (Active)
* **Goal**: Establish the engineering foundation, verify all hardware/software prerequisites, configure API connectivity, and document spacecraft specifications and mission timeline.
* **Selected Tools**: Python 3.14 (`requests`, `python-dotenv`), PowerShell, JPL Horizons API, NASA Open API.
* **Deliverables**:
  1. `config/.env` and `config/.env.example` with verified NASA API key.
  2. `docs/ARCHITECTURE.md`, `docs/SPECS.md`, `docs/TIMELINE.md`, `docs/ASSUMPTIONS_AND_LIMITATIONS.md`, `docs/ROADMAP.md`.
  3. `scripts/verify_environment.py`: Automated environment validation script.
  4. `scripts/test_horizons_api.py`: Automated JPL Horizons ephemeris fetch script.
  5. `tests/test_phase1.py`: Unit test verifying Phase 1 outputs.
* **Acceptance Gate**: All Phase 1 tests pass, environment verified, and user reviews architecture.

### Phase 2 — 3D Spacecraft Modeling
* **Goal**: Construct accurate, parametric 3D CAD assets of the Orion stack without paid proprietary CAD tools.
* **Selected Tools**: Blender 5.2.1 LTS (`bpy` headless Python automation), `ezdxf`.
* **Deliverables**: Parametric generation scripts for CM, Heat Shield, ESM, Solar Arrays, LAS; exported `.gltf` and `.obj` models; mass properties estimate.

### Phase 3 — MATLAB Engineering Simulation
* **Goal**: Develop the orbital mechanics, 6-DOF attitude dynamics, and GNC loop.
* **Selected Tools**: MATLAB R2026a (`.m` scripts, automated batch runner) and Simulink blocks.
* **Deliverables**: Trajectory propagator, quaternion attitude controller, EKF state estimator, entry guidance, and verification plots.

### Phase 4 — Lightweight Aerodynamic, Thermal & Structural Solvers
* **Goal**: Calculate hypersonic aerodynamic coefficients, re-entry heat flux, and pressure vessel stress margins.
* **Selected Tools**: Python 3.14 / MATLAB numerical scripts (NumPy/SciPy).
* **Deliverables**: Hypersonic aerothermal model, 1D thermal conduction solver, structural load analysis, parachute descent profile.

### Phase 5 — Mission Visualization and Telemetry
* **Goal**: Deliver a responsive, real-time mission operations dashboard.
* **Selected Tools**: FastAPI, Uvicorn, WebSockets, HTML5, Three.js / Canvas.
* **Deliverables**: Backend telemetry broker, frontend mission control UI with 3D spacecraft, orbit visualizer, and telemetry plots.

### Phase 6 — Integration and Verification
* **Goal**: Couple all components into a seamless, runnable end-to-end digital twin demonstration.
* **Selected Tools**: Automated test harness, batch launch script, Monte Carlo analysis.
* **Deliverables**: End-to-end mission playback, automated tests, comprehensive user guide.
