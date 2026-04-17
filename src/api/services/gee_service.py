"""
GEE service — wraps CorridorDataAPI with caching and tile URL generation.
"""

from __future__ import annotations

import logging
from typing import Any

import ee

from src.api.cache import gee_cache, make_cache_key
from src.api.config import CACHE_TTL_SECONDS, CACHE_TTL_STATIC, GEE_PROJECT
from src.pipelines.gee_pipeline.accessor import CorridorDataAPI
from src.pipelines.gee_pipeline.config import VIS_PARAMS, DEFAULT_SCALE, MAX_PIXELS

logger = logging.getLogger("corridor.api.gee_service")

# Lazily initialized
_api: CorridorDataAPI | None = None


def init() -> None:
    """Initialize the GEE service."""
    global _api
    _api = CorridorDataAPI(project=GEE_PROJECT or None)
    logger.info("GEE service initialized")


def get_api() -> CorridorDataAPI:
    """Get the CorridorDataAPI singleton."""
    if _api is None:
        init()
    return _api


def _is_connected() -> bool:
    """Check if GEE is initialized."""
    return _api is not None


# ── Tile URL helpers ─────────────────────────────────────────────────────────

def get_tile_url(image: ee.Image, vis_params: dict) -> str:
    """Convert an ee.Image to a tile URL for Mapbox GL JS."""
    map_id = image.getMapId(vis_params)
    return map_id["tile_fetcher"].url_format


def get_stats(image: ee.Image, band: str | None = None, scale: int = 1000) -> dict[str, Any]:
    """Compute corridor-wide stats for an image."""
    api = get_api()
    return api.zone_stats(image, band=band, scale=scale)


# ── Cached data access ──────────────────────────────────────────────────────

def get_nightlights(year: int, month: int) -> dict[str, Any]:
    """Get nightlights tile URL and stats (cached)."""
    key = make_cache_key("nightlights", year, month)
    cached = gee_cache.get(key)
    if cached:
        return cached

    api = get_api()
    image = api.nightlights(year, month)
    vis = VIS_PARAMS["nightlights"]
    tile_url = get_tile_url(image, vis)

    stats = image.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True),
        geometry=api._aoi,
        scale=1000,
        maxPixels=MAX_PIXELS,
    ).getInfo()

    result = {
        "tile_url": tile_url,
        "vis_params": vis,
        "stats": stats,
        "layer_name": f"Nightlights {year}-{month:02d}",
    }

    gee_cache.set(key, result, ttl=CACHE_TTL_SECONDS)
    return result


def get_nightlights_change(year_start: int, year_end: int) -> dict[str, Any]:
    """Get nightlights change tile URL and stats (cached)."""
    key = make_cache_key("nightlights_change", year_start, year_end)
    cached = gee_cache.get(key)
    if cached:
        return cached

    api = get_api()
    image = api.nightlights_change(year_start, year_end)
    vis = VIS_PARAMS["nightlights_change"]
    tile_url = get_tile_url(image, vis)

    stats = image.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True).combine(ee.Reducer.min(), sharedInputs=True),
        geometry=api._aoi,
        scale=1000,
        maxPixels=MAX_PIXELS,
    ).getInfo()

    country_stats = api.zone_stats_by_country(image, band="radiance_change")

    result = {
        "tile_url": tile_url,
        "vis_params": vis,
        "stats": stats,
        "country_stats": country_stats,
        "layer_name": f"Nightlights Change {year_start}-{year_end}",
    }

    gee_cache.set(key, result, ttl=CACHE_TTL_SECONDS)
    return result


def get_ndvi(year: int, month: int) -> dict[str, Any]:
    """Get NDVI tile URL and stats (cached)."""
    key = make_cache_key("ndvi", year, month)
    cached = gee_cache.get(key)
    if cached:
        return cached

    api = get_api()
    image = api.ndvi(year, month)
    vis = VIS_PARAMS["ndvi"]
    tile_url = get_tile_url(image, vis)

    result = {
        "tile_url": tile_url,
        "vis_params": vis,
        "layer_name": f"NDVI {year}-{month:02d}",
    }

    gee_cache.set(key, result, ttl=CACHE_TTL_SECONDS)
    return result


