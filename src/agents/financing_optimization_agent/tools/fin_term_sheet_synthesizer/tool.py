import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("fin_term_sheet_synthesizer", description=TOOL_DESCRIPTION)
def fin_term_sheet_synthesizer_tool(config: dict, runtime: ToolRuntime) -> Command:
    """
    Mock tool: generate recommended structure and rationale.
    """
    result = {
        "status": "ok",
        "step": "term_sheet_synthesizer",
        "summary": "Mock blended finance structure summary.",
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

