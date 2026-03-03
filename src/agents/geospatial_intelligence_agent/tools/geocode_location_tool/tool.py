import json
from datetime import datetime, timezone
from pathlib import Path

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import GeocodeLocationInput




@tool("geocode_location", description=TOOL_DESCRIPTION)
def geocode_location_tool(
    payload: GeocodeLocationInput, runtime: ToolRuntime
) -> Command:
    """
    Mock tool: resolve place names to coordinates. Returns mock lat/lon/confidence.
    Dumps result to workspaces/{project_id}/project_data/ when project_id is set.
    """
    response = {
        "resolved_locations": [
            {
                "input_name": "Abidjan",
                "latitude": 5.359951,
                "longitude": -4.008256,
                "confidence": 0.97,
            },
            {
                "input_name": "Lagos",
                "latitude": 6.524379,
                "longitude": 3.379206,
                "confidence": 0.96,
            },
        ]
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
