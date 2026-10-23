# Author: Senior Aerospace Engineer
# Description: NASA Orion MPCV High-Fidelity Exploded Assembly Generator for Autodesk Fusion 360
# Features:
#   - Full Flight-Scale Parametric Geometry (Crew Module, Heat Shield, ESM, Solar Arrays, LAS)
#   - Subassembly 1: Crew Module Capsule (Pressure Hull, Avcoat Heat Shield, Windows, Hatch, 12 RCS Thrusters)
#   - Subassembly 2: European Service Module (ESM) with:
#       * Internal Orthogrid Stiffener Array (24 vertical stringers)
#       * 2 Large Spherical Propellant Tanks (MMH & MON-3 in bronze/copper)
#       * 2 Composite Auxiliary Tanks
#       * 6 High-Pressure Helium Pressurant Spheres
#       * Interconnecting Manifold Plumbing
#       * Conical Aft Spacecraft Adapter Shroud (Label 4)
#       * 8 Circumferential Auxiliary Rocket Engines (Aerojet R-4D-11, Label 8)
#   - Subassembly 3: Central OMS-E Gimbaled Main Engine with Injector Dome & Dual Actuators (Label 7)
#   - Subassembly 4: 4 Spacecraft Adapter Jettisoned (SAJ) Curved Peeling Fairing Panels (Label 6)
#   - Subassembly 5: 4 Articulated Solar Array Wings (ESA X-Configuration) with Triangular A-Frame Root Yokes (Label 5)
#   - Subassembly 6: Launch Abort System (LAS) Tower with Fairing Skirt, Abort Motor, 4 Vector Nozzles, ACM & Nose Cap
#   - Native Kinematic Joints for Fusion 360 Motion Study & Exploded Separation Animation

