import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from datetime import datetime, timezone

from .description import TOOL_DESCRIPTION
from .schema import FetchLayersInput


# --- Tool Implementation ---
@tool("fetch_geospatial_layers", description=TOOL_DESCRIPTION)
def fetch_geospatial_layers_tool(
    payload: FetchLayersInput, runtime: ToolRuntime
) -> Command:
    """
    Downloads, clips, and processes geospatial layers for the specified corridor.
    Returns file paths (URIs) and key data points extracted from the layers.
    """

    # In a real-world scenario, this tool would:
    # 1. Connect to an API (like Google Earth Engine or Sentinel Hub)
    # 2. Use the Corridor Polygon to 'Clip' the data
    # 3. Perform raster calculations (like slope or cloud masking)

    response = {
        "corridor_id": "AL_CORRIDOR_POC_001",
        "status": "Analysis Ready Data (ARD) Generated",
        "data_inventory": {
            "layers_requested": ["satellite", "dem", "land_use", "protected_areas"],
            "raster_layers": {
                "satellite": {
                    "source": "Sentinel-2 L2A",
                    "collection": "COPERNICUS/S2_SR_HARMONIZED",
                    "resolution_meters": 10,
                    "bands": ["B2", "B3", "B4", "B8"],
                    "band_labels": ["Blue", "Green", "Red", "NIR"],
                    "scene_count": 47,
                    "cloud_cover_threshold_pct": 15,
                    "compositing_method": "Median (6-month window)",
                    "date_range": {"start": "2025-06-01", "end": "2025-12-31"},
                    "actual_cloud_cover_pct": 8.3,
                    "radiometric_correction": "Surface Reflectance (Bottom of Atmosphere)",
                    "pixel_count": 184320000,
                    "nodata_pct": 1.2,
                },
                "dem": {
                    "source": "SRTM GL1",
                    "collection": "USGS/SRTMGL1_003",
                    "resolution_meters": 30,
                    "vertical_accuracy_m": 16,
                    "datum": "EGM96 Geoid",
                    "elevation_range_m": {"min": 0, "max": 142},
                    "void_filled": True,
                    "void_fill_source": "ASTER GDEM v3",
                    "pixel_count": 18432000,
                },
                "land_use": {
                    "source": "ESA WorldCover 2021",
                    "collection": "ESA/WorldCover/v200",
                    "resolution_meters": 10,
                    "classification_system": "FAO LCCS Level 3",
                    "overall_accuracy_pct": 74.6,
                    "classes_present": [
                        {"code": 10, "label": "Tree Cover", "area_pct": 18.4},
                        {"code": 20, "label": "Shrubland", "area_pct": 11.2},
                        {"code": 30, "label": "Grassland", "area_pct": 9.6},
                        {"code": 40, "label": "Cropland", "area_pct": 28.7},
                        {"code": 50, "label": "Built-up", "area_pct": 12.1},
                        {"code": 60, "label": "Bare / Sparse Veg", "area_pct": 3.8},
                        {"code": 80, "label": "Permanent Water", "area_pct": 7.4},
                        {"code": 90, "label": "Herbaceous Wetland", "area_pct": 6.3},
                        {"code": 95, "label": "Mangroves", "area_pct": 2.5},
                    ],
                },
            },
            "vector_layers": {
                "protected_areas": {
                    "source": "WDPA (World Database of Protected Areas)",
                    "version": "WDPA_Jan2026",
                    "provider": "UNEP-WCMC / IUCN",
                    "feature_type": "Polygon",
                    "feature_count": 34,
                    "total_protected_area_sqkm": 8621.4,
                    "pct_of_corridor_buffer": 8.4,
                    "iucn_categories_present": ["Ia", "II", "IV", "VI", "Not Reported"],
                    "notable_sites": [
                        {
                            "name": "Ankasa Conservation Area",
                            "country": "Ghana",
                            "iucn_category": "II",
                            "area_sqkm": 509.0,
                            "overlap_with_buffer": True,
                        },
                        {
                            "name": "Nzema Forest Reserve",
                            "country": "Ghana",
                            "iucn_category": "VI",
                            "area_sqkm": 182.3,
                            "overlap_with_buffer": True,
                        },
                        {
                            "name": "Lekki Conservation Centre",
                            "country": "Nigeria",
                            "iucn_category": "IV",
                            "area_sqkm": 78.2,
                            "overlap_with_buffer": True,
                        },
                    ],
                },
                "administrative_boundaries": {
                    "source": "GADM v4.1",
                    "feature_type": "Polygon",
                    "levels_included": [
                        "ADM0 (Country)",
                        "ADM1 (Region/State)",
                        "ADM2 (District)",
                    ],
                    "countries_intersected": [
                        "Côte d'Ivoire",
                        "Ghana",
                        "Togo",
                        "Benin",
                        "Nigeria",
                    ],
                    "adm1_units_intersected": 18,
                    "adm2_units_intersected": 74,
                },
                "osm_infrastructure": {
                    "source": "OpenStreetMap (Overpass API)",
                    "extract_date": "2026-01-15",
                    "feature_type": "Mixed (Point / LineString / Polygon)",
                    "features_extracted": {
                        "highways_km": 4820,
                        "power_lines_km": 1340,
                        "substations_count": 28,
                        "ports_count": 11,
                        "airports_count": 7,
                        "industrial_zones_count": 19,
                    },
                },
            },
        },
        "uris": {
            "satellite_raster_uri": "s3://corridor-platform/data/AL_CORRIDOR_POC_001/satellite/sentinel2_median_2025H2_10m.tif",
            "dem_raster_uri": "s3://corridor-platform/data/AL_CORRIDOR_POC_001/dem/srtm_gl1_void_filled_30m.tif",
            "land_use_raster_uri": "s3://corridor-platform/data/AL_CORRIDOR_POC_001/land_use/esa_worldcover_2021_10m.tif",
            "protected_areas_vector_uri": "s3://corridor-platform/data/AL_CORRIDOR_POC_001/vectors/wdpa_protected_areas.geojson",
            "admin_boundaries_vector_uri": "s3://corridor-platform/data/AL_CORRIDOR_POC_001/vectors/gadm41_admin_boundaries.geojson",
            "osm_infrastructure_uri": "s3://corridor-platform/data/AL_CORRIDOR_POC_001/vectors/osm_infrastructure_extract.geojson",
            "composite_preview_uri": "s3://corridor-platform/data/AL_CORRIDOR_POC_001/previews/rgb_thumbnail_256px.png",
        },
        "metadata": {
            "crs": "EPSG:4326 (WGS84)",
            "corridor_bounding_box": {
                "min_longitude": -4.200,
                "min_latitude": 4.800,
                "max_longitude": 3.750,
                "max_latitude": 6.800,
            },
            "corridor_length_km": 1080,
            "buffer_each_side_km": 50,
            "clip_area_sqkm": 102430.0,
            "processing_level": "Analysis Ready Data (ARD)",
            "projection_used_for_area_calc": "EPSG:32630 (UTM Zone 30N)",
            "generated_at": "2026-01-26T09:14:32+00:00",
            "processing_time_seconds": 184,
            "platform_version": "corridor-intelligence-platform@1.0.0",
            "data_quality_flags": {
                "dem_voids_detected": False,
                "satellite_cloud_threshold_met": True,
                "land_use_coverage_complete": True,
                "protected_areas_current": True,
                "any_warnings": False,
            },
            "downstream_tools_ready": [
                "infrastructure_detection",
                "terrain_analysis",
                "route_optimization",
                "environmental_constraint_mapping",
            ],
        },
    }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response), tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )
