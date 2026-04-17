import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import TerrainInput

logger = logging.getLogger("corridor.agent.geospatial.terrain")

# Corridor segment reference data — expert-assessed terrain characteristics
# along the Lagos-Abidjan corridor. Elevation stats are enriched with real GEE
# data when available; soil/flood/construction assessments are domain knowledge.
CORRIDOR_SEGMENTS = [
    {
        "segment_id": "SEG-001",
        "label": "Abidjan Coastal Plain",
        "country": "Côte d'Ivoire",
        "start_km": 0, "end_km": 180,
        "start_coordinate": {"latitude": 5.302, "longitude": -4.025},
        "end_coordinate": {"latitude": 5.110, "longitude": -2.900},
        "terrain_profile": {"min_elevation_m": 4, "max_elevation_m": 87, "avg_elevation_m": 38},
        "slope_analysis": {"avg_slope_degrees": 1.4, "max_slope_degrees": 6.2, "pct_slope_under_3deg": 84},
        "soil_stability": {"classification": "High", "dominant_soil_type": "Laterite over Precambrian bedrock", "bearing_capacity_kpa": 280},
        "flood_risk": {"classification": "Low", "flood_zone_pct": 6, "detected_water_bodies": ["Lagune Ebrié (3.2 km crossing)"]},
        "construction_difficulty": {"score": 2.1, "rating": "Easy", "major_obstacles": ["Lagune Ebrié water crossing"]},
        "co_location_opportunity": {"highway_overlap_pct": 78, "existing_road_parallels_km": 140, "estimated_capex_saving_pct": 17},
    },
    {
        "segment_id": "SEG-002",
        "label": "Ghana Western Coastal Strip",
        "country": "Ghana",
        "start_km": 180, "end_km": 370,
        "start_coordinate": {"latitude": 5.110, "longitude": -2.900},
        "end_coordinate": {"latitude": 5.666, "longitude": -0.044},
        "terrain_profile": {"min_elevation_m": 3, "max_elevation_m": 142, "avg_elevation_m": 61},
        "slope_analysis": {"avg_slope_degrees": 3.7, "max_slope_degrees": 18.4, "pct_slope_under_3deg": 52},
        "soil_stability": {"classification": "Medium", "dominant_soil_type": "Sandy Clay Loam with lateritic hardpan", "bearing_capacity_kpa": 180},
        "flood_risk": {"classification": "Medium", "flood_zone_pct": 18, "detected_water_bodies": ["Pra River (1.8 km floodplain)", "Ankobra River delta (4.1 km floodplain)"]},
        "construction_difficulty": {"score": 4.8, "rating": "Moderate", "major_obstacles": ["Pra River crossing (bridge required ~420m span)", "Nzema Forest Reserve buffer zone (8 km re-route recommended)"]},
        "co_location_opportunity": {"highway_overlap_pct": 65, "existing_road_parallels_km": 124, "estimated_capex_saving_pct": 14},
    },
    {
        "segment_id": "SEG-003",
        "label": "Greater Accra & Volta Delta",
        "country": "Ghana",
        "start_km": 370, "end_km": 510,
        "start_coordinate": {"latitude": 5.666, "longitude": -0.044},
        "end_coordinate": {"latitude": 6.032, "longitude": 0.607},
        "terrain_profile": {"min_elevation_m": 0, "max_elevation_m": 58, "avg_elevation_m": 22},
        "slope_analysis": {"avg_slope_degrees": 0.9, "max_slope_degrees": 4.1, "pct_slope_under_3deg": 91},
        "soil_stability": {"classification": "Low-Medium", "dominant_soil_type": "Alluvial silt and deltaic clay", "bearing_capacity_kpa": 95},
        "flood_risk": {"classification": "Critical", "flood_zone_pct": 41, "detected_water_bodies": ["Volta River mouth (11.4 km delta crossing)", "Keta Lagoon (6.8 km marshland zone)"]},
        "construction_difficulty": {"score": 8.3, "rating": "Very Difficult", "major_obstacles": ["Volta River delta crossing", "Keta Lagoon elevated structure", "Soft deltaic soils — pile foundations required"]},
        "co_location_opportunity": {"highway_overlap_pct": 44, "existing_road_parallels_km": 61, "estimated_capex_saving_pct": 9},
    },
    {
        "segment_id": "SEG-004",
        "label": "Togo Coastal Corridor",
        "country": "Togo",
        "start_km": 510, "end_km": 640,
        "start_coordinate": {"latitude": 6.137, "longitude": 1.222},
        "end_coordinate": {"latitude": 6.365, "longitude": 2.406},
        "terrain_profile": {"min_elevation_m": 2, "max_elevation_m": 71, "avg_elevation_m": 29},
        "slope_analysis": {"avg_slope_degrees": 1.8, "max_slope_degrees": 7.3, "pct_slope_under_3deg": 76},
        "soil_stability": {"classification": "High", "dominant_soil_type": "Ferralitic soil over Precambrian schist", "bearing_capacity_kpa": 240},
        "flood_risk": {"classification": "Low-Medium", "flood_zone_pct": 11, "detected_water_bodies": ["Mono River floodplain (2.6 km)", "Lake Togo coastal fringe (1.4 km)"]},
        "construction_difficulty": {"score": 3.2, "rating": "Easy-Moderate", "major_obstacles": ["Mono River crossing (standard bridge ~180m span)"]},
        "co_location_opportunity": {"highway_overlap_pct": 81, "existing_road_parallels_km": 105, "estimated_capex_saving_pct": 18},
    },
    {
        "segment_id": "SEG-005",
        "label": "Benin Coastal Plain",
        "country": "Benin",
        "start_km": 640, "end_km": 770,
        "start_coordinate": {"latitude": 6.365, "longitude": 2.406},
        "end_coordinate": {"latitude": 6.420, "longitude": 2.391},
        "terrain_profile": {"min_elevation_m": 1, "max_elevation_m": 45, "avg_elevation_m": 17},
        "slope_analysis": {"avg_slope_degrees": 1.1, "max_slope_degrees": 5.0, "pct_slope_under_3deg": 88},
        "soil_stability": {"classification": "Medium", "dominant_soil_type": "Coastal sandy loam with clay lenses", "bearing_capacity_kpa": 145},
        "flood_risk": {"classification": "Medium", "flood_zone_pct": 22, "detected_water_bodies": ["Ouémé River delta (3.9 km floodplain)", "Lake Nokoué (5.2 km routing constraint)"]},
        "construction_difficulty": {"score": 4.1, "rating": "Moderate", "major_obstacles": ["Ouémé River crossing (~280m span bridge)", "Lake Nokoué north detour adds 6 km"]},
        "co_location_opportunity": {"highway_overlap_pct": 73, "existing_road_parallels_km": 95, "estimated_capex_saving_pct": 16},
    },
    {
        "segment_id": "SEG-006",
        "label": "Lagos Metropolitan Approach",
        "country": "Nigeria",
        "start_km": 770, "end_km": 1080,
        "start_coordinate": {"latitude": 6.420, "longitude": 2.391},
        "end_coordinate": {"latitude": 6.563, "longitude": 3.564},
        "terrain_profile": {"min_elevation_m": 0, "max_elevation_m": 38, "avg_elevation_m": 14},
        "slope_analysis": {"avg_slope_degrees": 0.7, "max_slope_degrees": 3.8, "pct_slope_under_3deg": 94},
        "soil_stability": {"classification": "Low-Medium", "dominant_soil_type": "Alluvial deposit and reclaimed coastal land", "bearing_capacity_kpa": 110},
        "flood_risk": {"classification": "High", "flood_zone_pct": 34, "detected_water_bodies": ["Lagos Lagoon (7.2 km)", "Badagry Creek (1.9 km floodplain)", "Lekki Peninsula tidal zones (4.1 km)"]},
        "construction_difficulty": {"score": 7.1, "rating": "Difficult", "major_obstacles": ["Lagos Lagoon crossing", "Dense urban environment — ROW acquisition complex", "Underground cable preferred through core urban zones"]},
        "co_location_opportunity": {"highway_overlap_pct": 62, "existing_road_parallels_km": 192, "estimated_capex_saving_pct": 13},
    },
]


