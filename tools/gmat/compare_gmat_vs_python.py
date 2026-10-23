"""
Independent Orbital Cross-Validation Tool:
Compares NASA GMAT (R2026a) Output against Python Dormand-Prince 5(4) and Analytical LEO Solution.
"""

import os
import sys
import math
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from simulation.trajectory.adaptive_integrator import DormandPrince45, TwoBodyOrbitalPropagator

LOCAL_REPORT = Path(__file__).resolve().parent / "GMAT_LEO_Benchmark_Output.txt"
GMAT_INSTALL_REPORT = Path(r"E:\NASA\GMAT-R2026a\output\GMAT_LEO_Benchmark_Output.txt")

def find_gmat_report() -> Path:
    if LOCAL_REPORT.exists():
        return LOCAL_REPORT
    if GMAT_INSTALL_REPORT.exists():
        return GMAT_INSTALL_REPORT
    return LOCAL_REPORT

def run_cross_validation():
    # ---------------------------------------------------------
    # 1. Analytical Benchmark Definitions
    # ---------------------------------------------------------
    mu = 398600.4415e9 # [m^3/s^2]
    a = 6778.1363e3    # [m]
    inc = math.radians(28.5)

    v_circ = math.sqrt(mu / a)
    T = 2.0 * math.pi * math.sqrt((a ** 3) / mu)

    # Initial state in EarthMJ2000Eq
    r0 = np.array([a, 0.0, 0.0]) # [m]
    v0 = np.array([0.0, v_circ * math.cos(inc), v_circ * math.sin(inc)]) # [m/s]
    state0 = np.concatenate([r0, v0])
    e0_spec = (np.linalg.norm(v0)**2)/2.0 - mu/np.linalg.norm(r0)

    print("=" * 78)
    print("      NASA GMAT (R2026a) vs. PYTHON DP5(4) vs. ANALYTICAL BENCHMARK       ")
    print("=" * 78)
    print(f"Earth Gravitational Parameter (mu) : {mu:.4e} m^3/s^2 ({mu/1e9:.4f} km^3/s^2)")
    print(f"Orbital Radius (r0 = a)             : {a:.3f} m ({a/1e3:.4f} km)")
    print(f"Circular Velocity (v_circ)          : {v_circ:.7f} m/s ({v_circ/1e3:.7f} km/s)")
    print(f"Analytical Orbital Period (T)       : {T:.6f} s ({T/60.0:.4f} min)")
    print(f"Analytical Initial State r(0) [m]   : [{r0[0]:.3f}, {r0[1]:.3f}, {r0[2]:.3f}]")
    print(f"Analytical Initial State v(0) [m/s] : [{v0[0]:.3f}, {v0[1]:.3f}, {v0[2]:.3f}]")
    print("-" * 78)

    # ---------------------------------------------------------
    # 2. Python Dormand-Prince 5(4) Numerical Integration
    # ---------------------------------------------------------
    prop = TwoBodyOrbitalPropagator(mu=mu)
    integrator = DormandPrince45(rtol=1e-12, atol=1e-14, h_min=1e-6, h_max=60.0)

    res = integrator.integrate(prop.state_derivative, (0.0, T), state0, h_initial=10.0)

    r_py = res["y"][-1][:3]
    v_py = res["y"][-1][3:6]

    dr_py_ana = float(np.linalg.norm(r_py - r0))
    dv_py_ana = float(np.linalg.norm(v_py - v0))
    e_py = float((np.linalg.norm(v_py)**2)/2.0 - mu/np.linalg.norm(r_py))
    de_rel_py = abs(e_py - e0_spec) / abs(e0_spec)

    print(f"[Python DP5(4)] Final r(T) [m]     : [{r_py[0]:.3f}, {r_py[1]:.3f}, {r_py[2]:.3f}]")
    print(f"[Python DP5(4)] Final v(T) [m/s]   : [{v_py[0]:.3f}, {v_py[1]:.3f}, {v_py[2]:.3f}]")
    print(f"[Python DP5(4)] Position Error     : {dr_py_ana:.6e} m ({dr_py_ana*1000.0:.4f} mm)")
    print(f"[Python DP5(4)] Velocity Error     : {dv_py_ana:.6e} m/s")
    print(f"[Python DP5(4)] Energy Rel Error   : {de_rel_py:.6e}")
    print(f"[Python DP5(4)] Accepted Steps     : {res['accepted_steps']} (Rejected: {res['rejected_steps']})")
    print("-" * 78)

    # ---------------------------------------------------------
    # 3. NASA GMAT Output Parsing & Verification
    # ---------------------------------------------------------
    report_path = find_gmat_report()
    if not report_path.exists():
        print("[-] GMAT Report not found at:", report_path)
        print("    Run GMAT with tools/gmat/GMAT_LEO_Benchmark.script first.")
        return False

    print(f"[+] Sourcing Real GMAT Output Report from: {report_path}")

    with open(report_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("%")]

    if len(lines) < 2:
        print("[-] GMAT Report is empty or incomplete.")
        return False

    header = lines[0].split()
    first_record = lines[1].split()
    last_record = lines[-1].split()

    # Columns: ElapsedSecs, X, Y, Z, VX, VY, VZ, SMA, ECC, Energy
    # GMAT outputs in km, km/s, km^2/s^2
    gmat_t_start = float(first_record[0])
    gmat_r_start = np.array([float(first_record[1]), float(first_record[2]), float(first_record[3])]) * 1000.0
    gmat_v_start = np.array([float(first_record[4]), float(first_record[5]), float(first_record[6])]) * 1000.0
    gmat_e_start = float(first_record[9]) * 1e6 # J/kg

    gmat_t_end = float(last_record[0])
    gmat_r_end = np.array([float(last_record[1]), float(last_record[2]), float(last_record[3])]) * 1000.0
    gmat_v_end = np.array([float(last_record[4]), float(last_record[5]), float(last_record[6])]) * 1000.0
    gmat_sma_end = float(last_record[7]) * 1000.0
    gmat_ecc_end = float(last_record[8])
    gmat_e_end = float(last_record[9]) * 1e6 # J/kg

    # Residuals against Analytical Truth
    dr_gmat_ana = float(np.linalg.norm(gmat_r_end - r0))
    dv_gmat_ana = float(np.linalg.norm(gmat_v_end - v0))
    de_rel_gmat = abs(gmat_e_end - gmat_e_start) / abs(gmat_e_start)

    # Cross-Tool Residuals: GMAT vs. Python DP5(4)
    dr_gmat_py = float(np.linalg.norm(gmat_r_end - r_py))
    dv_gmat_py = float(np.linalg.norm(gmat_v_end - v_py))

    print(f"[NASA GMAT] Propagated Duration    : {gmat_t_end:.6f} s (Target: {T:.6f} s)")
    print(f"[NASA GMAT] Steps Output in Report : {len(lines) - 1} records")
    print(f"[NASA GMAT] Final r(T) [m]         : [{gmat_r_end[0]:.3f}, {gmat_r_end[1]:.3f}, {gmat_r_end[2]:.3f}]")
    print(f"[NASA GMAT] Final v(T) [m/s]       : [{gmat_v_end[0]:.3f}, {gmat_v_end[1]:.3f}, {gmat_v_end[2]:.3f}]")
    print(f"[NASA GMAT] Final SMA [m]          : {gmat_sma_end:.3f} (Error: {abs(gmat_sma_end - a)*1000.0:.4f} mm)")
    print(f"[NASA GMAT] Final Eccentricity     : {gmat_ecc_end:.4e} (Near-perfect circular)")
    print(f"[NASA GMAT] vs. Analytical Pos Err : {dr_gmat_ana:.6e} m ({dr_gmat_ana*1000.0:.4f} mm)")
    print(f"[NASA GMAT] vs. Analytical Vel Err : {dv_gmat_ana:.6e} m/s")
    print(f"[NASA GMAT] Energy Rel Error       : {de_rel_gmat:.6e}")
    print("-" * 78)
    print(">>> CROSS-TOOL COMPARISON (GMAT PrinceDormand78 vs. Python DormandPrince54) <<<")
    print(f"Position Residual |r_GMAT - r_Python| : {dr_gmat_py:.6e} m ({dr_gmat_py*1000.0:.4f} mm)")
    print(f"Velocity Residual |v_GMAT - v_Python| : {dv_gmat_py:.6e} m/s")
    print("=" * 78)

    # Acceptance Assertions
    passed = (dr_gmat_ana < 1.0) and (dv_gmat_ana < 1e-3) and (dr_gmat_py < 1.0) and (de_rel_gmat < 1e-6)
    if passed:
        print(">>> VERIFICATION STATUS: PASSED [MATHEMATICAL & CROSS-TOOL CONSISTENCY PROVEN] <<<")
    else:
        print(">>> VERIFICATION STATUS: FAILED [TOLERANCE EXCEEDED] <<<")
    print("=" * 78)
    return passed

if __name__ == "__main__":
    success = run_cross_validation()
    sys.exit(0 if success else 1)
