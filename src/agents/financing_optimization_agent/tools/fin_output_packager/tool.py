import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("fin_output_packager", description=TOOL_DESCRIPTION)
def fin_output_packager_tool(_: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: model artifacts and KPIs manifest.
    """
    result = {
        "status": "ok",
        "step": "output_packager",
        "artifacts": ["scenarios.json", "recommended_structure.json"],
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

