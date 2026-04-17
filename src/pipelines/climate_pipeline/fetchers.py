"""
Climate-hazard fetchers.

Each function returns a normalized dict:

    {
        "hazard": "drought" | "heat" | "coastal_flood" | "composite",
        "aoi": <geojson-like dict>,
        "score": float,                 # 0..1 normalized risk
        "category": str,                # human-readable tier
        "details": {...},               # hazard-specific fields
        "source": str,
        "pulled_at": ISO8601 str,
    }

GEE-backed fetchers require `ee.Initialize(project=GEE_PROJECT)` to be called
elsewhere (done in gee_pipeline.accessor.init). They will raise if GEE is not
initialized.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from src.pipelines.climate_pipeline import config as cfg
from src.shared.pipeline.aoi import CORRIDOR

logger = logging.getLogger("corridor.climate")


def _default_aoi() -> dict[str, Any]:
    return CORRIDOR.to_geojson()


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_drought_spei(aoi: dict[str, Any] | None = None) -> dict[str, Any]:
    """Mean 12-month SPEI over the AOI for the most recent 12 months."""
    import ee

    geom = ee.Geometry(aoi or _default_aoi())
    end = ee.Date(cfg.SPEI_TEMPORAL_END)
    start = end.advance(-12, "month")
    img = (
        ee.ImageCollection(cfg.SPEI_COLLECTION)
        .select(cfg.SPEI_BAND)
        .filterDate(start, end)
        .mean()
        .clip(geom)
    )
    stats = img.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=25_000,
        maxPixels=1e9,
    ).getInfo()
    spei = stats.get(cfg.SPEI_BAND)
    category = _spei_category(spei)
    return {
        "hazard": "drought",
        "aoi": aoi or _default_aoi(),
        "score": _spei_to_score(spei),
        "category": category,
        "details": {"mean_spei_12mo": spei},
        "source": "CSIC SPEI 2.9 (GEE)",
        "pulled_at": _timestamp(),
    }


def fetch_heat_stress_era5(aoi: dict[str, Any] | None = None) -> dict[str, Any]:
    """Days per year above 35°C (current 3y mean vs 1991-2020 baseline)."""
    import ee

    geom = ee.Geometry(aoi or _default_aoi())
    current = (
        ee.ImageCollection(cfg.ERA5_MONTHLY)
        .select(cfg.ERA5_TEMP_BAND)
        .filterDate(cfg.ERA5_TEMP_CURRENT_START, cfg.ERA5_TEMP_BASELINE_END)
        .map(lambda img: img.gte(cfg.HEAT_STRESS_THRESHOLD_K).rename("hot_day"))
        .sum()
        .clip(geom)
    )
    baseline = (
        ee.ImageCollection(cfg.ERA5_MONTHLY)
        .select(cfg.ERA5_TEMP_BAND)
        .filterDate(cfg.ERA5_TEMP_BASELINE_START, cfg.ERA5_TEMP_BASELINE_END)
        .map(lambda img: img.gte(cfg.HEAT_STRESS_THRESHOLD_K).rename("hot_day"))
        .sum()
        .clip(geom)
    )
    cur_stat = current.reduceRegion(ee.Reducer.mean(), geom, 10_000, maxPixels=1e9).getInfo()
    base_stat = baseline.reduceRegion(ee.Reducer.mean(), geom, 10_000, maxPixels=1e9).getInfo()
    cur = cur_stat.get("hot_day", 0) or 0
    base = base_stat.get("hot_day", 0) or 0
    delta = cur - base
    score = max(0.0, min(1.0, delta / 60.0))  # 60 extra hot days/yr = max risk
    return {
        "hazard": "heat",
        "aoi": aoi or _default_aoi(),
        "score": score,
        "category": _heat_category(score),
        "details": {
            "current_hot_days_per_year": cur,
            "baseline_hot_days_per_year": base,
            "delta_hot_days_per_year": delta,
        },
        "source": "ECMWF ERA5-Land (GEE)",
        "pulled_at": _timestamp(),
    }


def fetch_coastal_flood_deltares(aoi: dict[str, Any] | None = None, rp: int = 100) -> dict[str, Any]:
    """Maximum inundation depth for the specified return period, current SLR."""
    import ee

    if rp not in cfg.DELTARES_RETURN_PERIODS:
        raise ValueError(f"return period {rp} not in {cfg.DELTARES_RETURN_PERIODS}")
    geom = ee.Geometry(aoi or _default_aoi())
    img = (
        ee.ImageCollection(cfg.DELTARES_COASTAL)
        .filter(ee.Filter.eq("return_period", rp))
        .filter(ee.Filter.eq("sea_level", "sealevel_2018"))
        .select(cfg.DELTARES_DEPTH_BAND)
        .mosaic()
        .clip(geom)
    )
    stats = img.reduceRegion(
        reducer=ee.Reducer.max(),
        geometry=geom,
        scale=1_000,
        maxPixels=1e9,
    ).getInfo()
    max_depth = stats.get(cfg.DELTARES_DEPTH_BAND, 0) or 0
    score = max(0.0, min(1.0, max_depth / 5.0))  # 5m depth = max risk
    return {
        "hazard": "coastal_flood",
        "aoi": aoi or _default_aoi(),
        "score": score,
        "category": _depth_category(max_depth),
        "details": {"return_period_years": rp, "max_inundation_m": max_depth},
        "source": f"Deltares Global Flood (RP{rp}, SLR 2018)",
        "pulled_at": _timestamp(),
    }


def fetch_composite_thinkhazard(country_iso: str) -> dict[str, Any]:
    """Per-country multi-hazard ranking from ThinkHazard!.

    country_iso is the ISO-3 code (e.g. 'CIV', 'GHA', 'TGO', 'BEN', 'NGA').
    Returns ordered hazard tiers for all supported hazard types.
    """
    url = f"{cfg.THINKHAZARD_API_BASE}/{country_iso}"
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()
    hazards = {}
    for entry in payload:
        code = entry.get("hazardtype", {}).get("mnemonic")
        level = entry.get("hazardlevel", {}).get("mnemonic", "VLO")
        if code in cfg.THINKHAZARD_HAZARD_TYPES:
            hazards[code] = {
                "level": level,
                "ordinal": cfg.THINKHAZARD_LEVEL_ORDER.get(level, 0),
            }
    score = sum(h["ordinal"] for h in hazards.values()) / (3.0 * len(cfg.THINKHAZARD_HAZARD_TYPES))
    return {
        "hazard": "composite",
        "aoi": {"type": "Country", "iso3": country_iso},
        "score": round(score, 3),
        "category": _composite_category(score),
        "details": {"hazards": hazards},
        "source": "GFDRR ThinkHazard!",
        "pulled_at": _timestamp(),
    }


# ── Classifiers ──────────────────────────────────────────────────────────────

def _spei_category(spei: float | None) -> str:
    if spei is None:
        return "unknown"
    for name, (lo, hi) in cfg.SPEI_CATEGORIES.items():
        if lo <= spei < hi:
            return name
    return "unknown"


def _spei_to_score(spei: float | None) -> float:
    if spei is None:
        return 0.0
    # SPEI -2.5 → 1.0 risk;  SPEI +0 → 0 risk
    return max(0.0, min(1.0, -spei / 2.5))


def _heat_category(score: float) -> str:
    if score >= 0.75:
        return "critical"
    if score >= 0.5:
        return "high"
    if score >= 0.25:
        return "moderate"
    return "low"


def _depth_category(depth_m: float) -> str:
    if depth_m >= 3:
        return "critical"
    if depth_m >= 1:
        return "high"
    if depth_m >= 0.3:
        return "moderate"
    if depth_m > 0:
        return "low"
    return "none"


def _composite_category(score: float) -> str:
    if score >= 0.66:
        return "high"
    if score >= 0.33:
        return "medium"
    return "low"
