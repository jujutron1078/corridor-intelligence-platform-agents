import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("stake_output_packager", description=TOOL_DESCRIPTION)
def stake_output_packager_tool(runtime: ToolRuntime) -> Command:
    """
    Mock tool: database, network, and playbook manifest.
    """
    result = {
        "status": "ok",
        "step": "output_packager",
        "artifacts": ["stakeholders.json", "network.json", "roadmap.json", "risks.json"],
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

