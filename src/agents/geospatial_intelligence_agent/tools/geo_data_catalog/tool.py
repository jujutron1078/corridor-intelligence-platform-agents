import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("geo_data_catalog", description=TOOL_DESCRIPTION)
def geo_data_catalog_tool(query: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: resolve dataset availability and latest timestamps.
    """
    result = {
        "status": "ok",
        "step": "data_catalog",
        "datasets": [
            {"id": "sentinel_2", "type": "imagery", "resolution_m": 10, "latest_timestamp": "2025-12-01"},
            {"id": "landsat_8", "type": "imagery", "resolution_m": 30, "latest_timestamp": "2025-11-15"},
            {"id": "osm_vector", "type": "vector", "layers": ["roads", "settlements", "landuse"]},
            {"id": "copernicus_dem", "type": "dem", "resolution_m": 30},
        ],
        "echo": query,
    }
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(result),
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )

