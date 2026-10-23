# Project Architecture & Subsystem Integration
## NASA Orion Digital Twin (MPCV)

### 1. Architectural Philosophy
The NASA Orion Multi-Purpose Crew Vehicle (MPCV) digital twin is structured as a modular, hardware-conscious cyber-physical software simulator. It captures the complete lifecycle of an Artemis lunar mission—from SLS ascent, translunar injection (TLI), lunar flyby, trans-Earth return, skip atmospheric re-entry, to parachute splashdown and recovery.

```
       +-----------------------------------------------------------+
       |                  NASA & JPL Public Data                   |
       |  - JPL Horizons Ephemeris API (Earth/Moon/Orion states)    |
       |  - NASA Open APIs / Artemis Historical Telemetry Logs     |
       +-----------------------------+-----------------------------+
                                     |
                                     v
+------------------------------------+------------------------------------+
|                      Orion Digital Twin Engine                          |
|                                                                         |
|  +------------------------+  +-------------------+  +----------------+  |
|  |     3D CAD Geometry    |  | MATLAB / Simulink |  | Aerothermal &  |  |
|  |  Parametric Blender    |  | 6-DOF Dynamics    |  | Structural     |  |
|  |  (CM, ESM, LAS, Solar) |  | GNC, Orbital Prop |  | Approximations |  |
|  |  Export: GLTF, OBJ     |  | Kalman Filtering  |  | Fay-Riddell    |  |
|  +-----------+------------+  +---------+---------+  +--------+-------+  |
|              |                         |                     |          |
|              +-------------------------+---------------------+          |
|                                        |                                |
|                                        v                                |
|                       +---------------------------------+               |
|                       |  Telemetry Aggregator & Broker  |               |
|                       |  FastAPI / Python Telemetry Hub |               |
|                       |  Tagging: SIMULATED / EPHEMERIS |               |
|                       +----------------+----------------+               |
+----------------------------------------|--------------------------------+
                                         | WebSockets / REST
                                         v
       +-----------------------------------------------------------+
       |               Real-Time Mission Dashboard                 |
       |  - Three.js / WebGL 3D Spacecraft Attitude & Solar Arrays |
       |  - 2D / 3D Earth-Moon Trajectory Map                      |
       |  - Subsystem Panels: Propulsion, Power, ECLSS, Thermal    |
       |  - Mission Timeline Event Sequencer                       |
       +-----------------------------------------------------------+
```

---

### 2. Subsystem Functional Breakdown

| Subsystem | Physical Hardware Equivalent | Digital Twin Modeling Approach | Data In / Out |
| :--- | :--- | :--- | :--- |
| **Crew Module (CM)** | Al-Li 2195 pressure vessel, 4-crew cabin, forward bay cover | Parametric 3D shell; mass properties; cabin pressure dynamics (101.3 kPa $N_2/O_2$); 12 RCS thrusters (160 N MR-104G) | In: RCS firing commands, cabin setpoints.<br>Out: CM mass, CG, MOI, cabin telemetry. |
| **European Service Module (ESM)** | ESA/Airbus cylindrical service module, OMS-E 25.7 kN engine, 8 auxiliary thrusters (490 N), 24 RCS (220 N) | Variable-mass thrust vector model; staging logic; bipropellant consumption ($I_{sp}=316\text{ s}$); 4 solar array articulation (11.2 kW) | In: Main engine throttle, TVC gimbal, RCS pulses.<br>Out: Thrust vector, net $\Delta V$, propellant mass. |
| **Launch Abort System (LAS)** | Solid rocket abort tower (1,760 kN abort motor, 31 kN ACM, 178 kN jettison motor) | Ascent abort envelope calculations; nominal jettison at $T+200\text{ s}$ following booster separation | In: Ascent timeline trigger.<br>Out: Staging status, mass decrement. |
| **GNC & Flight Dynamics** | Quad-redundant Honeywell computers, Star Trackers, MIMUs, GPS/DSN nav | 6-DOF rigid-body dynamics (quaternion kinematics, Euler rotational equations); Cowell orbital propagator with $J_2$ and Lunar gravity; Extended Kalman Filter (EKF) sensor fusion | In: Sensor noisy vectors, target trajectory.<br>Out: Estimated state ($\mathbf{r}, \mathbf{v}, \mathbf{q}, \boldsymbol{\omega}$), actuation commands. |
| **Thermal Protection System (TPS)** | 5.0 m Avcoat ablative heat shield, AETB-8 silica tiles, thermal blankets | Stagnation heat flux calculation ($\dot{q}_{stag}$ via Sutton-Graves & Fay-Riddell); 1D transient heat conduction through Avcoat; ablation mass-loss rate | In: Aerodynamic freestream velocity, altitude, air density.<br>Out: Surface temperature, backface temperature, ablation recession. |
| **Earth Landing System (ELS)** | 2 drogue parachutes (7 m dia), 3 pilot chutes (3.4 m dia), 3 main chutes (35.4 m dia), CMUS airbags | Staged parachute deceleration model; dynamic pressure triggers; steady-state terminal velocity ($\sim 8\text{ m/s}$); splashdown g-load estimate | In: Altitude, dynamic pressure $q$, descent velocity.<br>Out: Parachute state, drag force, splashdown impact. |
| **Telemetry & Communications** | Deep Space Network (DSN) & TDRS transponders, Ka/S-band | Simulated CCSDS-compliant packet stream; JSON broadcast via WebSockets; real-time telemetry streaming at 1–10 Hz | In: All subsystem state variables.<br>Out: WebSocket JSON packets with provenance metadata. |

---

### 3. Tool Selection & Lightweight Strategy

Considering the system's hardware specifications (Intel Core i5-5200U dual-core, 8 GB RAM, Windows 10 Pro):

1. **CAD & 3D Visualization**:
   - **Blender 5.2.1 LTS** via headless Python scripting (`bpy`):
     - Avoids high-cost, proprietary CAD installations.
     - Generates exact parametric geometry for the Crew Module, ESM, Solar Arrays, and LAS.
     - Direct export to standardized `.gltf` / `.glb` for web dashboard rendering and `.obj` / `.stl` for geometric checks.
2. **Simulation & Flight Dynamics**:
   - **MATLAB R2026a & Simulink**:
     - Core 6-DOF equations of motion, quaternion kinematics, and Kalman filtering.
     - Run scriptable `.m` files with automated execution and validation tests.
     - Leverage Simulink / Simscape (`physmod`) blocks where beneficial.
3. **Aerodynamics & Structures**:
   - Closed-form analytical and empirical solutions:
     - Aerodynamics: Modified Newtonian impact theory for blunt-body hypersonic capsules ($C_D \approx 1.2 - 1.65$).
     - Aerothermodynamics: Sutton-Graves and Fay-Riddell stagnation heat flux calculations.
     - Structures: Thin-wall pressure vessel stress ($\sigma_h = \frac{p r}{t}$, $\sigma_l = \frac{p r}{2t}$) and inertial launch load factors.
4. **Telemetry Server & Web Dashboard**:
   - **Python 3.14 + FastAPI + Uvicorn + WebSockets**:
     - Asynchronous, ultra-low memory footprint (<50 MB RAM).
     - Feeds real-time telemetry at 10 Hz.
   - **Frontend Dashboard**:
     - Modern HTML5, Three.js, and CSS responsive layout.
     - Fully offline-functional with optional live JPL Horizons sync.
