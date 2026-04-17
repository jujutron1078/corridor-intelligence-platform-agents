"""
GEE pipeline configuration — dataset catalog, processing parameters, constants.
"""

from __future__ import annotations

# ── Sentinel-2 ────────────────────────────────────────────────────────────────

S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
S2_CLOUD_BAND = "SCL"
S2_CLOUD_CLASSES = [3, 8, 9, 10, 11]  # cloud shadow, cirrus, cloud, etc.
S2_MAX_CLOUD_PCT = 20
S2_SCALE_FACTOR = 10_000  # reflectance stored as uint16 × 10000
S2_TEMPORAL_START = "2015-06-01"
S2_TEMPORAL_END = "2024-12-31"

# ── VIIRS Nightlights ────────────────────────────────────────────────────────

VIIRS_COLLECTION = "NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG"
VIIRS_BAND = "avg_rad"
VIIRS_NOISE_THRESHOLD = 0.5  # nW/cm²/sr
VIIRS_TEMPORAL_START = "2012-04-01"
VIIRS_TEMPORAL_END = "2024-12-31"

# ── ESA WorldCover ────────────────────────────────────────────────────────────

WORLDCOVER_COLLECTION = "ESA/WorldCover/v200"
WORLDCOVER_BAND = "Map"
WORLDCOVER_CLASSES = {
    10: "Trees",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare/sparse",
    80: "Water",
    90: "Wetland",
    95: "Mangrove",
}

# ── Dynamic World ─────────────────────────────────────────────────────────────

DYNAMIC_WORLD_COLLECTION = "GOOGLE/DYNAMICWORLD/V1"
DYNAMIC_WORLD_BAND = "label"
DYNAMIC_WORLD_CLASSES = {
    0: "water",
    1: "trees",
    2: "grass",
    3: "flooded_vegetation",
    4: "crops",
    5: "shrub_and_scrub",
    6: "built",
    7: "bare",
    8: "snow_and_ice",
}
DYNAMIC_WORLD_START = "2016-01-01"
DYNAMIC_WORLD_END = "2024-12-31"

# ── SRTM Elevation ───────────────────────────────────────────────────────────

SRTM_COLLECTION = "USGS/SRTMGL1_003"
SRTM_BAND = "elevation"

# ── WorldPop ─────────────────────────────────────────────────────────────────

WORLDPOP_COLLECTION = "WorldPop/GP/100m/pop"
WORLDPOP_BAND = "population"
WORLDPOP_YEAR_MIN = 2000
WORLDPOP_YEAR_MAX = 2020

# ── JRC Surface Water ────────────────────────────────────────────────────────

JRC_WATER_COLLECTION = "JRC/GSW1_4/GlobalSurfaceWater"
JRC_WATER_BANDS = ["occurrence", "change_abs", "seasonality", "recurrence"]

# ── Hansen Forest Change ─────────────────────────────────────────────────────

HANSEN_COLLECTION = "UMD/hansen/global_forest_change_2024_v1_12"
HANSEN_BANDS = ["treecover2000", "loss", "gain", "lossyear"]

# ── Copernicus DEM (Tier 2) ──────────────────────────────────────────────────

COP_DEM_COLLECTION = "COPERNICUS/DEM/GLO30"
COP_DEM_BAND = "DEM"

# ── GHSL Built-Up (Tier 2) ──────────────────────────────────────────────────

GHSL_COLLECTION = "JRC/GHSL/P2023A/GHS_BUILT_S"
GHSL_BAND = "built_surface"
GHSL_EPOCHS = [1975, 1990, 2000, 2015, 2020]

# ── Google Open Buildings (Tier 2) ───────────────────────────────────────────

OPEN_BUILDINGS_COLLECTION = "GOOGLE/Research/open-buildings/v3/polygons"
OPEN_BUILDINGS_RASTER_SCALE = 1000  # 1km grid for density

# ── Sentinel-1 SAR (Tier 2) ─────────────────────────────────────────────────

S1_COLLECTION = "COPERNICUS/S1_GRD"
S1_BANDS = ["VV", "VH"]
S1_INSTRUMENT_MODE = "IW"
S1_ORBIT = "DESCENDING"
S1_TEMPORAL_START = "2015-01-01"
S1_TEMPORAL_END = "2024-12-31"

# ── ERA5-Land Climate (Tier 2) ───────────────────────────────────────────────

ERA5_COLLECTION = "ECMWF/ERA5_LAND/MONTHLY_AGGR"
ERA5_TEMP_BAND = "temperature_2m"
ERA5_PRECIP_BAND = "total_precipitation_sum"
ERA5_WIND_U_BAND = "u_component_of_wind_10m"
ERA5_WIND_V_BAND = "v_component_of_wind_10m"
ERA5_TEMPORAL_START = "2015-01-01"
ERA5_TEMPORAL_END = "2024-12-31"

