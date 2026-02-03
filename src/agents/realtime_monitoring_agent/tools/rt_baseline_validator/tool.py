import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("rt_baseline_validator", description=TOOL_DESCRIPTION)
def rt_baseline_validator_tool(payload: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: ingest baselines from Geo/Infra/Econ/Finance and validate.
    """
    result = {
        "status": "ok",
        "step": "baseline_validator",
        "baseline_version_id": "baseline_mock_v1",
        "echo": payload,
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

