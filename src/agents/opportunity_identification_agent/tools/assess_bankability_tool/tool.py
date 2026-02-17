import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import BankabilityInput


@tool("assess_bankability", description=TOOL_DESCRIPTION)
def assess_bankability_tool(
    payload: BankabilityInput, runtime: ToolRuntime
) -> Command:
    """Evaluates the financial strength and off-take readiness of each anchor load."""

    # In a real-world scenario, this tool would:
    # 1. Fetch credit ratings or financial health indicators for parent companies.
    # 2. Analyze 'Willingness to Pay' by comparing current diesel generation costs vs. proposed grid tariffs.
    # 3. Categorize loads into 'Tier 1' (Bankable) vs. 'Tier 2/3' (High Risk).

    response = {
        "bankability_scores": [
            {
                "anchor_id": "AL_ANC_042",
                "score": 0.94,
                "category": "Tier 1",
                "offtake_willingness": "High"
            }
        ],
        "corridor_average_score": 0.72,
        "message": "Bankability assessment complete; 12 Tier 1 anchors identified."
    }

    return Command(
        update={
            "messages": [
                ToolMessage(content=json.dumps(response), tool_call_id=runtime.tool_call_id)
            ]
        }
    )
