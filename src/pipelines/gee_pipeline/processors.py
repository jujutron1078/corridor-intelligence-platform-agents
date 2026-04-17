"""
GEE dataset processors — one function per dataset.

All computation happens server-side in GEE. Functions return ee.Image
or ee.ImageCollection objects. No data is pulled locally.
"""

from __future__ import annotations

import ee

from src.shared.pipeline.aoi import CORRIDOR
from .config import (
    S2_COLLECTION, S2_CLOUD_BAND, S2_CLOUD_CLASSES, S2_MAX_CLOUD_PCT,
    S2_SCALE_FACTOR,
    VIIRS_COLLECTION, VIIRS_BAND, VIIRS_NOISE_THRESHOLD,
    WORLDCOVER_COLLECTION, WORLDCOVER_BAND,
    DYNAMIC_WORLD_COLLECTION, DYNAMIC_WORLD_BAND,
    SRTM_COLLECTION, SRTM_BAND,
    WORLDPOP_COLLECTION, WORLDPOP_BAND, WORLDPOP_YEAR_MIN, WORLDPOP_YEAR_MAX,
    JRC_WATER_COLLECTION, JRC_WATER_BANDS,
    HANSEN_COLLECTION, HANSEN_BANDS,
    COP_DEM_COLLECTION, COP_DEM_BAND,
    GHSL_COLLECTION, GHSL_BAND, GHSL_EPOCHS,
    OPEN_BUILDINGS_COLLECTION, OPEN_BUILDINGS_RASTER_SCALE,
    S1_COLLECTION, S1_BANDS, S1_INSTRUMENT_MODE, S1_ORBIT,
    ERA5_COLLECTION, ERA5_TEMP_BAND, ERA5_PRECIP_BAND,
    ERA5_WIND_U_BAND, ERA5_WIND_V_BAND,
    EAI_NIGHTLIGHTS_WEIGHT, EAI_NDBI_WEIGHT, EAI_INV_NDVI_WEIGHT,
    WDPA_COLLECTION, WDPA_STATUS_FILTER,
    HEALTHCARE_ACCESS_IMAGE, HEALTHCARE_ACCESS_BAND, HEALTHCARE_ACCESS_MAX_MINUTES,
)


def _aoi() -> ee.Geometry:
    """Return the corridor AOI as an ee.Geometry."""
    return CORRIDOR.to_ee_geometry()


def _date_range(year: int, month: int) -> tuple[str, str]:
    """Return (start, end) date strings for a given year/month."""
    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year + 1}-01-01"
    else:
        end = f"{year}-{month + 1:02d}-01"
    return start, end


def _annual_range(year: int) -> tuple[str, str]:
    """Return (start, end) date strings for a full year."""
    return f"{year}-01-01", f"{year + 1}-01-01"


# ═══════════════════════════════════════════════════════════════════════════════
# TIER 1 — Core Economic Datasets
# ═══════════════════════════════════════════════════════════════════════════════


# ── Sentinel-2 ────────────────────────────────────────────────────────────────

def _mask_s2_clouds(image: ee.Image) -> ee.Image:
    """Mask clouds using SCL band classes 3, 8, 9, 10, 11."""
    scl = image.select(S2_CLOUD_BAND)
    mask = ee.Image(1)
    for cls in S2_CLOUD_CLASSES:
        mask = mask.And(scl.neq(cls))
    return image.updateMask(mask)


def sentinel2_composite(year: int, month: int) -> ee.Image:
    """Monthly cloud-free Sentinel-2 median composite with NDVI, NDBI, MNDWI."""
    start, end = _date_range(year, month)
    aoi = _aoi()

    col = (
        ee.ImageCollection(S2_COLLECTION)
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", S2_MAX_CLOUD_PCT))
        .map(_mask_s2_clouds)
    )

    composite = col.median().clip(aoi)

    # Scale reflectance to 0-1
    scaled = composite.select(["B2", "B3", "B4", "B8", "B11", "B12"]).divide(S2_SCALE_FACTOR)

    nir = scaled.select("B8")
    red = scaled.select("B4")
    green = scaled.select("B3")
    swir = scaled.select("B11")

    ndvi = nir.subtract(red).divide(nir.add(red)).rename("NDVI")
    ndbi = swir.subtract(nir).divide(swir.add(nir)).rename("NDBI")
    mndwi = green.subtract(swir).divide(green.add(swir)).rename("MNDWI")

    return scaled.addBands([ndvi, ndbi, mndwi])


# ── VIIRS Nightlights ────────────────────────────────────────────────────────

def nightlights(year: int, month: int) -> ee.Image:
    """Monthly VIIRS nighttime lights, noise-filtered."""
    start, end = _date_range(year, month)
    aoi = _aoi()

    col = (
        ee.ImageCollection(VIIRS_COLLECTION)
        .filterBounds(aoi)
        .filterDate(start, end)
    )

    image = col.median().select(VIIRS_BAND).clip(aoi)
    return image.updateMask(image.gte(VIIRS_NOISE_THRESHOLD))


def nightlights_change(year_start: int, year_end: int) -> ee.Image:
    """Radiance change between two years (annual average)."""
    aoi = _aoi()

    def _annual_mean(year: int) -> ee.Image:
        s, e = _annual_range(year)
        return (
            ee.ImageCollection(VIIRS_COLLECTION)
            .filterBounds(aoi)
            .filterDate(s, e)
            .select(VIIRS_BAND)
            .mean()
            .clip(aoi)
        )

    early = _annual_mean(year_start)
    late = _annual_mean(year_end)
    return late.subtract(early).rename("radiance_change")


# ── ESA WorldCover ────────────────────────────────────────────────────────────

def worldcover() -> ee.Image:
    """ESA WorldCover 10m land classification (2021)."""
    aoi = _aoi()
    return ee.ImageCollection(WORLDCOVER_COLLECTION).first().select(WORLDCOVER_BAND).clip(aoi)


# ── Dynamic World ─────────────────────────────────────────────────────────────

def dynamic_world(year: int, month: int) -> ee.Image:
    """Monthly mode composite of Dynamic World labels."""
    start, end = _date_range(year, month)
    aoi = _aoi()

    col = (
        ee.ImageCollection(DYNAMIC_WORLD_COLLECTION)
        .filterBounds(aoi)
        .filterDate(start, end)
        .select(DYNAMIC_WORLD_BAND)
    )

    return col.mode().clip(aoi)


# ── SRTM Elevation ───────────────────────────────────────────────────────────

def elevation() -> ee.Image:
    """SRTM elevation with derived slope and aspect."""
    aoi = _aoi()
    dem = ee.Image(SRTM_COLLECTION).clip(aoi)
    terrain = ee.Terrain.products(dem)
    return terrain.select(["elevation", "slope", "aspect"])


# ── WorldPop ─────────────────────────────────────────────────────────────────

def population(year: int) -> ee.Image:
    """WorldPop 100m gridded population for a given year."""
    year = max(WORLDPOP_YEAR_MIN, min(WORLDPOP_YEAR_MAX, year))
    aoi = _aoi()

    col = (
        ee.ImageCollection(WORLDPOP_COLLECTION)
        .filterBounds(aoi)
        .filter(ee.Filter.eq("year", year))
        .select(WORLDPOP_BAND)
    )

    return col.mosaic().clip(aoi)


def population_change(year_start: int, year_end: int) -> ee.Image:
    """Population change between two years."""
    early = population(year_start)
    late = population(year_end)
    return late.subtract(early).rename("population_change")


# ── JRC Surface Water ────────────────────────────────────────────────────────

def surface_water() -> ee.Image:
    """JRC Global Surface Water — occurrence, change, seasonality, recurrence."""
    aoi = _aoi()
    return ee.Image(JRC_WATER_COLLECTION).select(JRC_WATER_BANDS).clip(aoi)


# ── Hansen Forest Change ─────────────────────────────────────────────────────

def hansen_forest() -> ee.Image:
    """Hansen Global Forest Change — treecover2000, loss, gain, lossyear."""
    aoi = _aoi()
    return ee.Image(HANSEN_COLLECTION).select(HANSEN_BANDS).clip(aoi)


def forest_loss_by_year(start_year: int, end_year: int) -> ee.Image:
    """Forest loss mask for a specific year range (lossyear encoded as 1-23 for 2001-2023)."""
    aoi = _aoi()
    hansen = ee.Image(HANSEN_COLLECTION).clip(aoi)
    lossyear = hansen.select("lossyear")
    # lossyear values: 1=2001, ..., 23=2023
    start_code = start_year - 2000
    end_code = end_year - 2000
    return lossyear.gte(start_code).And(lossyear.lte(end_code)).rename("forest_loss_period")


# ═══════════════════════════════════════════════════════════════════════════════
# TIER 2 — Enrichment Datasets
# ═══════════════════════════════════════════════════════════════════════════════


# ── Copernicus DEM ───────────────────────────────────────────────────────────

def copernicus_dem() -> ee.Image:
    """Copernicus GLO-30 DEM mosaic."""
    aoi = _aoi()
    return (
        ee.ImageCollection(COP_DEM_COLLECTION)
        .filterBounds(aoi)
        .select(COP_DEM_BAND)
        .mosaic()
        .clip(aoi)
    )


# ── GHSL Built-Up ────────────────────────────────────────────────────────────

def ghsl_built(epoch: int = 2020) -> ee.Image:
    """GHSL built-up surface for a specific epoch."""
    aoi = _aoi()
    col = (
        ee.ImageCollection(GHSL_COLLECTION)
        .filterBounds(aoi)
        .filter(ee.Filter.eq("system:index", str(epoch)))
        .select(GHSL_BAND)
    )
    return col.mosaic().clip(aoi)


def ghsl_change(epoch_start: int, epoch_end: int) -> ee.Image:
    """GHSL built-up change between two epochs."""
    early = ghsl_built(epoch_start)
    late = ghsl_built(epoch_end)
    return late.subtract(early).rename("built_change")


# ── Google Open Buildings ────────────────────────────────────────────────────

def open_buildings_density() -> ee.Image:
    """Rasterized building density at 1km grid from Open Buildings polygons."""
    aoi = _aoi()
    buildings = (
        ee.FeatureCollection(OPEN_BUILDINGS_COLLECTION)
        .filterBounds(aoi)
    )
    # Rasterize: count buildings per 1km pixel
    return (
        buildings
        .reduceToImage(properties=["area_in_meters"], reducer=ee.Reducer.count())
        .rename("building_count")
        .clip(aoi)
    )


# ── Sentinel-1 SAR ──────────────────────────────────────────────────────────

def sentinel1_composite(year: int, month: int) -> ee.Image:
    """Monthly median Sentinel-1 SAR composite (VV, VH, VV/VH ratio)."""
    start, end = _date_range(year, month)
    aoi = _aoi()

    col = (
        ee.ImageCollection(S1_COLLECTION)
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.eq("instrumentMode", S1_INSTRUMENT_MODE))
        .filter(ee.Filter.eq("orbitProperties_pass", S1_ORBIT))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select(S1_BANDS)
    )

    composite = col.median().clip(aoi)
    ratio = composite.select("VV").subtract(composite.select("VH")).rename("VV_VH_ratio")
    return composite.addBands(ratio)


# ── ERA5-Land Climate ────────────────────────────────────────────────────────

def era5_climate(year: int, month: int) -> ee.Image:
    """Monthly ERA5-Land climate: temperature (°C), precipitation (mm), wind speed."""
    start, end = _date_range(year, month)
    aoi = _aoi()

    col = (
        ee.ImageCollection(ERA5_COLLECTION)
        .filterBounds(aoi)
        .filterDate(start, end)
    )

    image = col.first().clip(aoi)

    temp_c = image.select(ERA5_TEMP_BAND).subtract(273.15).rename("temperature_c")
    precip_mm = image.select(ERA5_PRECIP_BAND).multiply(1000).rename("precipitation_mm")

    u = image.select(ERA5_WIND_U_BAND)
    v = image.select(ERA5_WIND_V_BAND)
    wind_speed = u.pow(2).add(v.pow(2)).sqrt().rename("wind_speed_ms")

    return temp_c.addBands([precip_mm, wind_speed])


