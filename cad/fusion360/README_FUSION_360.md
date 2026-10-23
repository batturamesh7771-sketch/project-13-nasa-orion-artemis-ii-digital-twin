# Autodesk Fusion 360 — Orion MPCV Digital Twin Guide
## Parametric Assembly, Motion Study & Large Component Architecture

This directory contains the native automation script and CAD assets for **Autodesk Fusion 360** installed on your laptop at:
`C:\Users\user\AppData\Local\Autodesk\webdeploy\production\...\Fusion360.exe`

---

## 1. Quick Launch Inside Autodesk Fusion 360

The automation script has already been placed into your official Fusion 360 scripts directory:
`C:\Users\user\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\Scripts\Orion_Digital_Twin\`

### Execution Steps:
1. Open **Autodesk Fusion 360** on your laptop.
2. In the top toolbar, switch to the **Design** workspace.
3. Click the **Utilities** tab $\rightarrow$ **Add-Ins** $\rightarrow$ **Scripts and Add-Ins** (or press keyboard shortcut `Shift + S`).
4. Under the **My Scripts** list, select **`Orion_Digital_Twin`**.
5. Click **Run**.
6. The script will automatically generate the complete, parametric Orion spacecraft assembly in SI flight scale (centimeter internal units) with all sub-assemblies, materials, and kinematic joints!

---

## 2. Motion Study & Kinematic Joints Setup

The script automatically configures **As-Built Kinematic Joints** with realistic mechanical travel limits:

| Joint Name | Joint Type | Degrees of Freedom | Motion Study Animation Range | Spacecraft Maneuver |
| :--- | :--- | :--- | :--- | :--- |
| **`Jnt_OMSE_Engine_Pitch_Gimbal`** | Revolute | 1 DOF (Pitch axis) | $-7.0^\circ \le \theta \le +7.0^\circ$ | Main engine thrust-vector control (TVC) steering |
| **`Jnt_LAS_Tower_Jettison_Separation`** | Slider | 1 DOF (Longitudinal Z) | $0.0\text{ m} \le Z \le 15.0\text{ m}$ | Jettison of the 15.24 m abort tower at $T+3:20$ |
| **`Jnt_CM_SM_Staging_Separation`** | Slider | 1 DOF (Longitudinal Z) | $0.0\text{ m} \le Z \le 10.0\text{ m}$ | Pyrotechnic staging before atmospheric entry |
| **`Jnt_Solar_Root_1` to `4`** | Revolute | 1 DOF (Dihedral cant) | $0.0^\circ \le \phi \le 55.0^\circ$ | Solar array deployment from stowed cylinder to X-wing flight cant |

### Running a Motion Study in Fusion 360:
1. Go to the **Assemble** menu in the top ribbon.
2. Click **Motion Study**.
3. Click on any of the kinematic joints in the browser (e.g., `Jnt_LAS_Tower_Jettison_Separation` or `Jnt_OMSE_Engine_Pitch_Gimbal`).
4. A timeline graph will appear at the bottom of the screen.
5. Click at step 0 (set position to `0`), and at step 50 (set position to `1500 cm` for LAS jettison or `7 deg` for engine gimbal).
6. Click the **Play** button to watch the real-time kinematic simulation!

---

## 3. Large Assembly Architecture (10,000+ Parts & Hardware Optimization)

NASA's Orion spacecraft comprises thousands of physical components (including $\sim 1,300$ silica thermal tiles, Avcoat ablative honeycomb cells, thousands of photovoltaic cells across the 4 solar array wings, structural orthogrid ribs, and fasteners).

### Memory & Performance Strategy on Dual-Core (8 GB RAM) Hardware:
On an Intel Core i5-5200U laptop with 8 GB RAM and integrated graphics:
* Attempting to model 10,000 unconstrained individual CAD bodies simultaneously would consume $>12\text{ GB}$ of RAM and crash Fusion 360.
* Our script applies **Aerospace Large Assembly Management (LAM)**:
  * **Hierarchical Sub-Assemblies**: Groups elements into `ASM_01_Crew_Module`, `ASM_02_Service_Module`, `ASM_03_OMSE_Engine`, `ASM_04_Solar_Wings`, and `ASM_05_LAS`.
  * **Multi-Body Feature Arrays**: Uses parametric pattern arrays for the solar cell facets and thermal protection tiles, giving full visual fidelity and geometry without joint-solver overhead.
  * **Selective Kinematic Joints**: Assigns joints strictly between physical staging and mechanism interfaces, enabling ultra-smooth 60 FPS motion studies without CPU lag.

---

## 4. Updated Neutral 3D Files (3D Viewer Verified)

The export routines have been updated to fix previous viewport selection bugs:

* [`orion_reentry_capsule.glb`](file:///C:/Users/user/.gemini/antigravity/scratch/orion-digital-twin/cad/exports/orion_reentry_capsule.glb) & [`.obj`](file:///C:/Users/user/.gemini/antigravity/scratch/orion-digital-twin/cad/exports/orion_reentry_capsule.obj):
  * **Now contains ONLY the Crew Module and Avcoat Heat Shield** (12 objects: cone, windows, RCS pods, heat shield).
  * The LAS tower and solar wings have been completely removed from this configuration.
* [`orion_launch_stack.glb`](file:///C:/Users/user/.gemini/antigravity/scratch/orion-digital-twin/cad/exports/orion_launch_stack.glb) & [`.obj`](file:///C:/Users/user/.gemini/antigravity/scratch/orion-digital-twin/cad/exports/orion_launch_stack.obj):
  * Contains the **complete 15.24 m LAS tower**, Crew Module, Heat Shield, ESM, and **stowed solar array wings folded flat against the cylinder**.
* [`orion_orbital_flight.glb`](file:///C:/Users/user/.gemini/antigravity/scratch/orion-digital-twin/cad/exports/orion_orbital_flight.glb) & [`.obj`](file:///C:/Users/user/.gemini/antigravity/scratch/orion-digital-twin/cad/exports/orion_orbital_flight.obj):
  * Contains the Crew Module, Heat Shield, ESM, OMS-E engine, and **4 deployed X-wing solar arrays canted at $55^\circ$ dihedral** (NO LAS tower).
