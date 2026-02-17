import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

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
    
    # Mocked 'Processed Data Points' returned to the Agent's state
    data_summary = {
        "topography": {
            "elevation_range_m": [0, 420],
            "average_slope_percent": 4.2,
            "high_relief_zones_detected": False
        },
        "environment": {
            "protected_area_count": 3,
            "critical_habitats": ["Lekki Conservation Centre", "Omo Forest Reserve"],
            "wetland_coverage_sqkm": 124.5
        },
        "existing_infrastructure": {
            "road_network_density": "High",
            "detected_power_lines_km": 142.0,
            "major_settlements_count": 12
        }
    }

    # The actual file paths that the NEXT tools (CV and Routing) will open
    layer_uris = {
        "satellite": f"s3://atlantis-platform/data/{payload.corridor_id}/sentinel_mosaic.tif",
        "dem": f"s3://atlantis-platform/data/{payload.corridor_id}/terrain_model.tif",
        "vector_constraints": f"s3://atlantis-platform/data/{payload.corridor_id}/constraints.geojson"
    }

    response = {
        "corridor_id": payload.corridor_id,
        "status": "Analysis Ready Data (ARD) Generated",
        "data_points": data_summary,  # This is what the LLM 'reads'
        "uris": layer_uris,           # This is what the next 'Tools' use
        "metadata": {
            "crs": "EPSG:4326",
            "clip_area_sqkm": 102430.0,
            "source_count": 147 # Reflecting the 147+ datasets from the guide
        }
    }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response), 
                    tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )