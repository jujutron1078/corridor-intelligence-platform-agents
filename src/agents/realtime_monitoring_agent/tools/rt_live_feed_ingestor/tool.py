import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("rt_live_feed_ingestor", description=TOOL_DESCRIPTION)
def rt_live_feed_ingestor_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: pull progress, cost, and timeline updates.
    """
    result = {
        "status": "ok",
        "step": "live_feed_ingestor",
        "feeds": ["schedule", "costs", "throughput"],
        "echo": config,
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

