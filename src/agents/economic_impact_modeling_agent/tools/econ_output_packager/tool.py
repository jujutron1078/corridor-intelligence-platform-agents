import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("econ_output_packager", description=TOOL_DESCRIPTION)
def econ_output_packager_tool(_: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: package results dataset and narrative-ready summary.
    """
    result = {
        "status": "ok",
        "step": "output_packager",
        "artifacts": ["baseline.json", "impacts.json", "scenarios.json"],
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