def get_economic_index(year: int, month: int) -> dict[str, Any]:
    """Get economic activity index tile URL and stats (cached)."""
    key = make_cache_key("economic_index", year, month)
    cached = gee_cache.get(key)
    if cached:
        return cached

    api = get_api()
    image = api.economic_activity_index(year, month)
    vis = VIS_PARAMS["economic_index"]
    tile_url = get_tile_url(image, vis)

    stats = image.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True),
        geometry=api._aoi,
        scale=1000,
        maxPixels=MAX_PIXELS,
    ).getInfo()

    result = {
        "tile_url": tile_url,
        "vis_params": vis,
        "stats": stats,
        "layer_name": f"Economic Activity Index {year}-{month:02d}",
    }

    gee_cache.set(key, result, ttl=CACHE_TTL_SECONDS)
    return result


def get_urban_expansion(year_start: int, year_end: int) -> dict[str, Any]:
    """Get urban expansion tile URL (cached)."""
    key = make_cache_key("urban_expansion", year_start, year_end)
    cached = gee_cache.get(key)
    if cached:
        return cached

    api = get_api()
    image = api.urban_expansion(year_start, year_end)
    vis = VIS_PARAMS["urban_expansion"]
    tile_url = get_tile_url(image, vis)

    result = {
        "tile_url": tile_url,
        "vis_params": vis,
        "layer_name": f"Urban Expansion {year_start}-{year_end}",
    }

    gee_cache.set(key, result, ttl=CACHE_TTL_SECONDS)
    return result


def get_landcover() -> dict[str, Any]:
    """Get WorldCover tile URL and area stats (cached)."""
    key = make_cache_key("landcover")
    cached = gee_cache.get(key)
    if cached:
        return cached

    api = get_api()
    image = api.worldcover()
    vis = VIS_PARAMS["worldcover"]
    tile_url = get_tile_url(image, vis)

    result = {
        "tile_url": tile_url,
        "vis_params": vis,
        "layer_name": "ESA WorldCover 2021",
    }

    gee_cache.set(key, result, ttl=CACHE_TTL_STATIC)
    return result


def get_elevation() -> dict[str, Any]:
    """Get elevation/slope tile URL (cached)."""
    key = make_cache_key("elevation")
    cached = gee_cache.get(key)
    if cached:
        return cached

    api = get_api()
    image = api.elevation()
    vis = VIS_PARAMS["elevation"]
    tile_url = get_tile_url(image.select("elevation"), vis)

    result = {
        "tile_url": tile_url,
        "vis_params": vis,
        "layer_name": "SRTM Elevation",
    }

    gee_cache.set(key, result, ttl=CACHE_TTL_STATIC)
    return result


def get_population(year: int) -> dict[str, Any]:
    """Get population tile URL and total (cached)."""
    key = make_cache_key("population", year)
    cached = gee_cache.get(key)
    if cached:
        return cached

    api = get_api()
    image = api.population(year)
    vis = VIS_PARAMS["population"]
    tile_url = get_tile_url(image, vis)

    stats = image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=api._aoi,
        scale=1000,
        maxPixels=MAX_PIXELS,
    ).getInfo()

    result = {
        "tile_url": tile_url,
        "vis_params": vis,
        "stats": stats,
        "layer_name": f"Population {year}",
    }

    gee_cache.set(key, result, ttl=CACHE_TTL_STATIC)
    return result


def get_forest() -> dict[str, Any]:
    """Get Hansen forest change tile URL (cached)."""
    key = make_cache_key("forest")
    cached = gee_cache.get(key)
    if cached:
        return cached

    api = get_api()
    image = api.hansen_forest()
    vis = VIS_PARAMS["forest_loss"]
    tile_url = get_tile_url(image.select("loss"), vis)

    result = {
        "tile_url": tile_url,
        "vis_params": vis,
        "layer_name": "Hansen Forest Loss",
    }

    gee_cache.set(key, result, ttl=CACHE_TTL_STATIC)
    return result


def get_building_density() -> dict[str, Any]:
    """Get building density tile URL (cached)."""
    key = make_cache_key("building_density")
    cached = gee_cache.get(key)
    if cached:
        return cached

    api = get_api()
    image = api.building_density()
    vis = VIS_PARAMS["building_density"]
    tile_url = get_tile_url(image, vis)

    result = {
        "tile_url": tile_url,
        "vis_params": vis,
        "layer_name": "Building Density",
    }

    gee_cache.set(key, result, ttl=CACHE_TTL_STATIC)
    return result


