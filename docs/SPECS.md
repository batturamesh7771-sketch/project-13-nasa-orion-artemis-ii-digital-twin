# NASA Orion MPCV & Artemis Official Specifications

This document defines the baseline technical parameters for the NASA Orion Multi-Purpose Crew Vehicle (MPCV) digital twin, synthesized directly from official NASA and ESA technical documentation.

---

## 1. Master Mass Properties & Dimensions

| Parameter | Official NASA / ESA Value | Digital Twin SI Baseline | Verification Source / Reference |
| :--- | :--- | :--- | :--- |
| **Crew Module (CM) Base Diameter** | $5.029\text{ m}$ ($16.5\text{ ft}$) | $5.029\text{ m}$ | NASA Fact Sheet FS-2014-08-004-JSC |
| **Crew Module Height** | $3.35\text{ m}$ ($11.0\text{ ft}$) | $3.350\text{ m}$ | NASA Orion Reference Guide 2022 |
| **Pressurized Volume** | $19.56\text{ m}^3$ ($690.6\text{ ft}^3$) | $19.56\text{ m}^3$ | NASA Artemis I Press Kit |
| **Habitable Volume** | $9.0\text{ m}^3$ ($316\text{ ft}^3$) | $9.00\text{ m}^3$ | NASA Orion Quick Facts |
| **CM Dry Mass** | $\sim 9,300 - 10,387\text{ kg}$ | $9,300\text{ kg}$ | NASA / Lockheed Martin MPCV Mass Report |
| **CM Nominal Re-entry Mass** | $\sim 9,300\text{ kg}$ ($20,500\text{ lb}$) | $9,300\text{ kg}$ | NASA Artemis Post-Flight Briefing |
| **European Service Module (ESM) Diameter** | $5.00\text{ m}$ ($16.4\text{ ft}$) | $5.000\text{ m}$ | ESA European Service Module Factsheet |
| **ESM Height (Cylinder Body)** | $4.00\text{ m}$ ($13.1\text{ ft}$) | $4.000\text{ m}$ | ESA European Service Module Factsheet |
| **ESM Total Height (including nozzle)** | $4.50\text{ m}$ | $4.500\text{ m}$ | ESA / Airbus Defence and Space |
| **ESM Dry Mass** | $\sim 3,800\text{ kg}$ ($8,380\text{ lb}$) | $3,800\text{ kg}$ | ESA Orion ESM Operations Handbook |
| **ESM Usable Propellant Mass** | $8,600 - 8,620\text{ kg}$ ($19,000\text{ lb}$) | $8,618\text{ kg}$ | NASA Artemis I Trajectory Baseline |
| **ESM Wet Mass** | $\sim 13,500 - 15,500\text{ kg}$ | $15,460\text{ kg}$ | ESA / Airbus Spacecraft Specification |
| **Solar Array Tip-to-Tip Wingspan** | $19.0\text{ m}$ ($62.3\text{ ft}$) | $19.00\text{ m}$ | ESA ESM Solar Wing Specification |
| **Solar Array Output Power** | $11.2\text{ kW}$ (at $1\text{ AU}$) | $11,200\text{ W}$ | ESA / Airbus Power Subsystem Specs |
| **Launch Abort System (LAS) Tower Height**| $15.24\text{ m}$ ($50.0\text{ ft}$) | $15.24\text{ m}$ | NASA LAS Fact Sheet |
| **LAS Total Wet Mass** | $\sim 7,300\text{ kg}$ ($16,000\text{ lb}$) | $7,300\text{ kg}$ | NASA Ascent Abort-2 (AA-2) Profile |
| **Spacecraft at Liftoff (Stack Mass)** | $\sim 33,500 - 35,380\text{ kg}$ | $35,380\text{ kg}$ | NASA Artemis Flight Summary Document |

---

## 2. Propulsion System Parameters

### 2.1 ESM Orbital Maneuvering System - Engine (OMS-E)
* **Heritage**: Space Shuttle Orbital Maneuvering System engine (Aerojet Rocketdyne AJ10-190).
* **Propellants**: Monomethylhydrazine (MMH) fuel and Dinitrogen Tetroxide / Mixed Oxides of Nitrogen (MON-3) oxidizer.
* **Vacuum Thrust**: $25.7\text{ kN}$ ($5,770\text{ lbf}$).
* **Vacuum Specific Impulse ($I_{sp}$)**: $316\text{ s}$.
* **Nozzle Expansion Ratio**: $55:1$.
* **Gimbal Capability**: Dual-axis electro-mechanical gimbal ($\pm 7.0^\circ$ pitch and yaw).

### 2.2 ESM Auxiliary & RCS Thrusters
* **Auxiliary Thrusters**: 8 $\times$ Aerojet Rocketdyne R-4D-11 thrusters ($490\text{ N}$ each, $I_{sp} \approx 312\text{ s}$).
* **RCS Thrusters**: 24 thrusters grouped in 6 pods ($220\text{ N}$ each, $I_{sp} \approx 287\text{ s}$) providing 3-axis translation and attitude control during orbital flight.

### 2.3 Crew Module Reaction Control System (CM RCS)
* **Configuration**: 12 $\times$ MR-104G monopropellant (hydrazine) thrusters.
* **Thrust per Thruster**: $160\text{ N}$ ($36\text{ lbf}$).
* **Specific Impulse ($I_{sp}$)**: $220 - 230\text{ s}$.
* **Function**: Attitude control during atmospheric entry orientation and guidance bank angle modulation.

