import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("infra_tech_spec_generator", description=TOOL_DESCRIPTION)
def infra_tech_spec_generator_tool(runtime: ToolRuntime) -> Command:
    """
    Mock tool: generate high-level technical specs and BOQ-lite.
    """
    result = {
        "status": "ok",
        "step": "tech_spec_generator",
        "voltage_kv": 400,
        "capacity_mw": 1500,
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

