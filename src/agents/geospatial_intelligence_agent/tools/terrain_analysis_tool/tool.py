import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import TerrainInput


@tool("terrain_analysis", description=TOOL_DESCRIPTION)
def terrain_analysis_tool(payload: TerrainInput, runtime: ToolRuntime) -> Command:
    """
    Analyzes elevation data to calculate slopes, flood risks,
    and construction difficulty scores along the corridor.
    """

    # In a real-world scenario, this tool would:
    # 1. Access the Digital Elevation Model (DEM) clipped in Tool 3
    # 2. Run a 'Slope' algorithm to calculate the gradient between every pixel
    # 3. Generate a 'Cost Surface' (a map where steeper = more expensive)
    # 4. Identify drainage basins to predict flood-prone 'No-Go' zones

    response = {
        "analysis_metadata": {
            "tool_name": "terrain_analysis",
            "corridor_id": "ABIDJAN_LAGOS_CORRIDOR",
            "dem_source": "SRTM 30m Resolution (NASA)",
            "analysis_date": "2026-01-26",
            "crs": "EPSG:4326 (WGS84)",
            "total_corridor_length_km": 1080,
            "buffer_width_km": 50,
            "segments_analyzed": 6,
            "confidence_score": 0.91,
        },
        "segment_analysis": [
            {
                "segment_id": "SEG-001",
                "label": "Abidjan Coastal Plain",
                "country": "Côte d'Ivoire",
                "start_km": 0,
                "end_km": 180,
                "start_coordinate": {"latitude": 5.302, "longitude": -4.025},
                "end_coordinate": {"latitude": 5.110, "longitude": -2.900},
                "terrain_profile": {
                    "min_elevation_m": 4,
                    "max_elevation_m": 87,
                    "avg_elevation_m": 38,
                    "elevation_variance_m": 21,
                },
                "slope_analysis": {
                    "avg_slope_degrees": 1.4,
                    "max_slope_degrees": 6.2,
                    "pct_slope_under_3deg": 84,
                    "pct_slope_3_to_10deg": 14,
                    "pct_slope_over_10deg": 2,
                },
                "soil_stability": {
                    "classification": "High",
                    "dominant_soil_type": "Laterite over Precambrian bedrock",
                    "bearing_capacity_kpa": 280,
                    "erosion_risk": "Low",
                },
                "flood_risk": {
                    "classification": "Low",
                    "flood_zone_pct": 6,
                    "detected_water_bodies": ["Lagune Ebrié (3.2 km crossing)"],
                    "drainage_basin": "Southern Atlantic Coastal Drainage",
                    "100yr_flood_elevation_m": 12,
                },
                "construction_difficulty": {
                    "score": 2.1,
                    "rating": "Easy",
                    "major_obstacles": ["Lagune Ebrié water crossing"],
                    "estimated_earthworks_m3": 180000,
                },
                "co_location_opportunity": {
                    "highway_overlap_pct": 78,
                    "existing_road_parallels_km": 140,
                    "estimated_capex_saving_pct": 17,
                },
            },
            {
                "segment_id": "SEG-002",
                "label": "Ghana Western Coastal Strip",
                "country": "Ghana",
                "start_km": 180,
                "end_km": 370,
                "start_coordinate": {"latitude": 5.110, "longitude": -2.900},
                "end_coordinate": {"latitude": 5.666, "longitude": -0.044},
                "terrain_profile": {
                    "min_elevation_m": 3,
                    "max_elevation_m": 142,
                    "avg_elevation_m": 61,
                    "elevation_variance_m": 44,
                },
                "slope_analysis": {
                    "avg_slope_degrees": 3.7,
                    "max_slope_degrees": 18.4,
                    "pct_slope_under_3deg": 52,
                    "pct_slope_3_to_10deg": 36,
                    "pct_slope_over_10deg": 12,
                },
                "soil_stability": {
                    "classification": "Medium",
                    "dominant_soil_type": "Sandy Clay Loam with lateritic hardpan",
                    "bearing_capacity_kpa": 180,
                    "erosion_risk": "Medium — seasonal rainfall channels detected",
                },
                "flood_risk": {
                    "classification": "Medium",
                    "flood_zone_pct": 18,
                    "detected_water_bodies": [
                        "Pra River (1.8 km floodplain)",
                        "Ankobra River delta (4.1 km floodplain)",
                    ],
                    "drainage_basin": "Pra River Basin",
                    "100yr_flood_elevation_m": 28,
                },
                "construction_difficulty": {
                    "score": 4.8,
                    "rating": "Moderate",
                    "major_obstacles": [
                        "Pra River crossing (bridge required ~420m span)",
                        "Nzema Forest Reserve buffer zone (8 km re-route recommended)",
                    ],
                    "estimated_earthworks_m3": 390000,
                },
                "co_location_opportunity": {
                    "highway_overlap_pct": 65,
                    "existing_road_parallels_km": 124,
                    "estimated_capex_saving_pct": 14,
                },
            },
            {
                "segment_id": "SEG-003",
                "label": "Greater Accra & Volta Delta",
                "country": "Ghana",
                "start_km": 370,
                "end_km": 510,
                "start_coordinate": {"latitude": 5.666, "longitude": -0.044},
                "end_coordinate": {"latitude": 6.032, "longitude": 0.607},
                "terrain_profile": {
                    "min_elevation_m": 0,
                    "max_elevation_m": 58,
                    "avg_elevation_m": 22,
                    "elevation_variance_m": 14,
                },
                "slope_analysis": {
                    "avg_slope_degrees": 0.9,
                    "max_slope_degrees": 4.1,
                    "pct_slope_under_3deg": 91,
                    "pct_slope_3_to_10deg": 8,
                    "pct_slope_over_10deg": 1,
                },
                "soil_stability": {
                    "classification": "Low-Medium",
                    "dominant_soil_type": "Alluvial silt and deltaic clay",
                    "bearing_capacity_kpa": 95,
                    "erosion_risk": "High — active coastal erosion at 1.2m/year",
                },
                "flood_risk": {
                    "classification": "Critical",
                    "flood_zone_pct": 41,
                    "detected_water_bodies": [
                        "Volta River mouth (11.4 km delta crossing)",
                        "Keta Lagoon (6.8 km marshland zone)",
                        "Seasonal inundation zones (3 areas)",
                    ],
                    "drainage_basin": "Volta River Lower Basin",
                    "100yr_flood_elevation_m": 8,
                    "notes": "Marshland and deltaic soil detected via SAR imagery. Pile foundation likely required across 22 km of this segment.",
                },
                "construction_difficulty": {
                    "score": 8.3,
                    "rating": "Very Difficult",
                    "major_obstacles": [
                        "Volta River delta crossing — major bridge or elevated structure required",
                        "Keta Lagoon — elevated transmission towers with extended footings",
                        "Soft deltaic soils — standard tower foundations unsuitable",
                    ],
                    "estimated_earthworks_m3": 55000,
                    "special_foundation_required": True,
                    "special_foundation_type": "Bored pile foundations (25–35m depth)",
                },
                "co_location_opportunity": {
                    "highway_overlap_pct": 44,
                    "existing_road_parallels_km": 61,
                    "estimated_capex_saving_pct": 9,
                    "notes": "Limited co-location due to terrain constraints; highway also requires elevated structures",
                },
            },
            {
                "segment_id": "SEG-004",
                "label": "Togo Coastal Corridor",
                "country": "Togo",
                "start_km": 510,
                "end_km": 640,
                "start_coordinate": {"latitude": 6.137, "longitude": 1.222},
                "end_coordinate": {"latitude": 6.365, "longitude": 2.406},
                "terrain_profile": {
                    "min_elevation_m": 2,
                    "max_elevation_m": 71,
                    "avg_elevation_m": 29,
                    "elevation_variance_m": 18,
                },
                "slope_analysis": {
                    "avg_slope_degrees": 1.8,
                    "max_slope_degrees": 7.3,
                    "pct_slope_under_3deg": 76,
                    "pct_slope_3_to_10deg": 21,
                    "pct_slope_over_10deg": 3,
                },
                "soil_stability": {
                    "classification": "High",
                    "dominant_soil_type": "Ferralitic soil over Precambrian schist",
                    "bearing_capacity_kpa": 240,
                    "erosion_risk": "Low-Medium",
                },
                "flood_risk": {
                    "classification": "Low-Medium",
                    "flood_zone_pct": 11,
                    "detected_water_bodies": [
                        "Mono River floodplain (2.6 km)",
                        "Lake Togo coastal fringe (1.4 km diversion needed)",
                    ],
                    "drainage_basin": "Mono River Basin",
                    "100yr_flood_elevation_m": 18,
                },
                "construction_difficulty": {
                    "score": 3.2,
                    "rating": "Easy-Moderate",
                    "major_obstacles": [
                        "Mono River crossing (standard bridge ~180m span)",
                        "Lake Togo northern detour adds ~3.5 km to optimal path",
                    ],
                    "estimated_earthworks_m3": 145000,
                },
                "co_location_opportunity": {
                    "highway_overlap_pct": 81,
                    "existing_road_parallels_km": 105,
                    "estimated_capex_saving_pct": 18,
                },
            },
            {
                "segment_id": "SEG-005",
                "label": "Benin Coastal Plain",
                "country": "Benin",
                "start_km": 640,
                "end_km": 770,
                "start_coordinate": {"latitude": 6.365, "longitude": 2.406},
                "end_coordinate": {"latitude": 6.420, "longitude": 2.391},
                "terrain_profile": {
                    "min_elevation_m": 1,
                    "max_elevation_m": 45,
                    "avg_elevation_m": 17,
                    "elevation_variance_m": 11,
                },
                "slope_analysis": {
                    "avg_slope_degrees": 1.1,
                    "max_slope_degrees": 5.0,
                    "pct_slope_under_3deg": 88,
                    "pct_slope_3_to_10deg": 11,
                    "pct_slope_over_10deg": 1,
                },
                "soil_stability": {
                    "classification": "Medium",
                    "dominant_soil_type": "Coastal sandy loam with clay lenses",
                    "bearing_capacity_kpa": 145,
                    "erosion_risk": "Medium",
                },
                "flood_risk": {
                    "classification": "Medium",
                    "flood_zone_pct": 22,
                    "detected_water_bodies": [
                        "Ouémé River delta (3.9 km floodplain)",
                        "Lake Nokoué northern shoreline (5.2 km routing constraint)",
                    ],
                    "drainage_basin": "Ouémé River Basin",
                    "100yr_flood_elevation_m": 14,
                },
                "construction_difficulty": {
                    "score": 4.1,
                    "rating": "Moderate",
                    "major_obstacles": [
                        "Ouémé River crossing (~280m span bridge)",
                        "Lake Nokoué — route must pass north of lake (adds 6 km)",
                    ],
                    "estimated_earthworks_m3": 210000,
                },
                "co_location_opportunity": {
                    "highway_overlap_pct": 73,
                    "existing_road_parallels_km": 95,
                    "estimated_capex_saving_pct": 16,
                },
            },
            {
                "segment_id": "SEG-006",
                "label": "Lagos Metropolitan Approach",
                "country": "Nigeria",
                "start_km": 770,
                "end_km": 1080,
                "start_coordinate": {"latitude": 6.420, "longitude": 2.391},
                "end_coordinate": {"latitude": 6.563, "longitude": 3.564},
                "terrain_profile": {
                    "min_elevation_m": 0,
                    "max_elevation_m": 38,
                    "avg_elevation_m": 14,
                    "elevation_variance_m": 9,
                },
                "slope_analysis": {
                    "avg_slope_degrees": 0.7,
                    "max_slope_degrees": 3.8,
                    "pct_slope_under_3deg": 94,
                    "pct_slope_3_to_10deg": 5,
                    "pct_slope_over_10deg": 1,
                },
                "soil_stability": {
                    "classification": "Low-Medium",
                    "dominant_soil_type": "Alluvial deposit and reclaimed coastal land",
                    "bearing_capacity_kpa": 110,
                    "erosion_risk": "High — active urban development accelerating runoff",
                },
                "flood_risk": {
                    "classification": "High",
                    "flood_zone_pct": 34,
                    "detected_water_bodies": [
                        "Lagos Lagoon crossing (7.2 km — major engineering challenge)",
                        "Badagry Creek (1.9 km floodplain)",
                        "Lekki Peninsula tidal zones (4.1 km)",
                    ],
                    "drainage_basin": "Lagos Coastal Drainage System",
                    "100yr_flood_elevation_m": 6,
                    "notes": "Urban heat island and impervious surface cover is 68% in this segment, significantly increasing surface runoff and flood risk.",
                },
                "construction_difficulty": {
                    "score": 7.1,
                    "rating": "Difficult",
                    "major_obstacles": [
                        "Lagos Lagoon crossing — sub-marine cable or long bridge structure required",
                        "Dense urban environment — ROW acquisition in Lekki will be complex",
                        "Underground cable likely preferred through core urban zones (higher cost)",
                    ],
                    "estimated_earthworks_m3": 270000,
                    "underground_cable_recommended_km": 38,
                },
                "co_location_opportunity": {
                    "highway_overlap_pct": 62,
                    "existing_road_parallels_km": 192,
                    "estimated_capex_saving_pct": 13,
                    "notes": "Strong co-location with Lekki-Epe Expressway expansion and port access roads near Dangote Refinery",
                },
            },
        ],
        "corridor_summary": {
            "total_length_km": 1080,
            "overall_construction_difficulty": "Moderate (4.2 / 10 avg)",
            "critical_segments": ["SEG-003", "SEG-006"],
            "recommended_priority_segments": ["SEG-001", "SEG-004"],
            "total_flood_zone_km": 184,
            "total_major_water_crossings": 9,
            "total_excavation_estimate_m3": 1250000,
            "total_special_foundations_required_km": 22,
            "avg_highway_co_location_pct": 67,
            "estimated_total_capex_saving_from_colocation_pct": 15,
        },
        "engineering_recommendations": [
            {
                "priority": "Critical",
                "segment": "SEG-003",
                "recommendation": "Volta River delta crossing requires elevated pile-supported transmission towers (25–35m bored piles). Re-route 8 km north of Keta Lagoon to bypass marshland. Budget for special foundations across 22 km.",
            },
            {
                "priority": "Critical",
                "segment": "SEG-006",
                "recommendation": "Lagos Lagoon requires submarine cable or dedicated bridge attachment. Recommend underground XLPE cable for 38 km through Lekki urban core to avoid ROW conflicts with Dangote Refinery development.",
            },
            {
                "priority": "High",
                "segment": "SEG-002",
                "recommendation": "Divert 8 km north of Nzema Forest Reserve boundary. Pra River crossing requires 420m span bridge — coordinate with highway authority for shared structure.",
            },
            {
                "priority": "Medium",
                "segment": "SEG-005",
                "recommendation": "Route north of Lake Nokoué adds 6 km but avoids unstable delta soils. Align with N1 highway corridor to maximize co-location savings.",
            },
            {
                "priority": "Opportunity",
                "segment": "SEG-001",
                "recommendation": "Abidjan coastal plain is the lowest-risk segment. Recommend starting construction here to generate early revenue from CIPREL/Azito interconnection while complex segments are being designed.",
            },
        ],
        "no_go_zones": [
            {
                "zone_id": "NGZ-001",
                "description": "Keta Lagoon Marshland",
                "coordinates": {"latitude": 5.92, "longitude": 0.98},
                "radius_km": 6.8,
                "reason": "Saturated deltaic soil — unstable for tower foundations; protected wetland designation",
            },
            {
                "zone_id": "NGZ-002",
                "description": "Nzema Forest Reserve (Core Zone)",
                "coordinates": {"latitude": 4.996, "longitude": -2.788},
                "radius_km": 12.0,
                "reason": "Protected forest reserve — environmental permit unlikely; high biodiversity value",
            },
            {
                "zone_id": "NGZ-003",
                "description": "Lekki Conservation Centre Buffer",
                "coordinates": {"latitude": 6.452, "longitude": 3.558},
                "radius_km": 3.5,
                "reason": "Protected wetland; National Park designation — route must pass north",
            },
        ],
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
