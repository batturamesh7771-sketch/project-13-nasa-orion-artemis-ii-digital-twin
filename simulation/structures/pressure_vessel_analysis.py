"""
Thin-Walled Al-Li Pressure Vessel Structural Solver for NASA Orion MPCV.
Calculates membrane, hoop, and bending stresses under internal pressurization,
launch ascent limit loads (Max-Q / max acceleration), and ocean splashdown impact,
evaluating Von Mises stress and structural Margins of Safety per NASA-STD-5001.

Material: Aluminum-Lithium Alloy 2195-T8
    E = 76.0 GPa, Poisson nu = 0.33, Density = 2710 kg/m^3
    Yield Strength sigma_y = 530 MPa
    Ultimate Strength sigma_u = 580 MPa
    Factors of Safety: FS_yield = 1.25, FS_ult = 1.40
"""

import numpy as np
from typing import Dict, List, Any

class OrionPressureVesselSolver:
    def __init__(self,
                 base_diameter_m: float = 5.029,
                 total_height_m: float = 3.350,
                 skin_thickness_mm: float = 2.50,       # 2.5 mm Al-Li 2195 sheet
                 orthogrid_depth_mm: float = 8.00,      # Orthogrid stiffener rib depth
                 crew_module_mass_kg: float = 9300.0,
                 yield_strength_MPa: float = 530.0,
                 ultimate_strength_MPa: float = 580.0,
                 fs_yield: float = 1.25,
                 fs_ultimate: float = 1.40):
        
        self.D = base_diameter_m
        self.R = base_diameter_m / 2.0  # 2.5145 m
        self.H = total_height_m
        self.t_skin = skin_thickness_mm / 1000.0 # [m]
        self.t_eff = (skin_thickness_mm + 0.35 * orthogrid_depth_mm) / 1000.0 # Effective smeared thickness
        self.mass_cm = crew_module_mass_kg
        
        # Material properties: Al-Li 2195-T8
        self.sigma_yield = yield_strength_MPa * 1e6 # [Pa]
        self.sigma_ult = ultimate_strength_MPa * 1e6 # [Pa]
        self.FS_y = fs_yield
        self.FS_u = fs_ultimate
        self.g0 = 9.80665

    def analyze_internal_pressure(self, 
                                  cabin_pressure_kPa: float = 101.325,
                                  proof_factor: float = 1.5) -> Dict[str, Any]:
        """
        Load Case 1: Internal Cabin Pressurization in Space Vacuum.
        Analyzes cylindrical/conical shell under differential pressure.
        """
        p_delta = cabin_pressure_kPa * 1000.0 # [Pa]
        p_proof = p_delta * proof_factor
        
        # Membrane stresses in thin shell
        # Hoop stress: sigma_h = p * R / t_eff
        sigma_hoop = p_delta * self.R / self.t_eff
        # Longitudinal stress: sigma_l = p * R / (2 * t_eff)
        sigma_long = p_delta * self.R / (2.0 * self.t_eff)
        
        # Von Mises equivalent stress: sigma_vm = sqrt(s_h^2 - s_h*s_l + s_l^2)
        sigma_vm = np.sqrt(sigma_hoop**2 - sigma_hoop*sigma_long + sigma_long**2)
        
        # Margin of Safety: MS = (sigma_allowable / (FS * sigma_actual)) - 1
        ms_yield = (self.sigma_yield / (self.FS_y * sigma_vm)) - 1.0
        ms_ult = (self.sigma_ult / (self.FS_u * sigma_vm)) - 1.0
        
        # Proof pressure evaluation
        sigma_vm_proof = sigma_vm * proof_factor
        ms_proof_yield = (self.sigma_yield / (1.0 * sigma_vm_proof)) - 1.0
        
        return {
            "load_case": "Internal Cabin Pressurization (1.0 atm)",
            "p_delta_kPa": cabin_pressure_kPa,
            "sigma_hoop_MPa": float(sigma_hoop / 1e6),
            "sigma_long_MPa": float(sigma_long / 1e6),
            "sigma_von_mises_MPa": float(sigma_vm / 1e6),
            "sigma_proof_vm_MPa": float(sigma_vm_proof / 1e6),
            "MS_yield": float(ms_yield),
            "MS_ultimate": float(ms_ult),
            "MS_proof_yield": float(ms_proof_yield),
            "status": "PASSED [MARGIN POSITIVE]" if (ms_yield > 0 and ms_ult > 0) else "FAILED [NEGATIVE MARGIN]"
        }

    def analyze_launch_loads(self,
                             axial_accel_g: float = 4.0,
                             lateral_accel_g: float = 1.5,
                             cabin_pressure_kPa: float = 101.325,
                             external_q_kPa: float = 41.5) -> Dict[str, Any]:
        """
        Load Case 2: SLS Launch Ascent Max-Q & Maximum Dynamic Load Case.
        Superposition of axial compression, bending moment, and internal pressure.
        """
        # Internal differential pressure during ascent (external ambient ~ 25 kPa at max-Q)
        p_diff = max(0.0, (cabin_pressure_kPa - 25.0) * 1000.0) # [Pa]
        
        # 1. Axial compressive force from capsule inertia
        F_axial_comp = self.mass_cm * axial_accel_g * self.g0 # [N]
        # Cross-sectional shell area: A_shell = 2 * pi * R * t_eff
        A_shell = 2.0 * np.pi * self.R * self.t_eff
        sigma_axial_comp = - F_axial_comp / A_shell # Compressive [Pa]
        
        # 2. Bending moment at base from lateral acceleration and aero side force
        # Center of mass is at ~ 1.15 m from base
        arm_cg = 1.15 # [m]
        M_bending = (self.mass_cm * lateral_accel_g * self.g0) * arm_cg # [N*m]
        # Area moment of inertia of thin-walled ring: I_xx = pi * R^3 * t_eff
        I_ring = np.pi * (self.R ** 3) * self.t_eff
        sigma_bending_max = (M_bending * self.R) / I_ring # [Pa]
        
        # 3. Pressure contribution
        sigma_long_p = p_diff * self.R / (2.0 * self.t_eff)
        sigma_hoop_p = p_diff * self.R / self.t_eff
        
        # Total longitudinal stresses:
        # Tension side: sigma_long_p + sigma_bending - sigma_axial_comp
        # Compression side: sigma_long_p - sigma_bending - sigma_axial_comp
        sigma_long_tension = sigma_long_p + sigma_bending_max + sigma_axial_comp
        sigma_long_compression = sigma_long_p - sigma_bending_max + sigma_axial_comp
        
        # Von Mises on critical tension side
        sigma_vm_tension = np.sqrt(sigma_hoop_p**2 - sigma_hoop_p*sigma_long_tension + sigma_long_tension**2)
        # Von Mises on critical compression side
        sigma_vm_comp = np.sqrt(sigma_hoop_p**2 - sigma_hoop_p*sigma_long_compression + sigma_long_compression**2)
        sigma_vm_max = max(sigma_vm_tension, sigma_vm_comp)
        
        # Critical Euler / Brazier shell buckling stress for thin cylinder
        # sigma_cr = 0.605 * E * (t / R) * gamma_knockdown
        E_modulus = 76.0e9 # [Pa]
        gamma_knockdown = 0.40 # NASA SP-8007 knockdown factor
        sigma_buckling_crit = 0.605 * E_modulus * (self.t_eff / self.R) * gamma_knockdown
        
        ms_yield = (self.sigma_yield / (self.FS_y * sigma_vm_max)) - 1.0
        ms_ult = (self.sigma_ult / (self.FS_u * sigma_vm_max)) - 1.0
        ms_buckling = (sigma_buckling_crit / (1.40 * abs(sigma_long_compression))) - 1.0
        
        return {
            "load_case": "SLS Launch Ascent Max-Q & Boost (nx=4.0g, ny=1.5g)",
            "axial_load_kN": float(F_axial_comp / 1000.0),
            "bending_moment_kNm": float(M_bending / 1000.0),
            "sigma_axial_comp_MPa": float(sigma_axial_comp / 1e6),
            "sigma_bending_MPa": float(sigma_bending_max / 1e6),
            "sigma_hoop_MPa": float(sigma_hoop_p / 1e6),
            "max_von_mises_MPa": float(sigma_vm_max / 1e6),
            "buckling_crit_stress_MPa": float(sigma_buckling_crit / 1e6),
            "MS_yield": float(ms_yield),
            "MS_ultimate": float(ms_ult),
            "MS_buckling": float(ms_buckling),
            "status": "PASSED [MARGIN POSITIVE]" if (ms_yield > 0 and ms_ult > 0 and ms_buckling > 0) else "FAILED [MARGIN NEGATIVE]"
        }

    def analyze_ocean_splashdown(self,
                                 splashdown_velocity_m_s: float = 8.20,
                                 water_density_kg_m3: float = 1025.0) -> Dict[str, Any]:
        """
        Load Case 3: Pacific Ocean Water Splashdown Hydrodynamic Slamming.
        Impact of spherical heat shield structure with water entry deceleration.
        """
        # Hydrodynamic slamming peak pressure (Wagner / von Karman entry theory)
        # Cp_slam ~ 3.0 to 5.0 for blunt spherical cap entry into ocean
        Cp_slam = 4.2
        q_slam = 0.5 * water_density_kg_m3 * (splashdown_velocity_m_s ** 2)
        p_impact = Cp_slam * q_slam # Hydrodynamic impact pressure [Pa]
        
        # Membrane compressive stress in spherical bottom cap (R_sphere = 6.0 m)
        R_cap = 6.000 # [m]
        # Heat shield carrier structure thickness (Titanium/Al-Li composite sandwich ~ 8 mm)
        t_bulkhead = 0.008 # [m]
        sigma_membrane = p_impact * R_cap / (2.0 * t_bulkhead)
        
        # Peak deceleration of capsule during splashdown
        # F_slam = p_impact * A_projected_wetted -> approx 12-15 g peak decel on water entry
        decel_peak_g = 13.5
        
        ms_yield = (self.sigma_yield / (self.FS_y * sigma_membrane)) - 1.0
        ms_ult = (self.sigma_ult / (self.FS_u * sigma_membrane)) - 1.0
        
        return {
            "load_case": "Pacific Ocean Water Splashdown (8.2 m/s)",
            "impact_velocity_m_s": splashdown_velocity_m_s,
            "peak_impact_pressure_kPa": float(p_impact / 1000.0),
            "peak_slam_deceleration_g": decel_peak_g,
            "bulkhead_stress_MPa": float(sigma_membrane / 1e6),
            "MS_yield": float(ms_yield),
            "MS_ultimate": float(ms_ult),
            "status": "PASSED [MARGIN POSITIVE]" if (ms_yield > 0 and ms_ult > 0) else "FAILED [MARGIN NEGATIVE]"
        }

