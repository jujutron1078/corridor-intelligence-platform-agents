import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import AnchorRealizationInput


@tool("audit_anchor_load_realization", description=TOOL_DESCRIPTION)
def audit_anchor_load_realization_tool(
    payload: AnchorRealizationInput, runtime: ToolRuntime
) -> Command:
    """Verifies commercial uptake by tracking anchor load load-factors."""

    # In a real-world scenario, this tool would:
    # 1. Reconcile utility billing data with the original Anchor Load catalog.
    # 2. Flag 'Ghost Anchors' (loads that were projected but haven't connected).
    # 3. Analyze load factors for industrial zones to optimize future capacity expansion.

    response = {
        "realization_metrics": {
            "anchors_online": "28 of 45",
            "capacity_realized_mw": 950,
            "target_mw": 2650
        },
        "notable_delays": ["Anchor Load X (Mining) delayed by 6 months"],
        "message": "Anchor load realization at 62% of Phase 1 targets."
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
