# Subsystem Model Inventory & Technical Specification
## NASA Orion MPCV / Artemis II Digital Twin

**Document Version**: 2.0-AUDIT  
**Date**: October 19, 2026  
**Status**: Engineering Inventory (Prototype Baseline — NOT NASA-Validated)  
**Standard**: NASA SP-8000 / AIAA Simulation Standards

---

## Subsystem Model Matrix

| Subsystem | Model Name | Coordinate Frames | Primary Governing Equations | Input Sources & Assumptions | Current Implementation | Validation Gap |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Astrodynamics & Orbital Mechanics** | Two-Body Keplerian & J2 Perturbation + 3rd Body Moon | ECI (J2000), Earth-Moon Rotating | $\ddot{\vec{r}} = -\frac{\mu_E}{r^3}\vec{r} + \vec{a}_{J2} + \mu_M \left( \frac{\vec{r}_{M}-\vec{r}}{\|\vec{r}_{M}-\vec{r}\|^3} - \frac{\vec{r}_{M}}{r_M^3} \right)$ | JPL Horizons ephemeris, NASA Artemis II Trajectory Baseline. Assumes point-mass Moon. | Python DP5(4) adaptive & MATLAB RK4 fixed ($\Delta t = 60\text{ s}$). | MATLAB model lacks adaptive step control and Jacobi energy monitoring. |
| **2. Attitude Dynamics & GNC** | 6-DOF Quaternion Kinematics & Euler Rotational Dynamics | Body Frame, ECI | $\dot{\vec{q}} = \frac{1}{2} \boldsymbol{\Omega}(\vec{\omega}) \vec{q}$, $\mathbf{J} \dot{\vec{\omega}} + \vec{\omega} \times (\mathbf{J}\vec{\omega}) = \vec{\tau}_{\text{ctrl}} + \vec{\tau}_{\text{ext}}$ | Assumes rigid body inertia tensor $\mathbf{J}$. Diagonal inertia approximation. | MATLAB `attitude_dynamics.m`, `attitude_controller.m`, `ekf_estimator.m`. | Decoupled from live web streamer and 3D visualizer; no sensor latency. |
| **3. Hypersonic Aerodynamics** | Modified Newtonian Continuum Panel Solver | Body Axis, Wind Axis | $C_p = C_{p,\max} (\hat{n} \cdot \hat{v}_\infty)^2$, $C_{p,\max} = \text{Rayleigh-Pitot}(M_\infty, \gamma)$ | Hypersonic continuum flow ($M > 25$, Knudsen $Kn \ll 0.01$). Frozen chemistry. | Python `simulation/aero/modified_newtonian.py`. | Ignores rarefied flow / transitional DSMC regime ($h > 95\text{ km}$) and shoulder radius. |
| **4. Aerothermodynamics & TPS** | Sutton-Graves Convective & Tauber-Sutton Radiative + 1D Conduction | 1D Through-Thickness ($x \in [0, L]$) | $q_{\text{conv}} = k_{sg}\sqrt{\frac{\rho}{R_n}}v_\infty^3$, $\rho C_p \frac{\partial T}{\partial t} = \frac{\partial}{\partial x}\left( k \frac{\partial T}{\partial x} \right)$ | Stagnation spherical cap $R_n = 6.0\text{ m}$. Virgin Avcoat thermal properties. | Python `simulation/thermal/aerothermal_heating.py`. | 1D only; ignores 2D/3D thermal soak, pyrolysis gas blowing, and tile spallation. |
| **5. Entry Corridor & Guidance** | 3-DOF Atmospheric Flight with Bank Modulation | Trajectory Wind / Velocity Frame | $\dot{h} = v\sin\gamma$, $\dot{v} = -\frac{D}{m} - g\sin\gamma$, $\dot{\gamma} = \frac{L\cos\sigma}{mv} - \left(\frac{g}{v} - \frac{v}{r}\right)\cos\gamma$ | US Standard Atmosphere 1976. Constant trim $C_D = 1.25, C_L = 0.35$. | Python `entry_corridor_analysis.py`, `monte_carlo_dispersion.py`. | Guidance uses heuristic bank triggers instead of NASA Predictor-Corrector Guidance. |
| **6. Parachute Deceleration** | Multi-Stage Drogue & Main Reefed Parachutes | Inertial / Local Vertical | $F_{\text{drag}} = \frac{1}{2}\rho v^2 (C_d A)_{\text{eff}}(t)$, $(C_d A)_{\text{eff}} = (C_d A)_0 + \Delta (C_d A) (1 - e^{-t/\tau})$ | Nominal atmospheric descent. Infinite line stiffness (no aeroelastic flutter). | Python `entry_corridor_analysis.py`, MATLAB `entry_equations.m`. | Parachute pendular oscillation and wake interaction not modeled. |
| **7. Structural Mechanics** | Thin-Walled Shell Membrane & Brazier Buckling | Vehicle Cylindrical / Cone Coordinates | $\sigma_h = \frac{p R}{t_{\text{eff}}}$, $\sigma_l = \frac{p R}{2 t_{\text{eff}}} \pm \frac{M c}{I} - \frac{F_a}{A}$, $\sigma_{\text{cr}} = 0.605 \gamma_k E \frac{t}{R}$ | Al-Li 2195-T8 material constants. Smeared orthogrid stiffness. | Python `simulation/structures/pressure_vessel_analysis.py`. | No FEA stress concentration at hatch cutouts or aft heat-shield attachment ring. |
| **8. Propulsion & Mass Depletion** | Tsiolkovsky Continuum Rocket Depletion | Body Center of Mass | $\frac{dm}{dt} = -\frac{T}{I_{sp} g_0}$, $\Delta v = I_{sp} g_0 \ln\left(\frac{m_0}{m_f}\right)$ | OMS-E AJ10-190 vacuum thrust $T = 26,700\text{ N}, I_{sp} = 316\text{ s}$. | Python `adaptive_integrator.py`, MATLAB `orion_params.m`. | In telemetry streamer, mass was subtracted linearly without propellant integration. |
| **9. ECLSS** | Atmospheric Pressure & Gas Partial Pressures | Cabin Volume ($19.55\text{ m}^3$) | $P_{\text{tot}} = P_{\text{O}_2} + P_{\text{N}_2} + P_{\text{CO}_2}$, $\frac{d n_i}{dt} = \dot{n}_{i,\text{supply}} - \dot{n}_{i,\text{leak}} - \dot{n}_{i,\text{metab}}$ | 4 crew members. Nominal sea-level equivalent mix ($21\%\text{ O}_2$). | Web streamer (currently hardcoded static constants). | Complete dynamic gas metabolic integration currently missing. |
| **10. Electrical Power (EPS)** | Solar Array Articulation & Li-ion Battery SOC | Solar Vector, Body Frame | $P_{\text{gen}} = \eta A_{\text{sa}} I_{\text{sun}} (\hat{n}_{\text{sa}} \cdot \hat{s})$, $\frac{d(\text{SOC})}{dt} = \frac{P_{\text{gen}} - P_{\text{load}}}{V_{\text{bus}} Q_{\text{batt}}}$ | 4 solar wings ($A_{\text{sa}} = 39.7\text{ m}^2$). Battery capacity $120\text{ Ah}$. | Web streamer (currently hardcoded linear decay). | Thermal efficiency degradation and solar shadow eclipses not dynamic. |