### 2.4 Launch Abort System Motors
* **Abort Motor**: Solid propellant, reverse-flow 4-nozzle configuration; $1,760\text{ kN}$ ($395,000\text{ lbf}$) thrust.
* **Attitude Control Motor (ACM)**: Solid propellant gas generator with 8 proportional radial pintle nozzles; $31\text{ kN}$ ($7,000\text{ lbf}$).
* **Jettison Motor**: Solid propellant motor to separate LAS tower from CM; $178\text{ kN}$ ($40,000\text{ lbf}$).

---

## 3. Mission $\Delta V$ Budget (Artemis Lunar Trajectory)

| Maneuver | Nominal $\Delta V$ Target | Executing Propulsion Stage | Propellant Expended (approx) |
| :--- | :--- | :--- | :--- |
| **Trans-Lunar Injection (TLI)** | $\approx 3,050 - 3,400\text{ m/s}$ | SLS ICPS (Interim Cryogenic Stage) | ICPS $LH_2/LOX$ |
| **Outbound Trajectory Correction (OTC-1 to OTC-3)** | $50 - 100\text{ m/s}$ | ESM Auxiliary / RCS | $\sim 250\text{ kg}$ |
| **Outbound Powered Flyby (OPF)** | $180 - 250\text{ m/s}$ | ESM OMS-E Main Engine | $\sim 1,100\text{ kg}$ |
| **Distant Retrograde Orbit Insertion (DROI)** | $100 - 150\text{ m/s}$ | ESM OMS-E Main Engine | $\sim 650\text{ kg}$ |
| **Distant Retrograde Orbit Departure (DROD)** | $120 - 170\text{ m/s}$ | ESM OMS-E Main Engine | $\sim 750\text{ kg}$ |
| **Return Powered Flyby (RPF)** | $200 - 300\text{ m/s}$ | ESM OMS-E Main Engine | $\sim 1,350\text{ kg}$ |
| **Return Trajectory Corrections (RTC-1 to RTC-3)** | $30 - 60\text{ m/s}$ | ESM Auxiliary / RCS | $\sim 180\text{ kg}$ |
| **CM Entry Corridor Correction** | $10 - 25\text{ m/s}$ | CM RCS Hydrazine Thrusters | $\sim 45\text{ kg}$ |
| **Total Orion Propellant Margin** | Reserve: $>5\%$ | ESM Tanks | $\sim 450\text{ kg}$ remaining at CM/SM sep |

---

## 4. Thermal Protection System (TPS)

* **Base Heat Shield**:
  * Diameter: $5.029\text{ m}$ circular spherical cap.
  * Material: **Avcoat** (epoxy novolac resin filled with hollow phenolic microballoons and silica glass fibers inside fiberglass honeycomb matrix).
  * Design Peak Re-entry Velocity: $\sim 11.0\text{ km/s}$ ($24,600\text{ mph}$ / Mach 32).
  * Peak Temperature Experienced: $\sim 2,760^\circ\text{C} - 2,800^\circ\text{C}$ ($\sim 5,000^\circ\text{F}$).
  * Peak Heat Flux: $100 - 220\text{ W/cm}^2$.
* **Conical Backshell**:
  * Material: $\sim 1,300$ Advanced Engineered Ceramic Foam Tiles (AETB-8) coated with Reaction Cured Glass (RCG).
  * Flexible Reusable Surface Insulation (FRSI) blankets for low-temperature aft areas.

---

## 5. Earth Landing System (ELS) Deployment Sequence

| Event / Chute Phase | Nominal Altitude | Velocity Range | Quantity & Dimensions |
| :--- | :--- | :--- | :--- |
| **Forward Bay Cover (FBC) Jettison** | $\sim 7,620\text{ m}$ ($25,000\text{ ft}$) | $\sim 175\text{ m/s}$ ($390\text{ mph}$) | 2 $\times$ FBC thrusters & jettison chutes |
| **Drogue Parachutes Deployment** | $\sim 7,300\text{ m}$ ($24,000\text{ ft}$) | $\sim 145\text{ m/s}$ ($325\text{ mph}$) | 2 $\times$ conical ribbon chutes ($7.0\text{ m}$ / $23\text{ ft}$ dia) |
| **Drogue Release & Pilot Chutes** | $\sim 2,900\text{ m}$ ($9,500\text{ ft}$) | $\sim 58\text{ m/s}$ ($130\text{ mph}$) | 3 $\times$ pilot chutes ($3.4\text{ m}$ / $11\text{ ft}$ dia) |
| **Main Parachutes Deployment** | $\sim 2,750\text{ m}$ ($9,000\text{ ft}$) | $\sim 50\text{ m/s}$ | 3 $\times$ ringsail parachutes ($35.4\text{ m}$ / $116\text{ ft}$ dia) |
| **Splashdown Speed** | Sea Level | $\sim 7.5 - 8.2\text{ m/s}$ ($17 - 18\text{ mph}$) | Steady-state terminal descent under 3 mains |
| **Uprighting System (CMUS)** | Sea Level (Ocean) | Zero velocity | 5 $\times$ inflatable spherical airbags ($1.8\text{ m}$ dia) |

---

## 6. Official References & Document IDs

1. **NASA JSC**: *Orion Quick Facts*, Reference Sheet FS-2014-08-004-JSC.
2. **NASA**: *Artemis I Press Kit: Exploration Ground Systems, Space Launch System, Orion*, Nov 2022.
3. **NASA / Lockheed Martin**: *Orion Crew Module Architecture and Structural Sizing*, AIAA 2018-0134.
4. **ESA (European Space Agency)**: *European Service Module for Orion (ESM) Media Briefing*, ESA-HQ-BR-2022-001.
5. **NASA JPL**: *Horizons On-Line Ephemeris System API Documentation*, Solar System Dynamics Group.
