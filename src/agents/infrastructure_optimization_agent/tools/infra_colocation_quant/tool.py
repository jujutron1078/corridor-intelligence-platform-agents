import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("infra_colocation_quant", description=TOOL_DESCRIPTION)
def infra_colocation_quant_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: compute co-location overlap and savings band.
    """
    result = {
        "status": "ok",
        "step": "colocation_quant",
        "overlap_pct": 0.2,
        "savings_band_pct": [0.15, 0.25],
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

