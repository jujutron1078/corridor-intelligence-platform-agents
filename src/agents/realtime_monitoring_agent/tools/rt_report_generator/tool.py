import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("rt_report_generator", description=TOOL_DESCRIPTION)
def rt_report_generator_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: generate DFI-compliant reports and dashboard refresh.
    """
    result = {
        "status": "ok",
        "step": "report_generator",
        "artifacts": ["dfi_report.pdf", "internal_dashboard_snapshot.json"],
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

