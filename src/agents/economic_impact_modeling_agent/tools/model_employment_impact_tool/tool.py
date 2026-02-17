import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import EmploymentModelingInput


@tool("model_employment_impact", description=TOOL_DESCRIPTION)
def model_employment_impact_tool(
    payload: EmploymentModelingInput, runtime: ToolRuntime
) -> Command:
    """Estimates job creation across construction and operations phases."""

    # In a real-world scenario, this tool would:
    # 1. Estimate direct construction jobs based on labor-to-CAPEX ratios.
    # 2. Project 'Enabled' jobs in the 57 anchor loads (e.g., workers needed for a new mine).
    # 3. Use employment elasticities to calculate 'Induced' jobs in the local service economy.

    response = {
        "employment_summary": {
            "direct_construction_jobs": 75000,
            "direct_operational_jobs": 12000,
            "enabled_industrial_jobs": 145000,
            "induced_jobs": 68000,
        },
        "total_jobs_created": 300000,
        "message": "Employment projection based on current corridor industrial portfolio.",
    }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response), tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )
