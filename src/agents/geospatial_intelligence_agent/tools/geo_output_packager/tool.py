import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("geo_output_packager", description=TOOL_DESCRIPTION)
def geo_output_packager_tool(_: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: produce final GeoJSON/raster artifact manifest.
    """
    result = {
        "status": "ok",
        "step": "output_packager",
        "artifacts": ["detections.geojson", "routes.geojson", "constraints.json"],
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