# ═══════════════════════════════════════════════════════════════════════════════
# COMPOSITE INDICES
# ═══════════════════════════════════════════════════════════════════════════════

def economic_activity_index(year: int, month: int) -> ee.Image:
    """
    Composite Economic Activity Index (0-1).

    Nightlights normalized (0.5) + NDBI normalized (0.3) + inverse NDVI (0.2).
    """
    aoi = _aoi()

    # Nightlights — normalize 0-1 within corridor
    nl = nightlights(year, month)
    # Use fixed range for normalization (0-60 nW/cm²/sr covers most corridor values)
    nl_norm = nl.unitScale(0, 60).clamp(0, 1).rename("nl_norm")

    # Sentinel-2 indices
    s2 = sentinel2_composite(year, month)
    ndbi = s2.select("NDBI")
    ndvi = s2.select("NDVI")

    # Normalize NDBI (-0.3 to 0.3 typical range)
    ndbi_norm = ndbi.unitScale(-0.3, 0.3).clamp(0, 1).rename("ndbi_norm")

    # Inverse NDVI (high vegetation = low economic activity)
    inv_ndvi = ee.Image(1).subtract(ndvi.unitScale(0, 0.8).clamp(0, 1)).rename("inv_ndvi_norm")

    # Weighted combination
    eai = (
        nl_norm.multiply(EAI_NIGHTLIGHTS_WEIGHT)
        .add(ndbi_norm.multiply(EAI_NDBI_WEIGHT))
        .add(inv_ndvi.multiply(EAI_INV_NDVI_WEIGHT))
        .rename("economic_activity_index")
        .clip(aoi)
    )

    return eai


# ═══════════════════════════════════════════════════════════════════════════════
# CHANGE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def urban_expansion(year_start: int, year_end: int) -> ee.Image:
    """
    Detect urban expansion using Dynamic World.
    Returns a binary mask: 1 = newly built-up, 0 = no change.
    """
    early = dynamic_world(year_start, 6)  # June composite for consistency
    late = dynamic_world(year_end, 6)

    # Class 6 = built in Dynamic World
    built_early = early.eq(6)
    built_late = late.eq(6)

    # New built = was NOT built before, IS built now
    return built_late.And(built_early.Not()).rename("urban_expansion")


# ═══════════════════════════════════════════════════════════════════════════════
# ENVIRONMENTAL & HEALTH ACCESS
# ═══════════════════════════════════════════════════════════════════════════════


def protected_areas() -> ee.Image:
    """
    WDPA Protected Areas rasterized to a binary mask.
    1 = protected, 0 = not protected.
    """
    aoi = _aoi()
    wdpa = (
        ee.FeatureCollection(WDPA_COLLECTION)
        .filterBounds(aoi)
        .filter(ee.Filter.inList("STATUS", WDPA_STATUS_FILTER))
    )
    # Rasterize: 1 inside protected area, 0 outside
    return (
        wdpa
        .reduceToImage(properties=["REP_AREA"], reducer=ee.Reducer.first())
        .gt(0)
        .unmask(0)
        .rename("protected_area")
        .clip(aoi)
    )


def protected_areas_vector() -> ee.FeatureCollection:
    """WDPA Protected Areas as vector FeatureCollection for GeoJSON export."""
    aoi = _aoi()
    return (
        ee.FeatureCollection(WDPA_COLLECTION)
        .filterBounds(aoi)
        .filter(ee.Filter.inList("STATUS", WDPA_STATUS_FILTER))
        .select(["NAME", "DESIG", "STATUS", "IUCN_CAT", "REP_AREA", "STATUS_YR"])
    )


def healthcare_accessibility() -> ee.Image:
    """
    Oxford/MAP travel time to nearest healthcare facility (minutes).
    Lower values = better access.
    """
    aoi = _aoi()
    image = ee.Image(HEALTHCARE_ACCESS_IMAGE).select(HEALTHCARE_ACCESS_BAND)
    return image.clamp(0, HEALTHCARE_ACCESS_MAX_MINUTES).rename("travel_time_minutes").clip(aoi)
