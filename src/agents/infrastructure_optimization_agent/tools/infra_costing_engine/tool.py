import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("infra_costing_engine", description=TOOL_DESCRIPTION)
def infra_costing_engine_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: compute CAPEX/OPEX ranges and contingencies.
    """
    result = {
        "status": "ok",
        "step": "costing_engine",
        "capex_range_usd_m": [730, 1005],
        "opex_range_usd_m_per_year": [15, 25],
        
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

