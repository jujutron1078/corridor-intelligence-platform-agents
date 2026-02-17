import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import EngagementRoadmapInput


@tool("generate_engagement_roadmap", description=TOOL_DESCRIPTION)
def generate_engagement_roadmap_tool(
    payload: EngagementRoadmapInput, runtime: ToolRuntime
) -> Command:
    """Creates a 4-phase engagement roadmap aligned with the project lifecycle."""

    # In a real-world scenario, this tool would:
    # 1. Prioritize 'High Influence / High Interest' stakeholders for Phase 1.
    # 2. Schedule community consultations to align with Environmental Impact milestones.
    # 3. Define specific KPIs for each engagement phase.

    response = {
        "roadmap": {
            "phase_1": {"months": "1-4", "target": "32 Champions", "focus": "Buy-in"},
            "phase_2": {"months": "5-10", "target": "68 Private/Utility", "focus": "Off-take"},
            "phase_3": {"months": "11-18", "target": "55 Communities", "focus": "Social License"},
            "phase_4": {"months": "19-24", "target": "25 Regulators", "focus": "Final Approval"},
        },
        "message": "Engagement roadmap generated; 4-phase sequence finalized.",
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