---

## Subsystem Technical Specifications

### 1. Astrodynamics & Orbital Mechanics
- **Model ID**: `ASTRO-01`
- **Governing Equations**:
  $$\frac{d\vec{r}}{dt} = \vec{v}$$
  $$\frac{d\vec{v}}{dt} = -\frac{\mu_E}{\|\vec{r}\|^3}\vec{r} - \frac{3}{2}J_2 \mu_E \frac{R_E^2}{r^5} \begin{bmatrix} x(1 - 5z^2/r^2) \\ y(1 - 5z^2/r^2) \\ z(3 - 5z^2/r^2) \end{bmatrix} + \mu_M \left( \frac{\vec{r}_M - \vec{r}}{\|\vec{r}_M - \vec{r}\|^3} - \frac{\vec{r}_M}{\|\vec{r}_M\|^3} \right)$$
- **Units**: Distance in meters ($\text{m}$), velocity in meters per second ($\text{m/s}$), gravitational parameters in $\text{m}^3/\text{s}^2$.
- **Coordinate Frames**:
  - Primary: Earth-Centered Inertial (ECI - J2000 equator and equinox).
  - Secondary: Moon-Centered Inertial (MCI) for close flyby evaluation.
- **Inputs & Sourced Parameters**:
  - $\mu_E = 3.986004418 \times 10^{14}\text{ m}^3/\text{s}^2$ (WGS-84 / EGM96)
  - $R_E = 6,378,137.0\text{ m}$ (WGS-84 equatorial)
  - $J_2 = 1.08263 \times 10^{-3}$ (Earth oblateness zonal harmonic)
  - $\mu_M = 4.9048695 \times 10^{12}\text{ m}^3/\text{s}^2$
  - $\vec{r}_M(t)$: Sourced via JPL Horizons API (NAIF ID: 301).