# ── WDPA Protected Areas (Tier 2) ──────────────────────────────────────────

WDPA_COLLECTION = "WCMC/WDPA/current/polygons"
WDPA_STATUS_FILTER = ["Designated", "Inscribed", "Established"]

# ── Oxford/MAP Healthcare Accessibility (Tier 2) ──────────────────────────

HEALTHCARE_ACCESS_IMAGE = "projects/malariaatlasproject/assets/accessibility/accessibility_to_healthcare/2019"
HEALTHCARE_ACCESS_BAND = "accessibility"
HEALTHCARE_ACCESS_MAX_MINUTES = 180  # cap at 3 hours for visualization

# ── Global Flood Database (Tier 2) ─────────────────────────────────────────

FLOOD_COLLECTION = "GLOBAL_FLOOD_DB/MODIS_EVENTS/V1"
FLOOD_BANDS = ["flooded", "duration", "clear_views"]

# ── JRC Flood Hazard Maps (Tier 2) ────────────────────────────────────────

JRC_FLOOD_COLLECTION = "JRC/CEMS_GLOFAS/FloodHazard"
JRC_FLOOD_BAND = "flood_hazard"

# ── iSDAsoil Africa (Tier 2) ──────────────────────────────────────────────

ISDASOIL_CLAY = "ISDASOIL/Africa/v1/clay_content"
ISDASOIL_PH = "ISDASOIL/Africa/v1/ph"
ISDASOIL_SAND = "ISDASOIL/Africa/v1/sand_content"
ISDASOIL_BULK_DENSITY = "ISDASOIL/Africa/v1/bulk_density"
ISDASOIL_ORGANIC_CARBON = "ISDASOIL/Africa/v1/carbon_organic"
ISDASOIL_NITROGEN = "ISDASOIL/Africa/v1/nitrogen_total"
ISDASOIL_BANDS = ["mean_0_20", "mean_20_50"]  # depth intervals in cm

# ── Solar & Wind Resource (derived from ERA5-Land) ────────────────────────

ERA5_SOLAR_BAND = "surface_solar_radiation_downwards_sum"
ERA5_DEWPOINT_BAND = "dewpoint_temperature_2m"

# ── Economic Activity Index weights ─────────────────────────────────────────

EAI_NIGHTLIGHTS_WEIGHT = 0.5
EAI_NDBI_WEIGHT = 0.3
EAI_INV_NDVI_WEIGHT = 0.2

# ── Processing defaults ─────────────────────────────────────────────────────

DEFAULT_SCALE = 100  # meters — for reduceRegion / sampling
MAX_PIXELS = 1e9

# ── Visualization palettes ───────────────────────────────────────────────────

VIS_PARAMS = {
    "nightlights": {"min": 0, "max": 60, "palette": ["000000", "FFFF00", "FFFFFF"]},
    "ndvi": {"min": -0.2, "max": 0.8, "palette": ["CE7E45", "DF923D", "F1B555", "FCD163", "99B718", "74A901", "66A000", "529400", "3E8601", "207401", "056201"]},
    "ndbi": {"min": -0.3, "max": 0.3, "palette": ["2166AC", "F7F7F7", "B2182B"]},
    "mndwi": {"min": -0.5, "max": 0.5, "palette": ["D7191C", "FFFFBF", "2C7BB6"]},
    "economic_index": {"min": 0, "max": 1, "palette": ["440154", "31688E", "35B779", "FDE725"]},
    "elevation": {"min": 0, "max": 500, "palette": ["006633", "E5FFCC", "662A00", "D8D8D8", "F5F5F5"]},
    "slope": {"min": 0, "max": 30, "palette": ["FFFFFF", "FF0000"]},
    "population": {"min": 0, "max": 1000, "palette": ["FFFFCC", "FD8D3C", "BD0026"]},
    "worldcover": {"min": 10, "max": 95, "palette": ["006400", "FFBB22", "FFFF4C", "F096FF", "FA0000", "B4B4B4", "0064C8", "0096A0", "00CF75"]},
    "forest_loss": {"min": 0, "max": 1, "palette": ["FFFFFF", "FF0000"]},
    "urban_expansion": {"min": 0, "max": 1, "palette": ["FFFFFF", "FF4500"]},
    "nightlights_change": {"min": -20, "max": 50, "palette": ["0000FF", "FFFFFF", "FF0000"]},
    "sar_vv": {"min": -25, "max": 0, "palette": ["000000", "FFFFFF"]},
    "sar_vh": {"min": -30, "max": -5, "palette": ["000000", "FFFFFF"]},
    "temperature": {"min": 20, "max": 35, "palette": ["2166AC", "F7F7F7", "B2182B"]},
    "precipitation": {"min": 0, "max": 300, "palette": ["FFFFFF", "00BFFF", "0000FF"]},
    "building_density": {"min": 0, "max": 500, "palette": ["FFFFFF", "FFA500", "FF0000"]},
    "ghsl": {"min": 0, "max": 10000, "palette": ["FFFFFF", "FFA500", "FF0000"]},
    "protected_areas": {"min": 0, "max": 1, "palette": ["FFFFFF", "228B22"]},
    "healthcare_access": {"min": 0, "max": 180, "palette": ["00FF00", "FFFF00", "FF8C00", "FF0000"]},
    "flood_hazard": {"min": 0, "max": 1, "palette": ["FFFFFF", "0000FF"]},
    "soil_clay": {"min": 0, "max": 60, "palette": ["FFFFCC", "D7191C"]},
    "soil_ph": {"min": 4, "max": 9, "palette": ["FF0000", "00FF00"]},
    "solar_radiation": {"min": 100, "max": 300, "palette": ["FFFFCC", "FF8C00", "FF0000"]},
}

