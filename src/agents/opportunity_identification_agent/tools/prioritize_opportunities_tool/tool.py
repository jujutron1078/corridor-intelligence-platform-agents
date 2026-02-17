import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import PrioritizationInput


@tool("prioritize_opportunities", description=TOOL_DESCRIPTION)
def prioritize_opportunities_tool(
    payload: PrioritizationInput, runtime: ToolRuntime
) -> Command:
    """Ranks opportunities to guide the final phasing strategy."""

    # In a real-world scenario, this tool would:
    # 1. Run a Multi-Criteria Decision Analysis (MCDA).
    # 2. Weight Bankability (40%), Total Demand (30%), and Regional Impact (30%).
    # 3. Output a phased roadmap: Phase 1 (Quick Wins) vs Phase 2 (Catalytic).

    response = {
        "priority_list": [
            {"rank": 1, "id": "AL_ANC_042", "name": "Tarkwa Mine Hub", "score": 96.5},
            {"rank": 2, "id": "AL_ANC_001", "name": "Azito Expansion", "score": 94.2}
        ],
        "top_15_count": 15,
        "recommendation": "Phase 1 should focus on energy-intensive mining anchors to secure early ROI.",
        "message": "Priority catalog generated for stakeholder review."
    }

    return Command(
        update={
            "messages": [
                ToolMessage(content=json.dumps(response), tool_call_id=runtime.tool_call_id)
            ]
        }
    )
