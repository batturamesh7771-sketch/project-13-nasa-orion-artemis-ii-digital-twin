"""
Automated Unit and Integration Test Suite — Phase 4
Lightweight Aerodynamic, Thermal & Structural Solvers for NASA Orion MPCV.
"""

import unittest
import numpy as np
from simulation.aero.modified_newtonian import OrionHypersonicAero
from simulation.thermal.aerothermal_heating import OrionAerothermalSolver
from simulation.structures.pressure_vessel_analysis import OrionPressureVesselSolver
from simulation.entry.entry_corridor_analysis import OrionEntryCorridorAnalyzer

class TestPhase4AeroThermalStructures(unittest.TestCase):
    def setUp(self):
        self.aero_solver = OrionHypersonicAero()
        self.thermal_solver = OrionAerothermalSolver()
        self.struct_solver = OrionPressureVesselSolver()
        self.entry_analyzer = OrionEntryCorridorAnalyzer()

    def test_01_modified_newtonian_aerodynamics(self):
        """Verify hypersonic Modified Newtonian drag, trim L/D, and pitch stability."""
        sweep = self.aero_solver.sweep_alpha(alpha_min=0.0, alpha_max=35.0, steps=36)
        
        # 1. Zero-AoA Blunt Drag Coefficient
        cd0 = sweep["CD"][0]
        self.assertGreater(cd0, 1.40, "Hypersonic blunt drag CD(0) should be > 1.4")
        self.assertLess(cd0, 1.85, "Hypersonic blunt drag CD(0) should not exceed Cp_max limit")
        
        # 2. Trim Angle of Attack (nominal Orion trim AoA ~18 to 20 deg)
        trim_alpha = sweep["trim_alpha_deg"]
        self.assertGreaterEqual(trim_alpha, 15.0, "Trim AoA too small (<15 deg)")
        self.assertLessEqual(trim_alpha, 25.0, "Trim AoA too large (>25 deg)")
        
        # 3. Trim Lift-to-Drag Ratio (NASA Artemis I L/D ~ 0.28 to 0.32)
        trim_ld = sweep["trim_LD"]
        self.assertGreater(trim_ld, 0.25, "Trim L/D ratio too low for skip re-entry control (<0.25)")
        self.assertLess(trim_ld, 0.38, "Trim L/D ratio unrealistically high for blunt capsule (>0.38)")
        
        # 4. Longitudinal Static Stability (dCm/dAlpha < 0)
        self.assertTrue(sweep["statically_stable"], "Capsule is statically unstable in pitch!")
        self.assertLess(sweep["dCm_dalpha_per_rad"], 0.0, "Pitch stability slope dCm/dAlpha must be negative")

    def test_02_aerothermal_heating_and_ablation(self):
        """Verify stagnation heat flux and 1D Avcoat heat conduction through bondline."""
        # Peak re-entry conditions: V = 11,050 m/s, alt ~60 km (rho ~ 0.00032 kg/m^3)
        v_peak = 11050.0
        rho_peak = 0.00032
        flux = self.thermal_solver.compute_stagnation_heat_flux(v_peak, rho_peak)
        
        # Stagnation heat flux checks
        self.assertGreater(flux["q_conv_W_cm2"], 120.0, "Convective flux too low for lunar return")
        self.assertLess(flux["q_conv_W_cm2"], 220.0, "Convective flux exceeded Avcoat TPS limits")
        self.assertGreater(flux["T_radiation_equilibrium_C"], 1800.0, "Equilibrium radiation temp too low")
        self.assertLess(flux["T_radiation_equilibrium_C"], 2800.0, "Equilibrium radiation temp exceeded Avcoat limit")
        
        # 1D Transient Conduction Pulse Test
        t = np.linspace(0, 1200, 121)
        q_pulse = 135.0 * np.exp(-((t - 150) / 75.0)**2) + 90.0 * np.exp(-((t - 750) / 110.0)**2)
        conduction = self.thermal_solver.solve_1d_conduction(t, q_pulse, n_nodes=25)
        
        self.assertTrue(conduction["bondline_safe"], "Bondline exceeded critical structural temperature!")
        self.assertLess(conduction["max_bondline_temp_C"], 250.0, "Inner bondline temperature exceeded 250 deg C")
        self.assertGreater(conduction["max_surface_temp_C"], 400.0, "Surface temperature should reflect heating pulse")

    def test_03_pressure_vessel_structural_margins(self):
        """Verify Al-Li 2195 pressure vessel structural integrity and positive margins of safety."""
        # 1. Internal Cabin Pressurization
        c1 = self.struct_solver.analyze_internal_pressure(cabin_pressure_kPa=101.325)
        self.assertGreater(c1["MS_yield"], 0.0, "Yield margin of safety is negative for cabin pressure!")
        self.assertGreater(c1["MS_ultimate"], 0.0, "Ultimate margin of safety is negative for cabin pressure!")
        self.assertGreater(c1["MS_proof_yield"], 0.0, "Proof pressure test margin is negative!")
        
        # 2. SLS Launch Ascent Loads (Max-Q + 4g boost)
        c2 = self.struct_solver.analyze_launch_loads(axial_accel_g=4.0, lateral_accel_g=1.5)
        self.assertGreater(c2["MS_yield"], 0.0, "Yield margin is negative under launch loads!")
        self.assertGreater(c2["MS_ultimate"], 0.0, "Ultimate margin is negative under launch loads!")
        self.assertGreater(c2["MS_buckling"], 0.0, "Shell buckling margin is negative under launch compression!")
        
        # 3. Ocean Splashdown Slamming Impact
        c3 = self.struct_solver.analyze_ocean_splashdown(splashdown_velocity_m_s=8.20)
        self.assertGreater(c3["MS_yield"], 0.0, "Aft bulkhead yield margin is negative under splashdown slamming!")
        self.assertGreater(c3["MS_ultimate"], 0.0, "Aft bulkhead ultimate margin is negative under splashdown slamming!")

    def test_04_skip_reentry_corridor_and_chutes(self):
        """Verify entry corridor boundaries, G-load limits, and parachute terminal descent."""
        nom = self.entry_analyzer.simulate_entry_trajectory(gamma0_deg=-5.85)
        
        # 1. Splashdown Achievement
        self.assertTrue(nom["splashdown"], "Capsule failed to achieve ocean splashdown!")
        
        # 2. Human G-load Limit (<8.0 g per NASA astronaut limit)
        self.assertLess(nom["max_g_load"], 8.0, "Peak deceleration exceeded NASA astronaut 8.0g limit!")
        self.assertGreater(nom["max_g_load"], 2.5, "Peak deceleration too low for lunar return entry")
        
        # 3. Peak Stagnation Heating
        self.assertLess(nom["max_heat_flux_W_cm2"], 250.0, "Peak heat flux exceeded Avcoat TPS threshold")
        
        # 4. Terminal Parachute Splashdown Speed (<8.5 m/s)
        self.assertLess(nom["terminal_velocity_m_s"], 8.5, "Terminal splashdown velocity exceeded 8.5 m/s limit")
        self.assertGreater(nom["terminal_velocity_m_s"], 6.0, "Terminal splashdown velocity unrealistically low")
        
        # 5. Mission Flight Time (25 to 35 minutes)
        self.assertGreater(nom["flight_time_min"], 25.0, "Skip re-entry too fast (<25 min)")
        self.assertLess(nom["flight_time_min"], 35.0, "Skip re-entry took too long (>35 min)")
        
        # 6. Re-entry Corridor Status
        self.assertEqual(nom["corridor_status"], "NOMINAL_CORRIDOR", "Baseline entry was outside nominal corridor!")

if __name__ == "__main__":
    unittest.main()