# ── Test points for validation ───────────────────────────────────────────────

TEST_POINTS = {
    "Lagos": (3.40, 6.45),
    "Cotonou": (2.42, 6.37),
    "Lomé": (1.23, 6.17),
    "Accra": (-0.19, 5.60),
    "Takoradi": (-1.76, 4.93),
    "Abidjan": (-3.97, 5.36),
}

# ── Dataset catalog (for validation and catalog module) ──────────────────────

DATASET_CATALOG = {
    "sentinel2": {
        "collection": S2_COLLECTION,
        "tier": 1,
        "type": "image_collection",
        "temporal": "2015-2024",
        "resolution": "10m",
    },
    "viirs_nightlights": {
        "collection": VIIRS_COLLECTION,
        "tier": 1,
        "type": "image_collection",
        "temporal": "2012-2024",
        "resolution": "500m",
    },
    "worldcover": {
        "collection": WORLDCOVER_COLLECTION,
        "tier": 1,
        "type": "image",
        "temporal": "2021 (static)",
        "resolution": "10m",
    },
    "dynamic_world": {
        "collection": DYNAMIC_WORLD_COLLECTION,
        "tier": 1,
        "type": "image_collection",
        "temporal": "2016-2024",
        "resolution": "10m",
    },
    "srtm": {
        "collection": SRTM_COLLECTION,
        "tier": 1,
        "type": "image",
        "temporal": "static",
        "resolution": "30m",
    },
    "worldpop": {
        "collection": WORLDPOP_COLLECTION,
        "tier": 1,
        "type": "image_collection",
        "temporal": "2000-2020",
        "resolution": "100m",
    },
    "jrc_water": {
        "collection": JRC_WATER_COLLECTION,
        "tier": 1,
        "type": "image",
        "temporal": "static (35yr summary)",
        "resolution": "30m",
    },
    "hansen_forest": {
        "collection": HANSEN_COLLECTION,
        "tier": 1,
        "type": "image",
        "temporal": "static (annual loss encoded)",
        "resolution": "30m",
    },
    "copernicus_dem": {
        "collection": COP_DEM_COLLECTION,
        "tier": 2,
        "type": "image_collection",
        "temporal": "static",
        "resolution": "30m",
    },
    "ghsl": {
        "collection": GHSL_COLLECTION,
        "tier": 2,
        "type": "image_collection",
        "temporal": "multi-epoch (1975-2020)",
        "resolution": "100m",
    },
    "open_buildings": {
        "collection": OPEN_BUILDINGS_COLLECTION,
        "tier": 2,
        "type": "feature_collection",
        "temporal": "static",
        "resolution": "building-level",
    },
    "sentinel1": {
        "collection": S1_COLLECTION,
        "tier": 2,
        "type": "image_collection",
        "temporal": "2015-2024",
        "resolution": "10m",
    },
    "era5_land": {
        "collection": ERA5_COLLECTION,
        "tier": 2,
        "type": "image_collection",
        "temporal": "2015-2024",
        "resolution": "11km",
    },
    "wdpa_protected_areas": {
        "collection": WDPA_COLLECTION,
        "tier": 2,
        "type": "feature_collection",
        "temporal": "static (updated regularly)",
        "resolution": "vector (polygons)",
    },
    "healthcare_accessibility": {
        "collection": HEALTHCARE_ACCESS_IMAGE,
        "tier": 2,
        "type": "image",
        "temporal": "2019 (static)",
        "resolution": "1km",
    },
    "flood_database": {
        "collection": FLOOD_COLLECTION,
        "tier": 2,
        "type": "image_collection",
        "temporal": "2000-2018 (historical events)",
        "resolution": "250m",
    },
    "isdasoil": {
        "collection": ISDASOIL_CLAY,
        "tier": 2,
        "type": "image",
        "temporal": "static",
        "resolution": "30m",
    },
}
