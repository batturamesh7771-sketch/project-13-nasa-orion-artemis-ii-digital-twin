"""
Aerothermal Heating and 1D Ablative Thermal Conduction Solver for NASA Orion MPCV.
Calculates stagnation convective (Sutton-Graves) and radiative heat fluxes during
lunar skip re-entry, and solves 1D nonlinear transient heat conduction through
the Avcoat Thermal Protection System (TPS) and structural bondline.

Physical Models:
    1. Sutton-Graves Convective Heating:
       q_conv = k_sg * sqrt(rho / R_nose) * V_inf^3  [W/m^2]
       k_sg = 1.7415e-4 [W/(m^2 * (kg/m^3)^0.5 * (m/s)^3)]
       R_nose = 6.000 m (Orion spherical heat shield radius)
       
    2. Tauber-Sutton Radiative Shock-Layer Heating:
       q_rad = C_rad * R_nose^a * rho^b * f(V_inf)
       
    3. 1D Transient Nonlinear Conduction & Surface Energy Balance:
       rho * Cp * dT/dt = d/dx (k * dT/dx)
       Surface BC: -k * dT/dx = q_aero - eps * sigma * T_surf^4 - m_dot_abl * h_abl
       Bondline BC: -k * dT/dx = 0 (Adiabatic structural backface)
"""

import numpy as np
from typing import Dict, List, Tuple

class OrionAerothermalSolver:
    def __init__(self,
                 heat_shield_thickness_m: float = 0.045,  # 45 mm nominal Avcoat thickness
                 nose_radius_m: float = 6.000,
                 avcoat_density_kg_m3: float = 512.0,    # Virgin Avcoat density
                 avcoat_cp_J_kg_K: float = 1450.0,
                 avcoat_k_W_m_K: float = 0.16,           # Low thermal conductivity
                 emissivity: float = 0.85,
                 ablation_temp_K: float = 2100.0,        # Onset of active Avcoat ablation
                 heat_of_ablation_J_kg: float = 8.5e6):  # Effective heat of ablation
        
        self.L = heat_shield_thickness_m
        self.R_nose = nose_radius_m
        self.rho_tps = avcoat_density_kg_m3
        self.cp_tps = avcoat_cp_J_kg_K
        self.k_tps = avcoat_k_W_m_K
        self.emissivity = emissivity
        self.T_abl = ablation_temp_K
        self.h_abl = heat_of_ablation_J_kg
        
        self.sigma = 5.670374419e-8  # Stefan-Boltzmann constant [W/(m^2 * K^4)]
        self.k_sg = 1.7415e-4        # Sutton-Graves constant for Earth air

    def compute_stagnation_heat_flux(self, 
                                     velocity_m_s: float, 
                                     density_kg_m3: float) -> Dict[str, float]:
        """
        Compute convective and radiative heat flux at stagnation point.
        Returns heat fluxes in W/cm^2 (standard aerospace TPS unit).
        """
        # Convective heating (Sutton-Graves)
        if velocity_m_s <= 0 or density_kg_m3 <= 0:
            return {"q_conv_W_cm2": 0.0, "q_rad_W_cm2": 0.0, "q_total_W_cm2": 0.0}
            
        q_conv_W_m2 = self.k_sg * np.sqrt(density_kg_m3 / self.R_nose) * (velocity_m_s ** 3)
        q_conv_W_cm2 = q_conv_W_m2 / 10000.0 # Convert W/m^2 -> W/cm^2
        
        # Radiative heating (shock-layer equilibrium radiation for high velocities > 8.5 km/s)
        if velocity_m_s > 8500.0:
            v_scaled = velocity_m_s / 10000.0
            # Tauber-Sutton correlation scaled for Earth lunar return shock layer
            q_rad_W_cm2 = 4.736 * (self.R_nose ** 0.6) * (density_kg_m3 ** 1.2) * (v_scaled ** 8.5)
        else:
            q_rad_W_cm2 = 0.0
            
        q_total_W_cm2 = q_conv_W_cm2 + q_rad_W_cm2
        
        # Radiation equilibrium temperature (if no conduction or ablation)
        # q_total = eps * sigma * T_eq^4 -> T_eq = (q_total / (eps * sigma))^(1/4)
        q_total_W_m2 = q_total_W_cm2 * 10000.0
        T_eq_K = (q_total_W_m2 / (self.emissivity * self.sigma)) ** 0.25 if q_total_W_m2 > 0 else 300.0
        
        return {
            "q_conv_W_cm2": float(q_conv_W_cm2),
            "q_rad_W_cm2": float(q_rad_W_cm2),
            "q_total_W_cm2": float(q_total_W_cm2),
            "T_radiation_equilibrium_C": float(T_eq_K - 273.15)
        }

    def solve_1d_conduction(self, 
                            time_profile_sec: np.ndarray,
                            heat_flux_W_cm2: np.ndarray,
                            n_nodes: int = 40,
                            T_initial_C: float = 20.0) -> Dict[str, np.ndarray]:
        """
        Solve 1D transient heat conduction through Avcoat heat shield thickness:
        rho * Cp * dT/dt = k * d2T/dx2
        BC at x = 0 (outer surface): q_in - eps*sigma*T^4 = -k * dT/dx
        BC at x = L (bondline to composite/aluminum structure): dT/dx = 0 (adiabatic)
        """
        dx = self.L / (n_nodes - 1)
        dt = np.min(np.diff(time_profile_sec))
        
        # Numerical stability limit (CFL for diffusion): dt <= 0.5 * dx^2 / alpha
        alpha = self.k_tps / (self.rho_tps * self.cp_tps)
        dt_cfl = 0.45 * (dx ** 2) / alpha
        sub_steps = int(np.ceil(dt / dt_cfl))
        dt_sub = dt / sub_steps
        
        T_nodes = np.full(n_nodes, T_initial_C + 273.15) # in Kelvin
        
        n_times = len(time_profile_sec)
        T_surface_history = np.zeros(n_times)
        T_bondline_history = np.zeros(n_times)
        surface_recession_mm = 0.0
        
        total_recession_history = np.zeros(n_times)
        
        for step in range(n_times):
            q_in_W_m2 = heat_flux_W_cm2[step] * 10000.0
            
            for _ in range(sub_steps):
                T_new = T_nodes.copy()
                
                # Interior nodes (central difference)
                for j in range(1, n_nodes - 1):
                    d2T_dx2 = (T_nodes[j+1] - 2.0 * T_nodes[j] + T_nodes[j-1]) / (dx ** 2)
                    T_new[j] = T_nodes[j] + alpha * d2T_dx2 * dt_sub
                    
                # Surface node (x = 0):
                # Energy balance: rho * cp * (dx/2) * dT/dt = q_in - eps*sigma*T_surf^4 - k * (T_surf - T_1)/dx - q_abl
                q_rad_out = self.emissivity * self.sigma * (T_nodes[0] ** 4)
                q_cond_in = - self.k_tps * (T_nodes[0] - T_nodes[1]) / dx
                q_net = q_in_W_m2 - q_rad_out + q_cond_in
                
                # Check for active ablation
                if T_nodes[0] >= self.T_abl and q_net > 0:
                    # Excess energy causes mass loss (recession)
                    m_dot_abl = q_net / self.h_abl
                    surface_recession_mm += (m_dot_abl / self.rho_tps) * dt_sub * 1000.0
                    dT_surf = 0.0
                else:
                    dT_surf = (q_net / (self.rho_tps * self.cp_tps * (0.5 * dx))) * dt_sub
                    
                T_new[0] = max(200.0, T_nodes[0] + dT_surf)
                
                # Backface bondline node (x = L): adiabatic BC (dT/dx = 0 -> T_ghost = T_n-2)
                d2T_dx2_back = 2.0 * (T_nodes[-2] - T_nodes[-1]) / (dx ** 2)
                T_new[-1] = T_nodes[-1] + alpha * d2T_dx2_back * dt_sub
                
                T_nodes = T_new
                
            T_surface_history[step] = T_nodes[0] - 273.15 # [C]
            T_bondline_history[step] = T_nodes[-1] - 273.15 # [C]
            total_recession_history[step] = surface_recession_mm
            
        return {
            "time_sec": time_profile_sec,
            "T_surface_C": T_surface_history,
            "T_bondline_C": T_bondline_history,
            "surface_recession_mm": total_recession_history,
            "max_surface_temp_C": float(np.max(T_surface_history)),
            "max_bondline_temp_C": float(np.max(T_bondline_history)),
            "total_recession_mm": float(surface_recession_mm),
            "bondline_safe": bool(np.max(T_bondline_history) < 250.0) # 250 C limit
        }

