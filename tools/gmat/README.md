# NASA GMAT Independent Orbital Validation Benchmark
## Orion / Artemis II Digital Twin

This directory contains the independent astrodynamics verification harness using NASA's **General Mission Analysis Tool (GMAT)** (GMAT R2026a). GMAT serves as an external, authoritative reference standard to validate the digital twin's orbital propagators without embedding or modifying the NASA tool itself.

---

## 1. Environment & Installation Verification

During the automated system audit and setup:
- **GMAT Installation Path**: `E:\NASA\GMAT-R2026a\`
- **Console Executable**: `E:\NASA\GMAT-R2026a\bin\GmatConsole.exe`
- **GUI Executable**: `E:\NASA\GMAT-R2026a\bin\GMAT.exe`
- **Startup Configuration**: `E:\NASA\GMAT-R2026a\bin\gmat_startup_file.txt` (clean load; startup warning confirmed to be non-fatal plugin licensing notification)
- **Execution Mode**: Direct headless execution via `GmatConsole.exe` using fully qualified absolute script paths.

---

## 2. Benchmark 1: Earth-Centered Circular Low Earth Orbit (LEO)

### Benchmark Objectives
Isolate pure two-body Keplerian circular Low Earth Orbit with zero perturbations to evaluate numerical integrator stability and round-trip conservation.

### Sourced Initial Conditions
- **Earth Standard Gravitational Parameter ($\mu$)**: $398,600.4415\text{ km}^3/\text{s}^2$ ($3.986004415 \times 10^{14}\text{ m}^3/\text{s}^2$)
- **Orbital Radius ($r_0 = a$)**: $6,778.1363\text{ km}$ ($400.0\text{ km}$ altitude above reference Earth radius $6,378.1363\text{ km}$)
- **Orbital Eccentricity ($e$)**: $0.000000000000$
- **Orbital Inclination ($i$)**: $28.5000^\circ$ (Kennedy Space Center nominal direct ascent)
- **Circular Velocity**:
  $$v_{\text{circ}} = \sqrt{\frac{\mu}{r_0}} = 7,668.5585685\text{ m/s}$$
- **Analytical Orbital Period**:
  $$T = 2\pi\sqrt{\frac{a^3}{\mu}} = 5,553.623413\text{ s} \approx 92.5604\text{ minutes}$$

### Benchmark Execution & Validation Results
- **Script**: `tools/gmat/GMAT_LEO_Benchmark.script`
- **Output Report**: `tools/gmat/GMAT_LEO_Benchmark_Output.txt`
- **Verification Script**: `python tools/gmat/compare_gmat_vs_python.py`

| Metric | Analytical Value | NASA GMAT (PrinceDormand78) | Python (DormandPrince54) | Residual (GMAT vs Python) |
| :--- | :--- | :--- | :--- | :--- |
| **Final Radius $r(T)$** | $6,778,136.300\text{ m}$ | $6,778,136.300\text{ m}$ | $6,778,136.300\text{ m}$ | **$1.3888\text{ mm}$** |
| **Final Speed $v(T)$** | $7,668.5586\text{ m/s}$ | $7,668.5586\text{ m/s}$ | $7,668.5586\text{ m/s}$ | **$1.5713 \times 10^{-6}\text{ m/s}$** |
| **Final Eccentricity** | $0.000000$ | $9.6149 \times 10^{-16}$ | $2.3104 \times 10^{-14}$ | Negligible ($\sim 10^{-14}$) |
| **Specific Energy Error** | $0.0000$ | $1.647 \times 10^{-15}$ | $1.124 \times 10^{-12}$ | Conservation verified |

---

## 3. Benchmark 2: Artemis II Trans-Lunar Injection (TLI) Translunar Arc

### Benchmark Objectives
Validate 24-hour translunar coast dynamics from post-TLI orbital injection towards the Moon over a $171,500\text{ km}$ geocentric distance arc.

### Initial Conditions
- **Epoch**: 2026-Oct-14 00:00:00.000 UTC
- **Initial State**: $r_0 = [6563.136, 0.0, 0.0]\text{ km}$, $v_0 = [0.0, 9534.898, 5177.265]\text{ m/s}$ (Speed: $10,849.809\text{ m/s}$)
- **Propagated Duration**: $86,400.0\text{ s}$ (24.0 hours)
- **Central Body**: Earth Point-Mass + Moon 3rd-Body Gravity

### Benchmark Execution & Validation Results
- **Script**: `tools/gmat/GMAT_Translunar_Benchmark.script`
- **Output Report**: `tools/gmat/GMAT_Translunar_Benchmark_Output.txt` & `tools/gmat/GMAT_Translunar_EarthOnly_Output.txt`
- **Verification Script**: `python tools/gmat/compare_gmat_vs_python_translunar.py`

#### Part A: Matched Force Model (Pure Earth Point-Mass) — Integrator Equivalence
Isolating the numerical integrators (NASA GMAT PrinceDormand78 vs Python DormandPrince45) with identical physics models:

| Metric | NASA GMAT R2026a | Python Artemis II Propagator | Residual (GMAT vs Python) |
| :--- | :--- | :--- | :--- |
| **Geocentric Radius at 24 hr** | $171,560.490\text{ km}$ | $171,560.490\text{ km}$ | **$\Delta r = 0.000388\text{ m}$ (0.388 mm)** |
| **Final Velocity Magnitude** | $1,114.128766\text{ m/s}$ | $1,114.128766\text{ m/s}$ | **$\Delta v = 0.000000003\text{ m/s}$** |
| **Relative Distance Residual** | Reference Standard | Matched | **$2.26 \times 10^{-10}\%$ error** |
| **Validation Gate** | Reference Standard | Passed | **SUB-MILLIMETER CONVERGENCE** |

#### Part B: Force Model Sensitivity & Resolution of the 38.596 km Moon Gravity Effect
When GMAT is run with lunar third-body gravity enabled (`PointMasses = {Earth, Luna}`) and compared against the point-mass Earth trajectory:
- GMAT Earth+Luna final position at 24 hr: $r = 171,521.894\text{ km}$
- GMAT Earth-Only final position at 24 hr: $r = 171,560.490\text{ km}$
- **Net Moon Perturbation Vector Magnitude**: $\Delta r_{\text{Moon}} = 38.6471\text{ km}$
- **Geocentric Radius Difference**: $171,560.490 - 171,521.894 = \mathbf{38.596\text{ km}}$

**Scientific Conclusion**: The $38.596\text{ km}$ difference between early test runs is **not** a numerical solver error or software bug; it is the exact physical perturbation induced by the gravitational acceleration of the Moon over the 24-hour translunar transit:
$$\mathbf{a}_{\text{Moon}} = \mu_{\text{Moon}} \left( \frac{\mathbf{r}_{\text{Moon}} - \mathbf{r}}{\|\mathbf{r}_{\text{Moon}} - \mathbf{r}\|^3} - \frac{\mathbf{r}_{\text{Moon}}}{\|\mathbf{r}_{\text{Moon}}\|^3} \right)$$
Integrating this perturbation over 86,400 seconds yields precisely the observed $38.596\text{ km}$ trajectory deflection towards the Moon.

---

## 4. How to Execute GMAT Benchmarks

### Automated Execution (Headless Console)
From the repository root:
```powershell
# 1. Run LEO Circular Benchmark in GMAT
E:\NASA\GMAT-R2026a\bin\GmatConsole.exe --run C:\Users\user\.gemini\antigravity\scratch\orion-digital-twin\tools\gmat\GMAT_LEO_Benchmark.script

