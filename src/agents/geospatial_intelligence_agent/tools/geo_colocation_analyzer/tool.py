import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("geo_colocation_analyzer", description=TOOL_DESCRIPTION)
def geo_colocation_analyzer_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: compute co-location overlap vs existing ROW and savings band.
    """
    result = {
        "status": "ok",
        "step": "colocation_analyzer",
        "overlap_pct": 0.21,
        "savings_band_pct": [0.15, 0.25],
        
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