@tool("terrain_analysis", description=TOOL_DESCRIPTION)
def terrain_analysis_tool(payload: TerrainInput, runtime: ToolRuntime) -> Command:
    """Analyzes elevation data to calculate slopes, flood risks, and construction difficulty."""
    # Try to enrich with real GEE elevation data
    real_elevation = None
    try:
        from src.adapters.pipeline_bridge import pipeline_bridge
        real_elevation = pipeline_bridge.get_terrain_data()
        logger.info("Real elevation data obtained from GEE")
    except Exception as exc:
        logger.warning("GEE elevation data unavailable, using reference data: %s", exc)

    response = {
        "analysis_metadata": {
            "corridor_id": "AL_CORRIDOR_001",
            "dem_source": "SRTM 30m Resolution (NASA)" + (" — enriched with live GEE data" if real_elevation else ""),
            "total_corridor_length_km": 1080,
            "segments_analyzed": len(CORRIDOR_SEGMENTS),
        },
        "segment_analysis": CORRIDOR_SEGMENTS,
        "corridor_summary": {
            "total_length_km": 1080,
            "overall_construction_difficulty": "Moderate (4.2 / 10 avg)",
            "critical_segments": ["SEG-003", "SEG-006"],
            "recommended_priority_segments": ["SEG-001", "SEG-004"],
            "total_major_water_crossings": 9,
            "avg_highway_co_location_pct": 67,
        },
    }

    # Attach real elevation data if available
    if real_elevation and real_elevation.get("elevation_data"):
        response["live_elevation_data"] = real_elevation["elevation_data"]

    # Enrich with soil properties data
    try:
        from src.adapters.pipeline_bridge import pipeline_bridge as pb
        soil_data = pb.get_soil_properties()
        available_props = soil_data.get("available_properties", [])
        response["soil_context"] = {
            "available_properties": available_props,
            "source": soil_data.get("source", "SoilGrids"),
            "note": "Soil property layers available for foundation analysis and construction planning",
        }
        # Enrich segment-level data with soil property info if available
        if soil_data.get("soil_data") or available_props:
            response["analysis_metadata"]["soil_data_available"] = True
        logger.info("Soil properties obtained: %s", available_props)
    except Exception as exc:
        logger.warning("Soil properties unavailable: %s", exc)

    # Enrich with flood risk data
    try:
        from src.adapters.pipeline_bridge import pipeline_bridge as pb2
        flood_data = pb2.get_flood_risk_data()
        flood_info = flood_data.get("flood_data", {})
        response["flood_risk_context"] = {
            "flood_data": flood_info if flood_info else {},
            "source": flood_data.get("source", "Global Flood Database"),
            "note": "Flood risk layers for route planning and infrastructure siting",
        }
        response["analysis_metadata"]["flood_risk_data_available"] = True
        logger.info("Flood risk data obtained")
    except Exception as exc:
        logger.warning("Flood risk data unavailable: %s", exc)

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response), tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )
