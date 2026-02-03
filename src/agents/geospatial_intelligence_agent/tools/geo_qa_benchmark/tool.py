import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("geo_qa_benchmark", description=TOOL_DESCRIPTION)
def geo_qa_benchmark_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: QA against known sites; returns static precision/recall.
    """
    result = {
        "status": "ok",
        "step": "qa_benchmark",
        "metrics": {
            "precision": 0.9,
            "recall": 0.8,
            "f1": 0.847,
        },
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