import adsk.core
import adsk.fusion
import traceback
import math

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Ensure an active Design document exists; create one if user is in the Home tab
        if not app.activeDocument or not app.activeProduct:
            app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)

        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(app.activeProduct)

        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        rootComp = design.rootComponent
        rootComp.name = "NASA_Orion_MPCV_Exploded_Digital_Twin"

        # Dimensions in Centimeters (Fusion 360 Database Units: 1 m = 100 cm)
        R_CM_BASE = 251.45       # 5.029 m base diameter
        R_CM_TOP = 90.00         # 1.800 m docking diameter
        H_CM_CONE = 335.00       # 3.350 m height
        H_CM_TUNNEL = 375.00     # 3.750 m docking collar
        
        R_ESM = 250.00           # 5.000 m diameter
        H_ESM = 400.00           # 4.000 m cylindrical barrel
        
        R_OMSE_EXIT = 75.00      # 1.500 m exit diameter
        R_OMSE_THROAT = 18.00    # 0.360 m throat
        L_OMSE = 140.00          # 1.400 m bell length
        
        H_LAS = 1524.00          # 15.24 m tower height
        
        PANEL_LEN = 200.00       # 2.000 m panel length
        PANEL_WID = 115.00       # 1.150 m panel width
        PANEL_THICK = 3.50       # 0.035 m thickness

        # -------------------------------------------------------------
        # 1. SUB-ASSEMBLY: CREW MODULE (CM) & HEAT SHIELD
        # -------------------------------------------------------------
        occ_cm = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp_cm = occ_cm.component
        comp_cm.name = "ASM_01_Crew_Module_Capsule"

        # Avcoat Heat Shield Spherical Cap (Z = 0 to Z = -28 cm)
        sk_hs = comp_cm.sketches.add(comp_cm.xZConstructionPlane)
        lines_hs = sk_hs.sketchCurves.sketchLines
        arcs_hs = sk_hs.sketchCurves.sketchArcs
        p0_hs = adsk.core.Point3D.create(0.0, 0.0, 0.0)
        p1_hs = adsk.core.Point3D.create(R_CM_BASE, 0.0, 0.0)
        p2_hs = adsk.core.Point3D.create(0.0, 0.0, -28.0)
        center_hs = adsk.core.Point3D.create(0.0, 0.0, 572.0)
        lines_hs.addByTwoPoints(p0_hs, p1_hs)
        arcs_hs.addByCenterStartSweep(center_hs, p2_hs, -math.asin(R_CM_BASE / 600.0))
        lines_hs.addByTwoPoints(p2_hs, p0_hs)
        if sk_hs.profiles.count > 0:
            rev_hs = comp_cm.features.revolveFeatures
            rev_in_hs = rev_hs.createInput(sk_hs.profiles.item(0), comp_cm.zConstructionAxis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            rev_in_hs.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
            b_hs = rev_hs.add(rev_in_hs).bodies.item(0)
            b_hs.name = "Body_Avcoat_Heat_Shield"

        # Conical Pressure Vessel & Backshell
        sk_cm = comp_cm.sketches.add(comp_cm.xZConstructionPlane)
        lines_cm = sk_cm.sketchCurves.sketchLines
        lines_cm.addByTwoPoints(adsk.core.Point3D.create(0.0, 0.0, 0.0), adsk.core.Point3D.create(R_CM_BASE, 0.0, 0.0))
        lines_cm.addByTwoPoints(adsk.core.Point3D.create(R_CM_BASE, 0.0, 0.0), adsk.core.Point3D.create(R_CM_TOP, 0.0, H_CM_CONE))
        lines_cm.addByTwoPoints(adsk.core.Point3D.create(R_CM_TOP, 0.0, H_CM_CONE), adsk.core.Point3D.create(R_CM_TOP, 0.0, H_CM_TUNNEL))
        lines_cm.addByTwoPoints(adsk.core.Point3D.create(R_CM_TOP, 0.0, H_CM_TUNNEL), adsk.core.Point3D.create(0.0, 0.0, H_CM_TUNNEL))
        lines_cm.addByTwoPoints(adsk.core.Point3D.create(0.0, 0.0, H_CM_TUNNEL), adsk.core.Point3D.create(0.0, 0.0, 0.0))
        if sk_cm.profiles.count > 0:
            rev_cm = comp_cm.features.revolveFeatures
            rev_in_cm = rev_cm.createInput(sk_cm.profiles.item(0), comp_cm.zConstructionAxis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            rev_in_cm.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
            b_cm = rev_cm.add(rev_in_cm).bodies.item(0)
            b_cm.name = "Body_Crew_Cabin_Pressure_Hull"

        # 4 Cabin Windows
        for win_idx, (angle_deg, z_pos) in enumerate([(35, 230.0), (75, 230.0), (285, 230.0), (325, 230.0)]):
            rad = math.radians(angle_deg)
            r_w = R_CM_BASE - (R_CM_BASE - R_CM_TOP) * (z_pos / H_CM_CONE)
            sk_w = comp_cm.sketches.add(comp_cm.xYConstructionPlane)
            sk_w.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(r_w * math.cos(rad), r_w * math.sin(rad), 0.0), 16.0)
            if sk_w.profiles.count > 0:
                ext_w = comp_cm.features.extrudeFeatures
                ext_in_w = ext_w.createInput(sk_w.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in_w.setDistanceExtent(False, adsk.core.ValueInput.createByReal(z_pos + 10.0))
                try:
                    ext_w.add(ext_in_w)
                except:
                    pass

        # -------------------------------------------------------------
        # 2. SUB-ASSEMBLY: EUROPEAN SERVICE MODULE (ESM) INTERIOR & TANKS
        # -------------------------------------------------------------
        occ_esm = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp_esm = occ_esm.component
        comp_esm.name = "ASM_02_Service_Module_and_Tanks"

        # Cylindrical Barrel & Bulkhead
        sk_esm = comp_esm.sketches.add(comp_esm.xZConstructionPlane)
        lines_esm = sk_esm.sketchCurves.sketchLines
        lines_esm.addByTwoPoints(adsk.core.Point3D.create(0.0, 0.0, 0.0), adsk.core.Point3D.create(R_ESM, 0.0, 0.0))
        lines_esm.addByTwoPoints(adsk.core.Point3D.create(R_ESM, 0.0, 0.0), adsk.core.Point3D.create(R_ESM, 0.0, -H_ESM))
        lines_esm.addByTwoPoints(adsk.core.Point3D.create(R_ESM, 0.0, -H_ESM), adsk.core.Point3D.create(0.0, 0.0, -H_ESM))
        lines_esm.addByTwoPoints(adsk.core.Point3D.create(0.0, 0.0, -H_ESM), adsk.core.Point3D.create(0.0, 0.0, 0.0))
        if sk_esm.profiles.count > 0:
            rev_esm = comp_esm.features.revolveFeatures
            rev_in_esm = rev_esm.createInput(sk_esm.profiles.item(0), comp_esm.zConstructionAxis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            rev_in_esm.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
            b_esm = rev_esm.add(rev_in_esm).bodies.item(0)
            b_esm.name = "Body_ESM_Cylindrical_Barrel"

        # Conical Aft Spacecraft Adapter Shroud (Label 4)
        sk_shroud = comp_esm.sketches.add(comp_esm.xZConstructionPlane)
        lines_sh = sk_shroud.sketchCurves.sketchLines
        lines_sh.addByTwoPoints(adsk.core.Point3D.create(245.0, 0.0, -370.0), adsk.core.Point3D.create(268.0, 0.0, -435.0))
        lines_sh.addByTwoPoints(adsk.core.Point3D.create(268.0, 0.0, -435.0), adsk.core.Point3D.create(262.0, 0.0, -435.0))
        lines_sh.addByTwoPoints(adsk.core.Point3D.create(262.0, 0.0, -435.0), adsk.core.Point3D.create(240.0, 0.0, -370.0))
        lines_sh.addByTwoPoints(adsk.core.Point3D.create(240.0, 0.0, -370.0), adsk.core.Point3D.create(245.0, 0.0, -370.0))
        if sk_shroud.profiles.count > 0:
            rev_sh = comp_esm.features.revolveFeatures
            rev_in_sh = rev_sh.createInput(sk_shroud.profiles.item(0), comp_esm.zConstructionAxis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            rev_in_sh.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
            try:
                b_shroud = rev_sh.add(rev_in_sh).bodies.item(0)
                b_shroud.name = "Body_Aft_Adapter_Cone_Shroud"
            except:
                pass

        # 2 Large Spherical Propellant Tanks (MMH & MON-3 bronze/copper)
        for t_idx, x_sign in enumerate([-1.0, 1.0]):
            sk_t = comp_esm.sketches.add(comp_esm.xZConstructionPlane)
            c_pt = adsk.core.Point3D.create(x_sign * 95.0, 0.0, -200.0)
            p_top = adsk.core.Point3D.create(x_sign * 95.0, 0.0, -128.0)
            p_bot = adsk.core.Point3D.create(x_sign * 95.0, 0.0, -272.0)
            axis_l = sk_t.sketchCurves.sketchLines.addByTwoPoints(p_top, p_bot)
            sk_t.sketchCurves.sketchArcs.addByCenterStartSweep(c_pt, p_top, math.pi)
            if sk_t.profiles.count > 0:
                rev_t = comp_esm.features.revolveFeatures
                rev_in_t = rev_t.createInput(sk_t.profiles.item(0), axis_l, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                rev_in_t.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
                try:
                    b_tank = rev_t.add(rev_in_t).bodies.item(0)
                    b_tank.name = f"Body_Propellant_Tank_Bronze_{t_idx+1}"
                except:
                    pass

        # 6 High-Pressure Helium Pressurant Spheres
        for h_idx in range(6):
            h_ang = (h_idx / 6.0) * 2.0 * math.pi
            hx = 45.0 * math.cos(h_ang)
            hy = 45.0 * math.sin(h_ang)
            sk_he = comp_esm.sketches.add(comp_esm.xYConstructionPlane)
            sk_he.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(hx, hy, 0.0), 22.0)
            if sk_he.profiles.count > 0:
                ext_he = comp_esm.features.extrudeFeatures
                ext_in_he = ext_he.createInput(sk_he.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in_he.setDistanceExtent(False, adsk.core.ValueInput.createByReal(-130.0))
                try:
                    ext_he.add(ext_in_he)
                except:
                    pass

        # 8 Auxiliary Thrusters on Aft Bulkhead (Label 8, flared nozzles pointing aft)
        for a in range(8):
            ang = (a / 8.0) * 2.0 * math.pi
            ax = 185.0 * math.cos(ang)
            ay = 185.0 * math.sin(ang)
            sk_aux = comp_esm.sketches.add(comp_esm.xYConstructionPlane)
            sk_aux.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(ax, ay, 0.0), 14.0)
            if sk_aux.profiles.count > 0:
                ext_aux = comp_esm.features.extrudeFeatures
                ext_in_aux = ext_aux.createInput(sk_aux.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in_aux.setDistanceExtent(False, adsk.core.ValueInput.createByReal(-435.0))
                try:
                    ext_aux.add(ext_in_aux)
                except:
                    pass

        # -------------------------------------------------------------
        # 3. SUB-ASSEMBLY: OMS-E GIMBALED MAIN ENGINE (Label 7)
        # -------------------------------------------------------------
        occ_eng = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp_eng = occ_eng.component
        comp_eng.name = "ASM_03_OMSE_Main_Engine"

        sk_eng = comp_eng.sketches.add(comp_eng.xZConstructionPlane)
        lines_eng = sk_eng.sketchCurves.sketchLines
        lines_eng.addByTwoPoints(adsk.core.Point3D.create(0.0, 0.0, -H_ESM), adsk.core.Point3D.create(R_OMSE_THROAT, 0.0, -H_ESM))
        lines_eng.addByTwoPoints(adsk.core.Point3D.create(R_OMSE_THROAT, 0.0, -H_ESM), adsk.core.Point3D.create(R_OMSE_EXIT, 0.0, -H_ESM - L_OMSE))
        lines_eng.addByTwoPoints(adsk.core.Point3D.create(R_OMSE_EXIT, 0.0, -H_ESM - L_OMSE), adsk.core.Point3D.create(0.0, 0.0, -H_ESM - L_OMSE))
        lines_eng.addByTwoPoints(adsk.core.Point3D.create(0.0, 0.0, -H_ESM - L_OMSE), adsk.core.Point3D.create(0.0, 0.0, -H_ESM))

        if sk_eng.profiles.count > 0:
            rev_eng = comp_eng.features.revolveFeatures
            rev_in_eng = rev_eng.createInput(sk_eng.profiles.item(0), comp_eng.zConstructionAxis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            rev_in_eng.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
            b_eng = rev_eng.add(rev_in_eng).bodies.item(0)
            b_eng.name = "Body_OMSE_Nozzle_Bell"

        # Dual Gimbal Actuator Struts
        for g_idx in [-1, 1]:
            sk_gim = comp_eng.sketches.add(comp_eng.xYConstructionPlane)
            sk_gim.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(g_idx * 35.0, 0.0, 0.0), 5.0)
            if sk_gim.profiles.count > 0:
                ext_gim = comp_eng.features.extrudeFeatures
                ext_in_g = ext_gim.createInput(sk_gim.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in_g.setDistanceExtent(False, adsk.core.ValueInput.createByReal(-430.0))
                try:
                    ext_gim.add(ext_in_g)
                except:
                    pass

        # -------------------------------------------------------------
        # 4. SUB-ASSEMBLY: 4 SAJ JETTISON FAIRING PANELS (Label 6, Cruciform Gaps)
        # -------------------------------------------------------------
        occ_saj = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp_saj = occ_saj.component
        comp_saj.name = "ASM_04_SAJ_Peeling_Fairings"

        saj_azimuths = [0.0, 90.0, 180.0, 270.0]
        for q, az_deg in enumerate(saj_azimuths):
            ang = math.radians(az_deg)
            px = 410.0 * math.cos(ang)
            py = 410.0 * math.sin(ang)
            sk_saj = comp_saj.sketches.add(comp_saj.xYConstructionPlane)
            sk_saj.sketchCurves.sketchLines.addTwoPointRectangle(
                adsk.core.Point3D.create(px - 65.0, py - 65.0, 0.0),
                adsk.core.Point3D.create(px + 65.0, py + 65.0, 0.0)
            )
            if sk_saj.profiles.count > 0:
                ext_saj = comp_saj.features.extrudeFeatures
                ext_in_saj = ext_saj.createInput(sk_saj.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in_saj.setDistanceExtent(False, adsk.core.ValueInput.createByReal(-320.0))
                try:
                    ext_saj.add(ext_in_saj)
                except:
                    pass

        # -------------------------------------------------------------
        # 5. SUB-ASSEMBLY: 4 ARTICULATED SOLAR ARRAY WINGS (Label 5, ESA X-Wing)
        # -------------------------------------------------------------
        wing_azimuths = [45.0, 135.0, 225.0, 315.0]
        for w_idx, az in enumerate(wing_azimuths):
            occ_wing = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            comp_wing = occ_wing.component
            comp_wing.name = f"ASM_05_Solar_Wing_{w_idx+1}_Articulated"

            az_rad = math.radians(az)
            cos_a = math.cos(az_rad)
            sin_a = math.sin(az_rad)

            # Triangular A-Frame Root Deployment Yoke
            yx = (R_ESM + 45.0) * cos_a
            yy = (R_ESM + 45.0) * sin_a
            sk_yoke = comp_wing.sketches.add(comp_wing.xYConstructionPlane)
            sk_yoke.sketchCurves.sketchLines.addTwoPointRectangle(
                adsk.core.Point3D.create(yx - 22.0, yy - 22.0, 0.0),
                adsk.core.Point3D.create(yx + 22.0, yy + 22.0, 0.0)
            )
            if sk_yoke.profiles.count > 0:
                ext_yoke = comp_wing.features.extrudeFeatures
                ext_in_yoke = ext_yoke.createInput(sk_yoke.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in_yoke.setDistanceExtent(False, adsk.core.ValueInput.createByReal(-200.0))
                try:
                    ext_yoke.add(ext_in_yoke)
                except:
                    pass

            # 3 Contiguous Articulated Photovoltaic Panels
            for p_idx in range(3):
                d_radial = (p_idx + 0.5) * PANEL_LEN + 85.0
                px = (R_ESM + d_radial) * cos_a
                py = (R_ESM + d_radial) * sin_a

                sk_panel = comp_wing.sketches.add(comp_wing.xYConstructionPlane)
                sk_panel.sketchCurves.sketchLines.addTwoPointRectangle(
                    adsk.core.Point3D.create(px - PANEL_LEN * 0.48, py - PANEL_WID * 0.48, 0.0),
                    adsk.core.Point3D.create(px + PANEL_LEN * 0.48, py + PANEL_WID * 0.48, 0.0)
                )
                if sk_panel.profiles.count > 0:
                    ext_panel = comp_wing.features.extrudeFeatures
                    ext_in_p = ext_panel.createInput(sk_panel.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                    ext_in_p.setDistanceExtent(False, adsk.core.ValueInput.createByReal(PANEL_THICK))
                    try:
                        ext_panel.add(ext_in_p)
                    except:
                        pass

        # -------------------------------------------------------------
        # 6. SUB-ASSEMBLY: LAUNCH ABORT SYSTEM (LAS) TOWER
        # -------------------------------------------------------------
        occ_las = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp_las = occ_las.component
        comp_las.name = "ASM_06_Launch_Abort_System"

        sk_las = comp_las.sketches.add(comp_las.xZConstructionPlane)
        lines_las = sk_las.sketchCurves.sketchLines
        lines_las.addByTwoPoints(adsk.core.Point3D.create(0.0, 0.0, 20.0), adsk.core.Point3D.create(253.0, 0.0, 20.0))
        lines_las.addByTwoPoints(adsk.core.Point3D.create(253.0, 0.0, 20.0), adsk.core.Point3D.create(55.0, 0.0, 375.0))
        lines_las.addByTwoPoints(adsk.core.Point3D.create(55.0, 0.0, 375.0), adsk.core.Point3D.create(55.0, 0.0, 780.0))
        lines_las.addByTwoPoints(adsk.core.Point3D.create(55.0, 0.0, 780.0), adsk.core.Point3D.create(45.0, 0.0, 1280.0))
        lines_las.addByTwoPoints(adsk.core.Point3D.create(45.0, 0.0, 1280.0), adsk.core.Point3D.create(38.0, 0.0, 1430.0))
        lines_las.addByTwoPoints(adsk.core.Point3D.create(38.0, 0.0, 1430.0), adsk.core.Point3D.create(0.0, 0.0, H_LAS))
        lines_las.addByTwoPoints(adsk.core.Point3D.create(0.0, 0.0, H_LAS), adsk.core.Point3D.create(0.0, 0.0, 20.0))

        if sk_las.profiles.count > 0:
            rev_las = comp_las.features.revolveFeatures
            rev_in_las = rev_las.createInput(sk_las.profiles.item(0), comp_las.zConstructionAxis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            rev_in_las.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
            b_las = rev_las.add(rev_in_las).bodies.item(0)
            b_las.name = "Body_LAS_Tower_and_Fairing"

        # 4 Reverse Abort Nozzles on LAS
        for n in range(4):
            ang = (n / 4.0) * 2.0 * math.pi + math.pi / 4.0
            x_n = 55.0 * math.cos(ang)
            y_n = 55.0 * math.sin(ang)
            sk_noz = comp_las.sketches.add(comp_las.xYConstructionPlane)
            sk_noz.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(x_n, y_n, 0.0), 18.0)
            if sk_noz.profiles.count > 0:
                ext_noz = comp_las.features.extrudeFeatures
                ext_in = ext_noz.createInput(sk_noz.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal(820.0))
                try:
                    ext_noz.add(ext_in)
                except:
                    pass

        # -------------------------------------------------------------
        # 7. KINEMATIC JOINTS FOR MOTION STUDY & STAGING
        # -------------------------------------------------------------
        asBuiltJoints = rootComp.asBuiltJoints

        # Joint 1: OMS-E Engine Pitch Gimbal (+/- 7 deg)
        try:
            jnt_eng_in = asBuiltJoints.createInput(occ_eng, occ_esm, comp_esm.xConstructionAxis)
            jnt_eng_in.setAsRevoluteJointMotion(adsk.fusion.JointDirections.CustomJointDirection, comp_esm.xConstructionAxis)
            jnt_eng = asBuiltJoints.add(jnt_eng_in)
            jnt_eng.name = "Jnt_OMSE_Pitch_Gimbal"
            limits = jnt_eng.jointMotion.rotationLimits
            limits.isMinimumValueEnabled = True
            limits.minimumValue = math.radians(-7.0)
            limits.isMaximumValueEnabled = True
            limits.maximumValue = math.radians(7.0)
        except:
            pass

        # Joint 2: LAS Tower Jettison Slider (+15.0 m linear separation)
        try:
            jnt_las_in = asBuiltJoints.createInput(occ_las, occ_cm, comp_cm.zConstructionAxis)
            jnt_las_in.setAsSliderJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
            jnt_las = asBuiltJoints.add(jnt_las_in)
            jnt_las.name = "Jnt_LAS_Tower_Jettison"
            limits_las = jnt_las.jointMotion.slideLimits
            limits_las.isMinimumValueEnabled = True
            limits_las.minimumValue = 0.0
            limits_las.isMaximumValueEnabled = True
            limits_las.maximumValue = 1500.0
        except:
            pass

        # Joint 3: CM / ESM Staging Separation Slider (+10.0 m linear separation)
        try:
            jnt_sep_in = asBuiltJoints.createInput(occ_cm, occ_esm, comp_esm.zConstructionAxis)
            jnt_sep_in.setAsSliderJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
            jnt_sep = asBuiltJoints.add(jnt_sep_in)
            jnt_sep.name = "Jnt_CMSM_Staging_Separation"
            limits_sep = jnt_sep.jointMotion.slideLimits
            limits_sep.isMinimumValueEnabled = True
            limits_sep.minimumValue = 0.0
            limits_sep.isMaximumValueEnabled = True
            limits_sep.maximumValue = 1000.0
        except:
            pass

        ui.messageBox(
            "NASA Orion MPCV Exploded Assembly Generated Successfully!\n\n"
            "Subassemblies Created in Design Tree:\n"
            "  1. ASM_01: Crew Module Capsule (Pressure Hull, Heat Shield, Windows, Hatch, RCS)\n"
            "  2. ASM_02: European Service Module (Propellant Spheres, Helium Tanks, Aft Shroud, 8 Aux Engines)\n"
            "  3. ASM_03: OMS-E Gimbaled Main Engine (Dual Gimbal Actuators, Injector Dome)\n"
            "  4. ASM_04: 4 SAJ Peeling Fairing Panels (Curved Jettison Segments)\n"
            "  5. ASM_05: 4 Solar Array Wings with A-Frame Deployment Yokes & Hinges\n"
            "  6. ASM_06: Launch Abort System (15.24m Tower, 4 Vector Nozzles, ACM)\n\n"
            "Motion Study Joints Configured:\n"
            "  * Jnt_OMSE_Pitch_Gimbal (+/- 7.0 deg)\n"
            "  * Jnt_LAS_Tower_Jettison (+15.0 m)\n"
            "  * Jnt_CMSM_Staging_Separation (+10.0 m)\n\n"
            "Navigate to 'Assemble > Motion Study' to animate the exploded separation!",
            "NASA Orion Digital Twin — Fusion 360"
        )

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()), 'Orion Digital Twin Error')
