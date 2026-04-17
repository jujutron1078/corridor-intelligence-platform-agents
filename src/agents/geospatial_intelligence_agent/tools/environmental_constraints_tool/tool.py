import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import EnvironmentalInput

logger = logging.getLogger("corridor.agent.geospatial.environmental")

# Known no-go zones along the corridor (expert-assessed reference data)
CORRIDOR_NO_GO_ZONES = [
    {
        "zone_id": "NGZ-001",
        "name": "Ankasa Conservation Area",
        "type": "National Park (IUCN II)",
        "country": "Ghana",
        "coordinates": {"latitude": 5.244, "longitude": -2.636},
        "area_sqkm": 509.0,
        "buffer_meters": 500,
        "reason": "Protected rainforest — highest biodiversity priority in Ghana",
    },
    {
        "zone_id": "NGZ-002",
        "name": "Nzema Forest Reserve",
        "type": "Forest Reserve (IUCN VI)",
        "country": "Ghana",
        "coordinates": {"latitude": 4.996, "longitude": -2.788},
        "area_sqkm": 182.3,
        "buffer_meters": 500,
        "reason": "Protected forest reserve — environmental permit unlikely",
    },
    {
        "zone_id": "NGZ-003",
        "name": "Keta Lagoon Marshland",
        "type": "Wetland (Ramsar)",
        "country": "Ghana",
        "coordinates": {"latitude": 5.92, "longitude": 0.98},
        "area_sqkm": 128.0,
        "buffer_meters": 1000,
        "reason": "Ramsar wetland — saturated deltaic soil, unstable for tower foundations",
    },
    {
        "zone_id": "NGZ-004",
        "name": "Lekki Conservation Centre",
        "type": "Conservation Area (IUCN IV)",
        "country": "Nigeria",
        "coordinates": {"latitude": 6.452, "longitude": 3.558},
        "area_sqkm": 78.2,
        "buffer_meters": 500,
        "reason": "Protected wetland, National Park designation — route must pass north",
    },
    {
        "zone_id": "NGZ-005",
        "name": "Mono River Biosphere",
        "type": "Biosphere Reserve (UNESCO)",
        "country": "Togo/Benin",
        "coordinates": {"latitude": 6.25, "longitude": 1.65},
        "area_sqkm": 346.0,
        "buffer_meters": 500,
        "reason": "Trans-boundary biosphere — crossing permitted with EIA only",
    },
]


@tool("environmental_constraints", description=TOOL_DESCRIPTION)
def environmental_constraints_tool(
    payload: EnvironmentalInput, runtime: ToolRuntime
) -> Command:
    """Identifies protected areas, wetlands, and no-go zones along the corridor."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    # Get real protected areas and forest data from GEE
    real_constraints = None
    try:
        real_constraints = pipeline_bridge.get_environmental_constraints()
        logger.info("Real environmental constraint data obtained from GEE")
    except Exception as exc:
        logger.warning("GEE constraint data unavailable: %s", exc)

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "status": "Environmental Audit Complete",
        "no_go_zones": CORRIDOR_NO_GO_ZONES,
        "no_go_zone_count": len(CORRIDOR_NO_GO_ZONES),
        "buffer_zone_meters": payload.buffer_zone_meters,
    }

    if real_constraints:
        response["protected_areas_gee"] = real_constraints.get("protected_areas")
        response["forest_cover_gee"] = real_constraints.get("forest_cover")
        response["data_source"] = "WDPA + Hansen Global Forest Change (live GEE)"
    else:
        response["data_source"] = "Expert-assessed reference data (GEE unavailable)"

    # Enrich with flood zone constraints
    try:
        flood_data = pipeline_bridge.get_flood_risk_data()
        flood_info = flood_data.get("flood_data", {})
        response["flood_constraints"] = {
            "flood_zones": flood_info if flood_info else {},
            "source": flood_data.get("source", "Global Flood Database"),
            "note": "Flood-prone zones to avoid or mitigate in route planning",
        }
        response["data_source"] += " + Global Flood Database"
        logger.info("Flood risk constraint data obtained")
    except Exception as exc:
        logger.warning("Flood risk data unavailable for constraints: %s", exc)

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response), tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )
