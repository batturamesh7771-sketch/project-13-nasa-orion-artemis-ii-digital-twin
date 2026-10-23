# NASA Orion Artemis II Digital Twin — Complete Prompts & Evolution Log

This document records the complete sequence of prompts, requirements, feature additions, and engineering milestones that transformed this project from an initial concept into a full-scale digital twin.

---

## Phase 1: Core Trajectory & Astrodynamics (AIM 1 & AIM 2)
- **Requirements**:
  - Implement full-mission propagation for Artemis II: Pad 39B launch, SLS ascent, MECO, TLI burn, lunar free-return flyby, and trans-Earth trajectory.
  - Integrate **NASA GMAT** scripts and validate orbital parameters against NASA SPICE `de440s` planetary kernels.
  - Implement 6-DoF attitude kinematics with Euler angle transitions and quaternion state integration.
  - Build AE9/AP9 ionizing radiation model calculating proton/electron flux across the Van Allen belts.

## Phase 2: NASA Open MCT Telemetry Integration
- **Requirements**:
  - Connect a real-time telemetry streaming engine emitting 10 Hz telemetry packets over WebSockets.
  - Support NASA Open MCT dictionary format, channels for altitude, velocity, acceleration, propellant mass, thruster telemetry, and life support systems.
  - Display live telemetry gauges and time-history trend plots.

## Phase 3: High-Fidelity 3D WebGL Simulation & CAD Modeling
- **Requirements**:
  - PBR 3D models for SLS Block 1, Orion Command Module (CM), European Service Module (ESM), solar array wings, and Launch Abort System (LAS).
  - Accurate spatial representations of Kennedy Space Center Pad 39B, Earth with atmosphere shader, and high-resolution Moon.
  - Interactive camera modes: Free Orbit, Cockpit PFD view, Earth-Moon System view, and Pad 39B Tracking.

## Phase 4: AIM 3 Skip Reentry, Aerothermal Heating & Recovery
- **Requirements**:
  - Complete simulation of Mach 32 atmospheric entry, including the Lunar Skip Reentry trajectory.
  - Peak aerothermal heating simulation with Avcoat ablative heatshield reaching 5,000°F (2,760°C).
  - Parachute deployment sequence: Forward bay cover jettison, drogue parachutes deployment at 25,000 ft, and main parachute reefing sequence at 9,500 ft.
  - Pacific Ocean splashdown, buoyant wave dynamics, Crew Module Uprighting System (CMUS) airbags, and US Navy recovery vessel tracking.

## Phase 5: The 6 Core Engineering Upgrades
1. **Audio Soundscape & CAPCOM Voice Calls**: Web Audio API synthesizer for cabin life-support ambiance, thruster bursts, reaction wheel hum, and simulated Quindar-tone CAPCOM voice calls.
2. **Orion Cockpit Interior & Glass Displays**: Interactive Primary Flight Display (PFD) with artificial horizon, pitch ladder, roll pointer, and Mach/altitude ladder.
3. **DSN Antenna Dish Tracking & RF Link Physics**: Real-time pointing angles (azimuth/elevation) for Goldstone, Madrid, and Canberra dishes, free-space path loss (FSPL), and lunar far-side radio blackout.
4. **Avcoat Heatshield 3D Aerothermal Heatmap**: Dynamic thermal vertex shader visualizing temperature contours and stagnation point pressure.
5. **Entry Corridor Dispersions & Abort Modes**: Entry Flight Path Angle ($\gamma$) corridor chart (nominal $-5.85^\circ$), Pad Abort 1 (PA-1), and Ascent Abort 2 (AA-2 at Max-Q) simulation routines.
6. **Engineering Ephemeris Export Suite**: Instant export to standardized **CCSDS OEM**, **Google Earth KML**, and high-resolution **CSV**.
