import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("rt_satellite_monitoring", description=TOOL_DESCRIPTION)
def rt_satellite_monitoring_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: detect construction progress and anomalies from satellite.
    """
    result = {
        "status": "ok",
        "step": "satellite_monitoring",
        "construction_activity_detected": True,
        
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

