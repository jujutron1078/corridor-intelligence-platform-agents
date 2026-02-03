import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("stake_influence_graph", description=TOOL_DESCRIPTION)
def stake_influence_graph_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: build influence network and key pathways.
    """
    result = {
        "status": "ok",
        "step": "influence_graph_builder",
        "nodes": 170,
        "edges": 320,
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

