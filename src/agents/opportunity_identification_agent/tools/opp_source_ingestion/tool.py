import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("opp_source_ingestion", description=TOOL_DESCRIPTION)
def opp_source_ingestion_tool(task: str, runtime: ToolRuntime) -> Command:
    """
    Mock tool: pull registries, plans, and structured datasets.
    """
    result = {
        "status": "ok",
        "step": "source_ingestion",
        "sources": [
            "mock_business_registry",
            "mock_sez_list",
            "mock_mining_cadastre",
        ],
        "echo": task,
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

