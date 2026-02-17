import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import ConstructionProgressInput


@tool("track_construction_progress", description=TOOL_DESCRIPTION)
def track_construction_progress_tool(
    payload: ConstructionProgressInput, runtime: ToolRuntime
) -> Command:
    """Calculates physical completion percentage across all project phases."""

    # In a real-world scenario, this tool would:
    # 1. Compare 'Planned vs. Actual' (S-Curves) for civil and electrical works.
    # 2. Integrate satellite imagery change detection to verify ground reports.
    # 3. Aggregate progress across multiple contractors in different countries.

    response = {
        "overall_progress": "45%",
        "phase_breakdown": {
            "Phase 1 (Abidjan-Accra)": "90%",
            "Phase 2 (Accra-Lome)": "40%",
            "Phase 3 (Lome-Lagos)": "10%"
        },
        "milestones": "Substation ABJ-01 commissioned; 450km of 400kV line strung.",
        "status": "On Track",
        "message": "Construction monitoring updated. Phase 1 nearing completion."
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
