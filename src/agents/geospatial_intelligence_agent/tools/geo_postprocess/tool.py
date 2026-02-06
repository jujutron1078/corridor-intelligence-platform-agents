import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("geo_postprocess", description=TOOL_DESCRIPTION)
def geo_postprocess_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: deduplicate, vectorize footprints, assign confidence, snap to networks.
    """
    result = {
        "status": "ok",
        "step": "postprocess",
        "vector_detections_count": 3,
        
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

