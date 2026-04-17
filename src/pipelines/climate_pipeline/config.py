"""Climate pipeline dataset catalog and thresholds."""

from __future__ import annotations

# ── SPEI drought ─────────────────────────────────────────────────────────────

SPEI_COLLECTION = "CSIC/SPEI/2_9"
SPEI_BAND = "SPEI_12_month"
SPEI_TEMPORAL_START = "1990-01-01"
SPEI_TEMPORAL_END = "2025-12-31"
SPEI_CATEGORIES = {
    # Lower SPEI = drier. Thresholds from McKee et al. (1993) adapted for SPEI.
    "extreme_drought": (-float("inf"), -2.0),
    "severe_drought": (-2.0, -1.5),
    "moderate_drought": (-1.5, -1.0),
    "normal": (-1.0, 1.0),
    "wet": (1.0, float("inf")),
}

# ── ERA5 heat stress ─────────────────────────────────────────────────────────

ERA5_MONTHLY = "ECMWF/ERA5_LAND/MONTHLY_AGGR"
ERA5_TEMP_BAND = "temperature_2m_max"
ERA5_TEMP_BASELINE_START = "1991-01-01"
ERA5_TEMP_BASELINE_END = "2020-12-31"
ERA5_TEMP_CURRENT_START = "2023-01-01"
# Days per year above 35C is a common heat-stress proxy for outdoor labor.
HEAT_STRESS_THRESHOLD_K = 308.15  # 35°C in Kelvin

# ── Deltares coastal flood ───────────────────────────────────────────────────

DELTARES_COASTAL = "DELTARES/floods/v2024"
DELTARES_DEPTH_BAND = "inundation_depth"
DELTARES_RETURN_PERIODS = [10, 100, 250, 1000]  # years
DELTARES_SLR_SCENARIOS = ["sealevel_2018", "sealevel_2050"]

# ── WRI Aqueduct (REST) ──────────────────────────────────────────────────────

AQUEDUCT_API_BASE = "https://api.aqueduct-floods.wri.org/v1"

# ── ThinkHazard! (REST) ──────────────────────────────────────────────────────

THINKHAZARD_API_BASE = "https://thinkhazard.org/en/api/hazardcategory"
THINKHAZARD_HAZARD_TYPES = [
    "FL",  # river flood
    "CF",  # coastal flood
    "DG",  # drought
    "EH",  # extreme heat
    "LS",  # landslide
    "TC",  # cyclone
    "WF",  # wildfire
]
THINKHAZARD_LEVEL_ORDER = {"VLO": 0, "LOW": 1, "MED": 2, "HIG": 3}

# ── Output schema tags ───────────────────────────────────────────────────────

HAZARD_TYPES = ("flood", "drought", "heat", "coastal_flood", "landslide", "cyclone", "wildfire")