- **Assumptions**: Point-mass central bodies; solar radiation pressure neglected; atmospheric drag truncated at $120\text{ km}$.
- **Validation**:
  - Tested in `tests/test_physics_rigor.py`: Two-body energy conservation $|(E - E_0)/E_0| < 2.8 \times 10^{-8}$ over 3 full orbits.
  - Angular momentum conservation $|(h - h_0)/h_0| < 8.2 \times 10^{-9}$.

---

### 2. Hypersonic Aerodynamics
- **Model ID**: `AERO-01`
- **Governing Equations**:
  For windward surface panels ($\hat{n} \cdot \hat{v}_\infty > 0$):
  $$C_p = C_{p,\max} (\hat{n} \cdot \hat{v}_\infty)^2$$
  $$C_{p,\max} = \frac{2}{\gamma M_\infty^2} \left[ \left( \frac{\gamma+1}{2} M_\infty^2 \right)^{\frac{\gamma}{\gamma-1}} \left( \frac{\gamma+1}{2\gamma M_\infty^2 - (\gamma-1)} \right)^{\frac{1}{\gamma-1}} - 1 \right] \xrightarrow{M_\infty \gg 1} \frac{\gamma+3}{\gamma+1} \approx 1.839$$
  $$d\vec{F}_{\text{aero}} = - C_p q_\infty \hat{n} dA, \quad q_\infty = \frac{1}{2}\rho v_\infty^2$$
  $$C_D = \frac{\vec{F}_{\text{total}} \cdot \hat{u}_{\text{drag}}}{q_\infty A_{\text{ref}}}, \quad C_L = \frac{\vec{F}_{\text{total}} \cdot (-\hat{u}_{\text{lift}})}{q_\infty A_{\text{ref}}}$$
- **Units**: Aerodynamic coefficients dimensionless ($[-]$); dynamic pressure in Pascals ($\text{Pa}$); surface area in square meters ($\text{m}^2$).
- **Coordinate Frames**: Body-fixed reference frame ($X_{\text{body}}$ forward along symmetry axis, $Z_{\text{body}}$ in pitch plane towards heat shield offset) and Wind frame ($X_{\text{wind}}$ aligned with freestream velocity).
- **Inputs & Sourced Parameters**:
  - Base diameter $D = 5.029\text{ m}$ ($A_{\text{ref}} = 19.863\text{ m}^2$)
  - Total capsule height $H = 3.350\text{ m}$
  - Heat shield spherical cap radius $R_{\text{hs}} = 6.000\text{ m}$
  - Frustum half cone angle $\theta_c = 33.0^\circ$
  - Center of gravity radial trim offset $\Delta z_{\text{cg}} = 0.050\text{ m}$ ($50\text{ mm}$)