if __name__ == "__main__":
    solver = OrionAerothermalSolver()
    
    # Test stagnation heat flux at peak entry (Mach 32, V = 11 km/s, alt = 60 km -> rho ~ 0.0003 kg/m^3)
    v_peak = 11050.0 # m/s
    rho_peak = 0.00032 # kg/m^3
    flux = solver.compute_stagnation_heat_flux(v_peak, rho_peak)
    
    print("=" * 60)
    print("   ORION AEROTHERMAL STAGNATION & ABLATION RESULTS    ")
    print("=" * 60)
    print(f"Peak Entry Velocity    : {v_peak:.1f} m/s")
    print(f"Convective Heat Flux   : {flux['q_conv_W_cm2']:.2f} W/cm^2")
    print(f"Radiative Heat Flux    : {flux['q_rad_W_cm2']:.2f} W/cm^2")
    print(f"Total Stagnation Flux  : {flux['q_total_W_cm2']:.2f} W/cm^2")
    print(f"Radiation Equil Temp   : {flux['T_radiation_equilibrium_C']:.1f} deg C")
    
    # Synthetic re-entry pulse: 1200 seconds skip profile
    t = np.linspace(0, 1200, 241)
    # Bell-shaped heating pulses for skip profile
    pulse1 = 120.0 * np.exp(-((t - 150) / 60.0)**2)
    pulse2 = 85.0 * np.exp(-((t - 750) / 100.0)**2)
    q_profile = pulse1 + pulse2
    
    conduction = solver.solve_1d_conduction(t, q_profile)
    print("-" * 60)
    print(f"Avcoat Max Surface Temp: {conduction['max_surface_temp_C']:.1f} deg C (Limit ~2800 deg C)")
    print(f"Peak Bondline Temp     : {conduction['max_bondline_temp_C']:.1f} deg C (Limit < 250 deg C)")
    print(f"Avcoat Surface Recession: {conduction['total_recession_mm']:.2f} mm")
    print(f"Bondline Structural Status: {'PASSED [SAFE]' if conduction['bondline_safe'] else 'FAILED [OVERTEMP]'}")
    print("=" * 60)