def get_climate(year: int, month: int) -> dict[str, Any]:
    """Get ERA5 climate tile URL (cached)."""
    key = make_cache_key("climate", year, month)
    cached = gee_cache.get(key)
    if cached:
        return cached

    api = get_api()
    image = api.climate(year, month)
    vis = VIS_PARAMS["temperature"]
    tile_url = get_tile_url(image.select("temperature_c"), vis)

    result = {
        "tile_url": tile_url,
        "vis_params": vis,
        "layer_name": f"Climate {year}-{month:02d}",
    }

    gee_cache.set(key, result, ttl=CACHE_TTL_SECONDS)
    return result


def get_sar(year: int, month: int) -> dict[str, Any]:
    """Get Sentinel-1 SAR tile URL (cached)."""
    key = make_cache_key("sar", year, month)
    cached = gee_cache.get(key)
    if cached:
        return cached

    api = get_api()
    image = api.sentinel1(year, month)
    vis = VIS_PARAMS["sar_vv"]
    tile_url = get_tile_url(image.select("VV"), vis)

    result = {
        "tile_url": tile_url,
        "vis_params": vis,
        "layer_name": f"Sentinel-1 SAR {year}-{month:02d}",
    }

    gee_cache.set(key, result, ttl=CACHE_TTL_SECONDS)
    return result


def get_protected_areas() -> dict[str, Any]:
    """Get WDPA protected areas tile URL (cached, 24h static)."""
    key = make_cache_key("protected_areas")
    cached = gee_cache.get(key)
    if cached:
        return cached

    api = get_api()
    image = api.protected_areas()
    vis = VIS_PARAMS["protected_areas"]
    tile_url = get_tile_url(image, vis)

    # Get vector data for GeoJSON overlay
    try:
        fc = api.protected_areas_vector()
        features = fc.limit(500).getInfo()
        geojson = features
    except Exception:
        geojson = None

    result = {
        "tile_url": tile_url,
        "vis_params": vis,
        "layer_name": "WDPA Protected Areas",
        "geojson": geojson,
    }

    gee_cache.set(key, result, ttl=CACHE_TTL_STATIC)
    return result


def get_healthcare_access() -> dict[str, Any]:
    """Get Oxford/MAP healthcare accessibility tile URL (cached, 24h static)."""
    key = make_cache_key("healthcare_access")
    cached = gee_cache.get(key)
    if cached:
        return cached

    api = get_api()
    image = api.healthcare_accessibility()
    vis = VIS_PARAMS["healthcare_access"]
    tile_url = get_tile_url(image, vis)

    stats = image.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True),
        geometry=api._aoi,
        scale=1000,
        maxPixels=MAX_PIXELS,
    ).getInfo()

    result = {
        "tile_url": tile_url,
        "vis_params": vis,
        "stats": stats,
        "layer_name": "Healthcare Accessibility (travel time in minutes)",
    }

    gee_cache.set(key, result, ttl=CACHE_TTL_STATIC)
    return result


def sample_point(lon: float, lat: float, year: int = 2023, month: int = 6) -> dict[str, Any]:
    """Sample all data at a specific point."""
    api = get_api()
    return api.sample_at_point(lon, lat, year, month)


def corridor_transect(year: int = 2023, month: int = 6) -> list[dict]:
    """Sample all data at the 13 corridor nodes."""
    api = get_api()
    return api.sample_transect(year, month)


def zone_stats(layer: str, year: int | None, month: int | None, group_by: str = "country") -> dict:
    """Compute zonal statistics for a layer."""
    api = get_api()

    layer_map = {
        "nightlights": lambda: api.nightlights(year or 2023, month or 6),
        "ndvi": lambda: api.ndvi(year or 2023, month or 6),
        "economic_index": lambda: api.economic_activity_index(year or 2023, month or 6),
        "population": lambda: api.population(year or 2020),
        "forest_loss": lambda: api.hansen_forest().select("loss"),
    }

    image_fn = layer_map.get(layer)
    if not image_fn:
        return {"error": f"Unknown layer: {layer}"}

    image = image_fn()

    if group_by == "country":
        return api.zone_stats_by_country(image)
    return api.zone_stats(image)


# ── Cache pre-warming ────────────────────────────────────────────────────────

def prewarm_cache() -> None:
    """Pre-warm cache with common queries on server startup."""
    logger.info("Pre-warming GEE cache...")
    try:
        get_landcover()
        get_elevation()
        get_forest()
        logger.info("GEE cache pre-warmed (static layers)")
    except Exception as exc:
        logger.warning("Cache pre-warm failed: %s", exc)