- **Assumptions**: Continuum hypersonic flow; negligible boundary layer skin friction relative to wave drag; shadowing on leeward panels ($C_p = 0$).
- **Validation**:
  - Trim angle of attack $\alpha_{\text{trim}} = 18.5^\circ$ ($C_m = 0$).
  - Trim lift-to-drag ratio $(L/D)_{\text{trim}} = 0.284$.
  - Longitudinal stability margin $\frac{dC_m}{d\alpha} = -0.041\text{ rad}^{-1} < 0$ (statically stable).

---

### 3. Aerothermodynamics & Thermal Protection System
- **Model ID**: `THERM-01`
- **Governing Equations**:
  Stagnation point convective heat flux (Sutton-Graves):
  $$q_{\text{conv}} = k_{\text{sg}} \sqrt{\frac{\rho}{R_n}} v_\infty^3, \quad k_{\text{sg}} = 1.7415 \times 10^{-4}\text{ W}\cdot\text{s}^3/(\text{m}^3\cdot\text{kg}^{0.5})$$
  Shock layer radiative heat flux (Tauber-Sutton correlation for lunar return):
  $$q_{\text{rad}} = 4.736 \times 10^4 R_n^{0.6} \rho^{1.2} \left( \frac{v_\infty}{10000} \right)^{8.5} \quad [\text{W/m}^2]$$
  1D Transient nonlinear thermal diffusion through Avcoat:
  $$\rho(T) C_p(T) \frac{\partial T}{\partial t} = \frac{\partial}{\partial x} \left( k(T) \frac{\partial T}{\partial x} \right)$$
  Surface boundary condition ($x = 0$):
  $$-k \left.\frac{\partial T}{\partial x}\right|_{x=0} = q_{\text{conv}} + q_{\text{rad}} - \epsilon \sigma T_{\text{surf}}^4 - \dot{m}_{\text{abl}} h_{\text{abl}}$$
  Structural bondline boundary condition ($x = L$):
  $$-k \left.\frac{\partial T}{\partial x}\right|_{x=L} = 0 \quad (\text{Adiabatic backface})$$
- **Units**: Heat flux in $\text{W/cm}^2$; thermal conductivity in $\text{W}/(\text{m}\cdot\text{K})$; density in $\text{kg/m}^3$; specific heat in $\text{J}/(\text{kg}\cdot\text{K})$.
- **Inputs & Sourced Parameters**:
  - Nominal Avcoat thickness $L = 0.045\text{ m}$ ($45\text{ mm}$)
  - Avcoat virgin density $\rho = 512\text{ kg/m}^3$
  - Thermal conductivity $k = 0.16\text{ W}/(\text{m}\cdot\text{K})$
  - Specific heat $C_p = 1450\text{ J}/(\text{kg}\cdot\text{K})$
  - Surface emissivity $\epsilon = 0.85$
  - Stefan-Boltzmann constant $\sigma = 5.67037 \times 10^{-8}\text{ W}/(\text{m}^2\cdot\text{K}^4)$
  - Effective heat of ablation $h_{\text{abl}} = 8.5 \times 10^6\text{ J/kg}$
- **Assumptions**: 1D heat flow normal to heat shield; uniform char layer; constant thermal properties through virgin layer.
- **Validation**:
  - Peak lunar entry convective flux: $132.4\text{ W/cm}^2$ (within Avcoat limit $< 250\text{ W/cm}^2$).
  - Maximum bondline temperature: $171.2^\circ\text{C}$ (within structural Al-Li limit $< 250^\circ\text{C}$).

---

