import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("geo_imagery_acquisition", description=TOOL_DESCRIPTION)
def geo_imagery_acquisition_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: fetch tiles for corridor and buffer.
    """
    result = {
        "status": "ok",
        "step": "imagery_acquisition",
        "tiles": [
            {"scene_id": "S2A_MOCK_001", "cloud_cover_pct": 5.0},
            {"scene_id": "S2B_MOCK_002", "cloud_cover_pct": 8.0},
        ],
        
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

