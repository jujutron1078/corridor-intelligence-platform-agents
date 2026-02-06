import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("econ_baseline_builder", description=TOOL_DESCRIPTION)
def econ_baseline_builder_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: assemble corridor baseline GDP, jobs, poverty, sector shares.
    """
    result = {
        "status": "ok",
        "step": "baseline_builder",
        "baseline": {
            "gdp_usd_b": 12.5,
            "jobs": 500_000,
            "poverty_rate": 0.35,
        },
        
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