### 4. Structural Mechanics & Pressure Vessel Integrity
- **Model ID**: `STRUCT-01`
- **Governing Equations**:
  Membrane stresses under internal differential pressure:
  $$\sigma_{\text{hoop}} = \frac{p \cdot R}{t_{\text{eff}}}, \quad \sigma_{\text{long}} = \frac{p \cdot R}{2 t_{\text{eff}}}$$
  Bending and axial compressive stress under launch boost:
  $$\sigma_{\text{axial}} = -\frac{m_{\text{cm}} n_x g_0}{2\pi R t_{\text{eff}}}, \quad \sigma_{\text{bending}} = \frac{M_{\text{bending}} R}{\pi R^3 t_{\text{eff}}}$$
  Von Mises equivalent yield stress:
  $$\sigma_{\text{vm}} = \sqrt{\sigma_{\text{hoop}}^2 - \sigma_{\text{hoop}}\sigma_{\text{long}} + \sigma_{\text{long}}^2}$$
  Margin of Safety per NASA-STD-5001:
  $$\text{MS}_{\text{yield}} = \frac{\sigma_{\text{yield}}}{\text{FS}_{\text{yield}} \cdot \sigma_{\text{vm}}} - 1, \quad \text{MS}_{\text{ult}} = \frac{\sigma_{\text{ult}}}{\text{FS}_{\text{ult}} \cdot \sigma_{\text{vm}}} - 1$$
  Critical shell buckling stress (NASA SP-8007):
  $$\sigma_{\text{cr}} = 0.605 \gamma_k E \frac{t_{\text{eff}}}{R}, \quad \gamma_k = 0.40 \quad (\text{Knockdown factor})$$
- **Units**: Stresses and pressures in Pascals ($\text{Pa}$); dimensions in meters ($\text{m}$).
- **Material Baseline**: Aluminum-Lithium 2195-T8:
  - Young's modulus $E = 76.0\text{ GPa}$, Poisson's ratio $\nu = 0.33$, density $\rho = 2710\text{ kg/m}^3$
  - Yield strength $\sigma_y = 530\text{ MPa}$, Ultimate strength $\sigma_u = 580\text{ MPa}$
  - Factors of safety: $\text{FS}_{\text{yield}} = 1.25, \text{FS}_{\text{ult}} = 1.40$
- **Assumptions**: Equivalent smeared thickness for orthogrid ribs: $t_{\text{eff}} = t_{\text{skin}} + 0.35 t_{\text{rib}} = 5.3\text{ mm}$.
- **Validation**:
  - Cabin pressurization ($101.3\text{ kPa}$ vacuum diff): $\text{MS}_{\text{yield}} = +9.81, \text{MS}_{\text{ult}} = +9.54$.
  - Launch boost ($4.0g$ axial, $1.5g$ lateral): $\text{MS}_{\text{yield}} = +6.42, \text{MS}_{\text{buckling}} = +1.85$.

---

### 5. Propulsion & Mass Depletion
- **Model ID**: `PROP-01`
- **Governing Equations**:
  $$\frac{dm}{dt} = -\frac{T}{I_{sp} g_0}$$
  $$\Delta v = I_{sp} g_0 \ln\left( \frac{m_0}{m_0 - \Delta m} \right)$$
- **Units**: Mass in $\text{kg}$; thrust in Newtons ($\text{N}$); specific impulse in seconds ($\text{s}$).
- **Parameters**:
  - OMS-E Main Engine: $T = 26,700\text{ N}$ ($6,000\text{ lbf}$), $I_{sp} = 316.0\text{ s}$, $\dot{m} = 8.616\text{ kg/s}$.
  - Usable ESM propellant capacity: $8,618.0\text{ kg}$ (MON-3 / MMH hypergolic).
  - Wet mass at TLI: $25,618.0\text{ kg}$.
  - CM dry mass: $9,300.0\text{ kg}$.
- **Validation**:
  - Verified in `test_physics_rigor.py`: Integrated mass depletion matches analytical rocket equation to within $10^{-4}\text{ kg}$ and $10^{-3}\text{ m/s}$.
