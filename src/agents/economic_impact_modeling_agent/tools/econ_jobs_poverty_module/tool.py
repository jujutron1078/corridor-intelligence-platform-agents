import json

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("econ_jobs_poverty_module", description=TOOL_DESCRIPTION)
def econ_jobs_poverty_module_tool( runtime: ToolRuntime) -> Command:
    """
    Mock tool: estimate direct/indirect/induced jobs and poverty metrics.
    """
    result = {
        "status": "ok",
        "step": "jobs_poverty_module",
        "jobs_range": [200_000, 300_000],
        "poverty_metrics": {"people_lifted_out": [50_000, 100_000]},
        
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


