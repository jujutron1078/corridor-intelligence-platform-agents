import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import ImpactTrackingInput


@tool("track_economic_impact_kpis", description=TOOL_DESCRIPTION)
def track_economic_impact_kpis_tool(
    payload: ImpactTrackingInput, runtime: ToolRuntime
) -> Command:
    """Tracks actual development impact (Jobs, Electrification, GDP)."""

    # In a real-world scenario, this tool would:
    # 1. Pull data from national statistics offices for corridor-zone employment.
    # 2. Count new 'last-mile' connections enabled by the transmission backbone.
    # 3. Report 'Impact ROI' to DFI stakeholders.

    response = {
        "actual_impact_to_date": {
            "jobs_created": 4200,
            "variance_vs_projection": "+11%",
            "additional_people_electrified": 120000
        },
        "message": "Economic impact targets are being exceeded in the job creation category."
    }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response),
                    tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )
