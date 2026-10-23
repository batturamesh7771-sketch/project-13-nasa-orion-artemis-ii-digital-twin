# NASA Artemis II Orion MPCV Digital Twin — Master Reference & NASA Resources Directory

## 1. Project Overview & Architecture
This project is an end-to-end, high-fidelity engineering digital twin of NASA's Orion Multi-Purpose Crew Vehicle (MPCV) for the Artemis II Crewed Lunar Mission.
It includes full-mission trajectory modeling (AIM 1, AIM 2, AIM 3), 6-DoF rigid-body attitude dynamics, real-time telemetry streaming (10 Hz), Open MCT telemetry dashboards, Three.js 3D WebGL visualization, binaural audio soundscapes, interactive cockpit glass displays, Avcoat heatshield aerothermal modeling, DSN tracking link physics, and entry corridor dispersion analysis.

---

## 2. Official NASA Standards, Software, Data & References (A to Z)

| Category | NASA System / Dataset | Official Link & Documentation | Purpose in Project |
|:---|:---|:---|:---|
| **Mission Specs** | NASA Artemis II Mission Overview | https://www.nasa.gov/artemis-ii | Artemis II official crew, timeline, and trajectory parameters. |
| **Spacecraft Data** | NASA Orion Reference Guide | https://www.nasa.gov/reference/orion-spacecraft/ | Mass properties, dimensions, CM, ESM, and LAS specs. |
| **Astrodynamics** | NASA General Mission Analysis Tool (GMAT) | https://software.nasa.gov/software/GSC-17177-1 | Trajectory propagation, $16 \times 16$ gravity harmonics, TLI, and flyby. |
| **Planetary Ephemeris** | NASA NAIF SPICE Toolkit | https://naif.jpl.nasa.gov/naif/toolkit.html | High-precision barycentric planetary coordinates and state vectors. |
| **Ephemeris Kernels** | NASA JPL Planetary and Lunar Ephemerides | https://ssd.jpl.nasa.gov/planets/eph_export.html | JPL `de440s.bsp` planetary ephemeris kernel. |
| **Flight Simulation** | NASA Trick Simulation Environment | https://github.com/nasa/trick | Real-time 6-DoF numerical simulation architecture inspiration. |
| **Mission Control** | NASA Open MCT (Mission Control Technologies) | https://nasa.github.io/openmct/ | Mission control telemetry visualization framework and dictionary schema. |
| **Deep Space Network** | NASA DSN Now & Telecommunications | https://eyes.nasa.gov/dsn/dsn.html | Tracking stations: Goldstone (DSS-14), Madrid (DSS-63), Canberra (DSS-43). |
| **Space Radiation** | NASA AE9/AP9/SPM Radiation Models | https://software.nasa.gov/software/LAR-18758-1 | Van Allen radiation belts proton and electron cumulative dosimetry. |
| **Atmospheric Entry** | NASA Orion Skip Reentry & Parachutes | https://www.nasa.gov/exploration/systems/orion/reentry-and-recovery | Mach 32 entry, skip maneuver, Avcoat heatshield, drogue & main parachutes. |
| **Ephemeris Standard** | CCSDS Orbit Data Messages (OEM) | https://public.ccsds.org/Pubs/502x0b3e1.pdf | Aerospace standardized ephemeris export format. |
| **3D & Visuals** | NASA Scientific Visualization Studio (SVS) | https://svs.gsfc.nasa.gov/ | High-resolution Earth and Moon textures and lighting data. |
| **3D Models** | NASA 3D Resources / Sketchfab | https://nasa3d.arc.nasa.gov/ | SLS rocket, Orion spacecraft, and Launch Complex 39B geometry. |

---

## 3. Directory Layout in this Archive

- `cad/`: Complete 3D mesh files, OBJ/GLTF CAD models of SLS, Orion, and Pad 39B.
- `config/`: SPICE kernel configurations, mission timeline phases, and aerodynamic lookups.
- `data/`: Real-world Artemis II GMAT simulation exports, baseline ephemeris, and validation tables.
- `docs/`: Technical documentation, engineering equations, and architectural breakdown.
- `gallery_and_media/`: **100+ high-resolution screenshots**, verification captures, and render previews of every single feature from launch to ocean recovery.
- `openmct-telemetry/`: NASA Open MCT plugin configs, dictionary JSONs, and test suites.
- `scripts/`: Master end-to-end execution scripts, GMAT benchmarks, and validation tests.
- `simulation/`: 6-DoF dynamics engine, mass depletion, RCS thruster modeling, and radiation computation.
- `spice_kernels/`: Planetary ephemeris kernels for planetary barycenters.
- `telemetry/`: Telemetry state schemas, packet generators, and serializer engines.
- `web/`: Full-stack web dashboard:
  - `web/server.py`: FastAPI / Uvicorn telemetry streamer and ephemeris exporter.
  - `web/static/js/`: Three.js scene (`master_mission3d.js`), audio engine (`audio_soundscape.js`), cockpit displays, and HUD controllers.
  - `web/static/css/`: Mission Control styling and UI layouts.
- `complete_video_walkthrough_script_A_to_Z.md`: Full teleprompter video script explaining the project from A to Z.
- `PROMPTS_AND_PROJECT_EVOLUTION_LOG.md`: Step-by-step documentation of all user instructions, technical requirements, and how each feature was implemented.

---

## 4. How to Run the Digital Twin Locally

1. Install dependencies:
   ```bash
   pip install fastapi uvicorn websockets spiceypy numpy scipy
   ```
2. Start the telemetry server & WebGL Mission Control:
   ```bash
   python -m web.server
   ```
3. Open your browser to:
   - Dashboard: `http://127.0.0.1:8000/`
   - 3D Theater: `http://127.0.0.1:8000/#theater`
