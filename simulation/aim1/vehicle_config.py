"""
NASA Space Launch System (SLS) Block 1 & Orion MPCV Vehicle Configuration.
Directly implements parameters from:
  - NASA Artemis II SLS Reference Guide (2026)
  - NASA Artemis II Press Kit (2026)
  - data/aim1_source_registry.json
  - data/aim1_launch_event_reference.json

Truth Classes Enforced:
  - NASA_PUBLISHED_SPEC: Authoritative public dimensions, mass summaries, thrust.
  - NASA_PUBLISHED_EVENT: Official flight checkpoints with stated precision.
  - MODEL_ASSUMPTION: Clearly declared engineering approximations.
  - MODEL_OUTPUT: Dynamically integrated values.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"

class SLSBlock1Config:
    """
    Sourced physical vehicle configuration of SLS Block 1 crewed configuration.
    Dimensions, mass properties, and propulsion specifications.
    """
    # -------------------------------------------------------------------------
    # 1. OVERALL STACK SPECIFICATIONS (NASA_PUBLISHED_SPEC)
    # -------------------------------------------------------------------------
    TOTAL_STACK_HEIGHT_M = 98.27           # 322.4 ft (SLS Reference Guide 2026)
    LIFTOFF_MASS_KG = 2604000.0            # 5.74 million lb / 2,604 metric tonnes
    UNFUELED_MASS_KG = 1588000.0          # 3.5 million lb / 1,588 metric tonnes
    MAX_LIFTOFF_THRUST_N = 39144000.0      # 39,144 kN / 8.8 million lbf
    LAUNCH_THRUST_N = 36787000.0           # 36,787 kN / 8.27 million lbf
    CORE_DIAMETER_M = 8.4                  # 27.6 ft core diameter
    STACK_REF_AREA_M2 = 55.42              # pi * (8.4 / 2)^2

    # Launch site coordinates: KSC LC-39B
    LAUNCH_LAT_DEG = 28.608389             # North
    LAUNCH_LON_DEG = -80.604333            # West (279.395667 deg East)
    LAUNCH_ALT_M = 0.0                     # MSL pad elevation datum

    # -------------------------------------------------------------------------
    # 2. CORE STAGE & 4x RS-25 ENGINES (NASA_PUBLISHED_SPEC & MODEL_ASSUMPTION)
    # -------------------------------------------------------------------------
    RS25_ENGINE_COUNT = 4
    RS25_THRUST_SL_EACH_N = 1859357.0      # 418,000 lbf per engine at sea level
    RS25_THRUST_VAC_EACH_N = 2278822.0     # 512,300 lbf per engine in vacuum (109% power level)
    RS25_ISP_SL_S = 366.0                  # Sea-level specific impulse
    RS25_ISP_VAC_S = 452.3                 # Vacuum specific impulse
    CORE_PROPELLANT_MASS_KG = 987000.0     # 733,000 gal LOX + LH2
    CORE_DRY_MASS_KG = 85270.0             # Core stage inert structure

    # -------------------------------------------------------------------------
    # 3. TWIN FIVE-SEGMENT SOLID ROCKET BOOSTERS (SRBs)
    # -------------------------------------------------------------------------
    SRB_COUNT = 2
    SRB_HEIGHT_M = 53.9                    # 177 ft per booster
    SRB_DIAMETER_M = 3.7                   # 12 ft diameter
    SRB_LIFTOFF_THRUST_EACH_N = 16013590.0 # 3.6 million lbf per booster
    SRB_TOTAL_MASS_EACH_KG = 725700.0      # 1.6 million lb gross per booster
    SRB_PROPELLANT_MASS_EACH_KG = 639500.0 # Polybutadiene acrylonitrile (PBAN)
    SRB_INERT_MASS_EACH_KG = 86200.0       # Casings, nozzles, avionics dropped at sep
    SRB_BURN_TIME_S = 126.0                # Nominal burn duration
    SRB_ISP_SL_S = 242.0
    SRB_ISP_VAC_S = 269.0

    # -------------------------------------------------------------------------
    # 4. LAUNCH ABORT SYSTEM (LAS) & FAIRINGS
    # -------------------------------------------------------------------------
    LAS_JETTISON_MASS_KG = 7500.0          # Abort tower + fairing cover jettison
    LAS_JETTISON_MET_S = 193.0             # Launch-day reported: 193 s (Press kit: 198 s)

    # -------------------------------------------------------------------------
    # 5. UPPER STAGE: INTERIM CRYOGENIC PROPULSION STAGE (ICPS)
    # -------------------------------------------------------------------------
    ICPS_ENGINE_MODEL = "Aerojet Rocketdyne RL10B-2"
    ICPS_THRUST_VAC_N = 110100.0           # 24,750 lbf
    ICPS_ISP_VAC_S = 465.5                 # Extendable carbon-carbon nozzle
    ICPS_PROPELLANT_MASS_KG = 27100.0      # LH2 / LOX
    ICPS_DRY_MASS_KG = 3800.0
    ICPS_TOTAL_WET_MASS_KG = 30900.0

    # -------------------------------------------------------------------------
    # 6. ORION SPACECRAFT (CM-003 + ESM-2)
    # -------------------------------------------------------------------------
    ORION_TOTAL_MASS_AT_TLI_KG = 25618.0   # Stack before TLI burn
    ORION_CM_DRY_MASS_KG = 9300.0          # Crew Module dry mass
    ORION_ESM_DRY_MASS_KG = 7700.0         # European Service Module dry mass
    ORION_ESM_USABLE_PROP_KG = 8618.0      # MON-3 / MMH hypergolic propellant
    ORION_MAIN_ENGINE_THRUST_N = 26700.0   # AJ10-190 OMS-E vacuum thrust
    ORION_MAIN_ENGINE_ISP_S = 316.0        # OMS-E specific impulse

    @classmethod
    def load_source_registry(cls) -> Dict[str, Any]:
        path = DATA_DIR / "aim1_source_registry.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"sources": [], "truth_classes": []}

    @classmethod
    def load_launch_events(cls) -> Dict[str, Any]:
        path = DATA_DIR / "aim1_launch_event_reference.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"ascent_events": [], "tli_reference": {}}

    @classmethod
    def load_asset_manifest(cls) -> Dict[str, Any]:
        path = DATA_DIR / "aim1_asset_manifest.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"assembly_scene_sequence": []}
