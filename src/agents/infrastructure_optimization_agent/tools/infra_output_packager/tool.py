import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("infra_output_packager", description=TOOL_DESCRIPTION)
def infra_output_packager_tool(runtime: ToolRuntime) -> Command:
    """
    Mock tool: route book, segment table, and CAPEX/OPEX dataset manifest.
    """
    result = {
        "status": "ok",
        "step": "output_packager",
        "artifacts": ["recommended_routes.json", "substations.json", "phasing.json"],
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