if __name__ == "__main__":
    solver = OrionPressureVesselSolver()
    c1 = solver.analyze_internal_pressure()
    c2 = solver.analyze_launch_loads()
    c3 = solver.analyze_ocean_splashdown()
    
    print("=" * 65)
    print("   ORION AL-LI 2195 PRESSURE VESSEL STRUCTURAL ANALYSIS   ")
    print("=" * 65)
    for c in [c1, c2, c3]:
        print(f"CASE: {c['load_case']}")
        if "sigma_von_mises_MPa" in c:
            print(f"  Von Mises Stress   : {c['sigma_von_mises_MPa']:.2f} MPa")
        elif "max_von_mises_MPa" in c:
            print(f"  Max Von Mises Stress: {c['max_von_mises_MPa']:.2f} MPa")
        elif "bulkhead_stress_MPa" in c:
            print(f"  Bulkhead Stress    : {c['bulkhead_stress_MPa']:.2f} MPa")
        print(f"  MS (Yield)         : +{c['MS_yield']:.2f}")
        print(f"  MS (Ultimate)      : +{c['MS_ultimate']:.2f}")
        if "MS_buckling" in c:
            print(f"  MS (Shell Buckling): +{c['MS_buckling']:.2f}")
        print(f"  Structural Status  : {c['status']}")
        print("-" * 65)
    print("=" * 65)