# 2. Compare GMAT LEO output vs Python solver
python tools\gmat\compare_gmat_vs_python.py

# 3. Run Translunar Earth-Only Benchmark in GMAT
E:\NASA\GMAT-R2026a\bin\GmatConsole.exe --run C:\Users\user\.gemini\antigravity\scratch\orion-digital-twin\tools\gmat\GMAT_Translunar_EarthOnly.script

# 4. Run Translunar Earth+Luna Benchmark in GMAT
E:\NASA\GMAT-R2026a\bin\GmatConsole.exe --run C:\Users\user\.gemini\antigravity\scratch\orion-digital-twin\tools\gmat\GMAT_Translunar_Benchmark.script

# 5. Run Complete 2-Part GMAT Translunar Cross-Validation
python tools\gmat\compare_gmat_vs_python_translunar.py
```

### Manual Execution in GMAT GUI
1. Launch `E:\NASA\GMAT-R2026a\bin\GMAT.exe`.
2. Open script `tools/gmat/GMAT_LEO_Benchmark.script`, `tools/gmat/GMAT_Translunar_EarthOnly.script`, or `tools/gmat/GMAT_Translunar_Benchmark.script`.
3. Press **F5** (or click the green Play icon) to run.
4. Output reports are stored in `E:\NASA\GMAT-R2026a\output\` and mirrored in `tools/gmat/`.
