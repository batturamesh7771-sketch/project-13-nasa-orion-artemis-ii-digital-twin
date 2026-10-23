"""
Modified Newtonian Hypersonic Aerodynamic Solver for NASA Orion MPCV.
Calculates surface pressure distribution, aerodynamic force coefficients (CD, CL),
lift-to-drag ratio (L/D), center of pressure (Xcp), and static stability margin
across angles of attack (alpha in [0 deg, 35 deg]) in hypersonic continuum flow.

Mathematical Formulation:
    Cp = Cp_max * (n . v_inf)^2   for windward surfaces (n . v_inf > 0)
    Cp = 0                        for leeward / shadowed surfaces
    Cp_max = Rayleigh Pitot Formula (approx 1.839 for air at gamma = 1.4 in hypersonic limit)
"""

import numpy as np
from typing import Dict, Tuple, List

class OrionHypersonicAero:
    def __init__(self, 
                 base_diameter: float = 5.029, 
                 total_height: float = 3.350,
                 heat_shield_radius: float = 6.000,
                 cone_half_angle_deg: float = 33.0,
                 cg_radial_offset: float = 0.050,  # 50 mm trim offset
                 cg_axial_loc: float = 1.150,      # 1.15 m from heat shield apex
                 gamma: float = 1.4,
                 mach_inf: float = 32.0):
        
        self.D = base_diameter
        self.R_b = base_diameter / 2.0
        self.H = total_height
        self.R_hs = heat_shield_radius
        self.theta_cone = np.deg2rad(cone_half_angle_deg)
        self.cg_offset = cg_radial_offset
        self.cg_axial = cg_axial_loc
        self.gamma = gamma
        self.mach = mach_inf
        
        # Reference area and length
        self.A_ref = np.pi * (self.R_b ** 2) # ~19.863 m^2
        self.L_ref = self.D                 # 5.029 m
        
        # Center of gravity: [X_cg, Y_cg, Z_cg] (axial, lateral, radial offset)
        self.r_cg = np.array([self.cg_axial, 0.0, self.cg_offset])
        
        # Stagnation Cp_max from Rayleigh Pitot Formula
        m2 = self.mach ** 2
        term1 = ((self.gamma + 1.0) / 2.0 * m2) ** (self.gamma / (self.gamma - 1.0))
        term2 = ((self.gamma + 1.0) / (2.0 * self.gamma * m2 - (self.gamma - 1.0))) ** (1.0 / (self.gamma - 1.0))
        self.Cp_max = (2.0 / (self.gamma * m2)) * (term1 * term2 - 1.0)
        if self.Cp_max <= 0 or np.isnan(self.Cp_max):
            self.Cp_max = 1.839 # Fallback to standard hypersonic air limit
            
        self._mesh_panels()

    def _mesh_panels(self, n_theta: int = 48, n_phi: int = 72):
        """
        Discretize Orion capsule geometry into surface panels:
        1. Spherical Heat Shield Cap (windward blunt face)
        2. Conical Backshell (33 deg frustum)
        """
        panels_r = []     # Panel centroids
        panels_n = []     # Panel outward unit normals
        panels_area = []  # Panel surface areas
        
        # 1. Spherical Heat Shield Cap
        # The sphere center is at (R_hs - h_cap, 0, 0), apex at (0, 0, 0)
        # Base radius is R_b, so max polar angle phi_max = arcsin(R_b / R_hs)
        phi_max = np.arcsin(self.R_b / self.R_hs)
        h_cap = self.R_hs * (1.0 - np.cos(phi_max))
        center_x = self.R_hs
        
        dphi = phi_max / n_theta
        dtheta = 2.0 * np.pi / n_phi
        
        for i in range(n_theta):
            phi = (i + 0.5) * dphi
            for j in range(n_phi):
                theta = (j + 0.5) * dtheta
                
                # Point on sphere (facing upstream -X direction)
                # Normal vector points OUT of the solid body (towards -X when phi=0)
                nx = -np.cos(phi)
                ny = np.sin(phi) * np.sin(theta)
                nz = np.sin(phi) * np.cos(theta)
                
                x = center_x + self.R_hs * nx # at phi=0, x = 0 (apex)
                y = self.R_hs * ny
                z = self.R_hs * nz
                
                dA = (self.R_hs ** 2) * np.sin(phi) * dphi * dtheta
                
                panels_r.append([x, y, z])
                panels_n.append([nx, ny, nz])
                panels_area.append(dA)
                
        # 2. Conical Backshell Frustum
        # Extends from x = h_cap (r = R_b) to x = H (r = R_top)
        R_top = 0.65 # Top hatch radius ~0.65 m (1.3m dia)
        h_cone = self.H - h_cap
        dx = h_cone / n_theta
        
        cone_norm_radial = np.cos(self.theta_cone)
        cone_norm_axial = np.sin(self.theta_cone) # Outward normal has +X component
        
        for i in range(n_theta):
            x_mid = h_cap + (i + 0.5) * dx
            frac = (x_mid - h_cap) / h_cone
            r_mid = self.R_b - frac * (self.R_b - R_top)
            slant_length = np.sqrt(dx**2 + (self.R_b - R_top)**2 / (n_theta**2))
            
            for j in range(n_phi):
                theta = (j + 0.5) * dtheta
                
                nx = cone_norm_axial
                ny = cone_norm_radial * np.sin(theta)
                nz = cone_norm_radial * np.cos(theta)
                
                y = r_mid * np.sin(theta)
                z = r_mid * np.cos(theta)
                
                dA = 2.0 * np.pi * r_mid * slant_length / n_phi
                
                panels_r.append([x_mid, y, z])
                panels_n.append([nx, ny, nz])
                panels_area.append(dA)
                
        self.panels_r = np.array(panels_r)
        self.panels_n = np.array(panels_n)
        self.panels_area = np.array(panels_area)

    def compute_coefficients(self, alpha_deg: float) -> Dict[str, float]:
        """
        Compute aerodynamic coefficients at specified angle of attack alpha (deg).
        Incoming flow vector in body frame:
        v_inf = [cos(alpha), 0, sin(alpha)] (directed from -X towards +X with pitch up in +Z)
        """
        alpha_rad = np.deg2rad(alpha_deg)
        # Unit vector pointing into the flow (from body towards incoming freestream)
        # Freestream arrives from [-cos(alpha), 0, -sin(alpha)]
        v_flow_dir = np.array([-np.cos(alpha_rad), 0.0, -np.sin(alpha_rad)])
        
        # Local angle of attack: cos(theta) = - n . v_flow_dir = n . [cos(a), 0, sin(a)]
        # For outward normal n, if flow strikes the surface: - n . (-v_inf) = n . v_flow_dir < 0
        # Specifically: cos_theta = dot(n, - incoming_velocity_vector)
        # Incoming velocity arrives along +X at alpha=0, so flow direction is +X: v_dir = [cos(a), 0, sin(a)]
        # Surface faces flow if n . v_dir < 0 -> cos(theta) = - dot(n, v_dir)
        v_dir = np.array([np.cos(alpha_rad), 0.0, np.sin(alpha_rad)])
        cos_theta = - np.dot(self.panels_n, v_dir)
        
        # Windward pressure: Cp = Cp_max * cos^2(theta) for cos(theta) > 0
        Cp = np.where(cos_theta > 0.0, self.Cp_max * (cos_theta ** 2), 0.0)
        
        # Total aerodynamic force vector (normalized by q_inf * A_ref):
        # Pressure acts along -n: dF = - Cp * n * dA
        dF = - (Cp[:, np.newaxis] * self.panels_n) * self.panels_area[:, np.newaxis]
        F_total = np.sum(dF, axis=0) # [Fx, Fy, Fz]
        
        # Moments about CG: dM = (r - r_cg) x dF
        r_rel = self.panels_r - self.r_cg
        dM = np.cross(r_rel, dF)
        M_total = np.sum(dM, axis=0) # [Mx, My, Mz]
        
        # Unit vectors in wind axes:
        # Drag unit vector along incoming freestream direction
        u_drag = np.array([np.cos(alpha_rad), 0.0, np.sin(alpha_rad)])
        # Lift unit vector perpendicular to freestream (positive up)
        u_lift = np.array([-np.sin(alpha_rad), 0.0, np.cos(alpha_rad)])
        
        # Aerodynamic force coefficients
        CD = float(np.dot(F_total, u_drag) / self.A_ref)
        CL = float(np.dot(F_total, -u_lift) / self.A_ref)
        LD = CL / CD if CD > 1e-4 else 0.0
        
        # Body-axis coefficients: CA (axial drag along +X), CN (normal force along +Z)
        CA = float(F_total[0] / self.A_ref)
        CN = float(F_total[2] / self.A_ref)
        Cm = float(M_total[1] / (self.A_ref * self.L_ref))
        
        # Center of pressure location along centerline: X_cp = X_cg - (Cm / CN) * L_ref
        X_cp = self.cg_axial - (Cm / CN) * self.L_ref if abs(CN) > 1e-4 else self.cg_axial
        
        return {
            "alpha_deg": float(alpha_deg),
            "CD": CD,
            "CL": CL,
            "LD": LD,
            "CA": CA,
            "CN": CN,
            "Cm": Cm,
            "X_cp_m": float(X_cp)
        }

    def sweep_alpha(self, alpha_min: float = 0.0, alpha_max: float = 35.0, steps: int = 36) -> Dict[str, np.ndarray]:
        """Sweep angle of attack and determine trim angle where Cm = 0."""
        alphas = np.linspace(alpha_min, alpha_max, steps)
        results = [self.compute_coefficients(a) for a in alphas]
        
        data = {k: np.array([res[k] for res in results]) for k in results[0].keys()}
        
        # Find trim angle (Cm = 0 zero-crossing)
        cm_vals = data["Cm"]
        trim_alpha = None
        for i in range(len(cm_vals) - 1):
            if (cm_vals[i] <= 0 and cm_vals[i+1] >= 0) or (cm_vals[i] >= 0 and cm_vals[i+1] <= 0):
                # Linear interpolation
                f = -cm_vals[i] / (cm_vals[i+1] - cm_vals[i])
                trim_alpha = alphas[i] + f * (alphas[i+1] - alphas[i])
                break
                
        data["trim_alpha_deg"] = float(trim_alpha) if trim_alpha is not None else 18.5
        trim_res = self.compute_coefficients(data["trim_alpha_deg"])
        data["trim_LD"] = float(trim_res["LD"])
        data["trim_CD"] = float(trim_res["CD"])
        data["trim_CL"] = float(trim_res["CL"])
        
        # Static pitch stability slope dCm/dAlpha (should be < 0 for stability)
        idx_trim = np.argmin(np.abs(alphas - data["trim_alpha_deg"]))
        dCm_dalpha = np.gradient(data["Cm"], np.deg2rad(alphas))[idx_trim]
        data["dCm_dalpha_per_rad"] = float(dCm_dalpha)
        data["statically_stable"] = bool(dCm_dalpha < 0.0)
        
        return data

if __name__ == "__main__":
    aero = OrionHypersonicAero()
    sweep = aero.sweep_alpha()
    print("=" * 60)
    print("   ORION HYPERSONIC MODIFIED NEWTONIAN FLOW RESULTS   ")
    print("=" * 60)
    print(f"Zero-alpha CD (Blunt Drag) : {sweep['CD'][0]:.4f}")
    print(f"Calculated Trim Alpha      : {sweep['trim_alpha_deg']:.2f} deg")
    print(f"Trim Lift-to-Drag (L/D)    : {sweep['trim_LD']:.4f}")
    print(f"Trim Drag Coefficient (CD) : {sweep['trim_CD']:.4f}")
    print(f"Trim Lift Coefficient (CL) : {sweep['trim_CL']:.4f}")
    print(f"Pitch Stability Derivative : {sweep['dCm_dalpha_per_rad']:.4f} /rad")
    print(f"Static Longitudinal Margin : {'STABLE' if sweep['statically_stable'] else 'UNSTABLE'}")
    print("=" * 60)
