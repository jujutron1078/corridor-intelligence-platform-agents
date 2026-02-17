import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import StakeholderMappingInput


@tool("map_stakeholder_ecosystem", description=TOOL_DESCRIPTION)
def map_stakeholder_ecosystem_tool(
    payload: StakeholderMappingInput, runtime: ToolRuntime
) -> Command:
    """Identifies and categorizes all relevant stakeholders in the corridor ecosystem."""

    # In a real-world scenario, this tool would:
    # 1. Query gov.af and regional portals for ministry and regulatory leads.
    # 2. Extract board-level and program officer contacts for matched DFIs.
    # 3. Identify local community leaders and NGOs based on the physical route coordinates.

    response = {
        "status": "Mapping Complete",
        "stakeholder_counts": {
            "governments": 38,
            "dfis": 18,
            "utilities": 12,
            "private_sector": 55,
            "civil_society": 25,
            "regional_bodies": 12,
        },
        "total_identified": 160,
        "message": "Stakeholder database populated for all 5 corridor countries.",
    }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response),
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )
