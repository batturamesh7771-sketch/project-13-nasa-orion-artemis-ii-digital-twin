"""
NASA AE9/AP9 & SPENVIS Van Allen Radiation Environment Model.
Simulates:
  - McIlwain L-shell parameter & Earth magnetic dipole field B
  - AP9 Inner Trapped Proton Belt (>100 MeV) & South Atlantic Anomaly (SAA)
  - AE9 Outer Relativistic Electron Belt (>1 MeV)
  - Deep-Space Galactic Cosmic Rays (GCR) baseline
  - Interactive Solar Particle Event (SPE) drill & Orion aft-bay storm shelter attenuation
  - Real-time crew dose equivalent rate (mSv/hr) and cumulative mission dose (mSv)
"""

import math
from typing import Dict, Any, List, Optional
import numpy as np

RE_KM = 6378.137
B0_GAUSS = 0.312  # Dipole equatorial field at Earth surface (~31,200 nT)


class RadiationModelAE9AP9:
    def __init__(self):
        self.spe_active = False
        self.spe_start_time = 0.0
        self.spe_peak_multiplier = 45.0  # Solar flare proton flux surge multiplier
        self.storm_shelter_active = False  # Crew deployed into aft locker storm shelter

    def inject_solar_flare(self, met_seconds: float, duration_hours: float = 4.0):
        """Trigger an energetic Solar Particle Event (SPE) drill."""
        self.spe_active = True
        self.spe_start_time = float(met_seconds)

    def toggle_storm_shelter(self) -> bool:
        """Toggle crew deployment into Orion aft-bay storm shelter (88% attenuation)."""
        self.storm_shelter_active = not self.storm_shelter_active
        return self.storm_shelter_active

    def calculate_radiation_environment(
        self,
        met_seconds: float,
        alt_km: float,
        lat_deg: float = 28.5,
        lon_deg: float = -80.5
    ) -> Dict[str, Any]:
        """
        Evaluate AE9 electron flux, AP9 proton flux, L-shell, and crew dose rates.
        """
        met = max(0.0, float(met_seconds))
        alt = max(0.0, float(alt_km))
        r = RE_KM + alt

        # 1. Geomagnetic Dipole & McIlwain L-Shell Parameter
        # Approximate geomagnetic latitude with 11.5 deg tilt towards 70 deg W
        mag_lat_rad = math.radians(lat_deg + 11.5 * math.cos(math.radians(lon_deg + 70.0)))
        cos_lam = max(0.01, math.cos(mag_lat_rad))
        l_shell = r / (RE_KM * (cos_lam ** 2))

        # Local Magnetic Field B
        sin_lam = math.sin(mag_lat_rad)
        b_gauss = (B0_GAUSS / (l_shell ** 3)) * (math.sqrt(1.0 + 3.0 * (sin_lam ** 2)) / (cos_lam ** 6))
        b_tesla = b_gauss * 1e-4

        # 2. AP9 Inner Trapped Proton Belt (>100 MeV)
        # Peak around L = 1.4 to 2.2 (approx 2,000 km to 8,000 km alt)
        ap9_proton_flux = 0.0
        if 1.15 <= l_shell <= 2.8:
            ap9_peak = 3.2e5  # protons / (cm^2 * s)
            ap9_proton_flux = ap9_peak * math.exp(-((l_shell - 1.8) ** 2) / (2.0 * (0.28 ** 2)))
            
            # SAA (South Atlantic Anomaly) enhancement if in footprint
            if -45.0 <= lat_deg <= -10.0 and -90.0 <= lon_deg <= -20.0:
                ap9_proton_flux *= 4.5

        # 3. AE9 Outer Relativistic Electron Belt (>1 MeV)
        # Peak around L = 3.5 to 6.0 (approx 15,000 km to 32,000 km alt)
        ae9_electron_flux = 0.0
        if 2.8 <= l_shell <= 7.5:
            ae9_peak = 2.5e7  # electrons / (cm^2 * s)
            ae9_electron_flux = ae9_peak * math.exp(-((l_shell - 4.5) ** 2) / (2.0 * (0.85 ** 2)))

        # 4. Deep Space Galactic Cosmic Rays (GCR)
        # Outside Earth magnetosphere (r > 65,000 km / L > 10), full interplanetary GCR
        gcr_base_mSv_hr = 0.032  # ~0.77 mSv/day (typical solar minimum baseline)
        if alt < 500.0:
            # Low Earth Orbit geomagnetic shielding attenuates GCR
            gcr_dose_rate = gcr_base_mSv_hr * 0.25
        elif alt < 20000.0:
            gcr_dose_rate = gcr_base_mSv_hr * (0.25 + 0.75 * (alt / 20000.0))
        else:
            gcr_dose_rate = gcr_base_mSv_hr

        # 5. Solar Particle Event (SPE) Active Simulation
        spe_dose_rate = 0.0
        spe_active_now = False
        if self.spe_active:
            dt_spe_hr = (met - self.spe_start_time) / 3600.0
            if 0.0 <= dt_spe_hr <= 8.0:
                spe_active_now = True
                # Profile rises over 1 hr, decays over 7 hrs
                shape = (dt_spe_hr / 1.0) * math.exp(1.0 - (dt_spe_hr / 1.0))
                spe_dose_rate = 4.2 * shape * self.spe_peak_multiplier
            else:
                self.spe_active = False

        # Storm shelter attenuation factor: 88% reduction in cabin dose
        shelter_factor = 0.12 if self.storm_shelter_active else 1.0

        # Convert fluxes to dose rate (mSv/hr) through Orion Crew Module 10 g/cm^2 hull
        ap9_dose_rate = (ap9_proton_flux / 1.5e5) * 1.85 * shelter_factor
        ae9_dose_rate = (ae9_electron_flux / 1.2e7) * 0.65 * shelter_factor
        spe_dose_rate = spe_dose_rate * shelter_factor
        total_dose_rate = gcr_dose_rate + ap9_dose_rate + ae9_dose_rate + spe_dose_rate

        # 6. Cumulative Mission Dose (mSv) estimate
        # Artemis II nominal crew exposure: ~18 mSv total over 10 days
        cum_gcr = (met / 3600.0) * gcr_base_mSv_hr
        cum_belts = 2.4 if met > 92000.0 else (met / 92000.0) * 2.4
        cum_total = cum_gcr + cum_belts

        # Threat Level
        threat = "NOMINAL"
        if total_dose_rate >= 1.0:
            threat = "CRITICAL_RED_ALARM"
        elif total_dose_rate >= 0.5:
            threat = "CAUTION_YELLOW"

        return {
            "status": "OPERATIONAL_AE9AP9_SPENVIS",
            "met_seconds": round(met, 1),
            "altitude_km": round(alt, 1),
            "geomagnetic": {
                "mcilwain_l_shell": round(l_shell, 3),
                "mag_field_strength_tesla": round(b_tesla, 8),
                "mag_field_gauss": round(b_gauss, 5),
                "region": "INNER_BELT" if 1.15 <= l_shell <= 2.8 else ("OUTER_BELT" if 2.8 < l_shell <= 7.5 else ("LEO_SHIELDED" if alt < 1000 else "INTERPLANETARY_CISLUNAR"))
            },
            "fluxes": {
                "ap9_proton_flux_p_cm2_s": round(ap9_proton_flux, 1),
                "ae9_electron_flux_e_cm2_s": round(ae9_electron_flux, 1)
            },
            "dose_rates_mSv_hr": {
                "ap9_protons": round(ap9_dose_rate, 4),
                "ae9_electrons": round(ae9_dose_rate, 4),
                "gcr_cosmic_rays": round(gcr_dose_rate, 4),
                "spe_solar_event": round(spe_dose_rate, 4),
                "instantaneous_total": round(total_dose_rate, 3)
            },
            "cumulative_dose_mSv": round(cum_total, 2),
            "threat_status": threat,
            "spe_simulation": {
                "is_flare_active": spe_active_now,
                "storm_shelter_deployed": self.storm_shelter_active,
                "attenuation_pct": 88 if self.storm_shelter_active else 0
            }
        }


# Global Singleton Instance
radiation_sim = RadiationModelAE9AP9()
