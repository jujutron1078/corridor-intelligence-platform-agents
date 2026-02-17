import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import AdaptiveRecommendationsInput


@tool("generate_adaptive_recommendations", description=TOOL_DESCRIPTION)
def generate_adaptive_recommendations_tool(
    payload: AdaptiveRecommendationsInput, runtime: ToolRuntime
) -> Command:
    """Provides actionable advice for course correction and optimization."""

    # In a real-world scenario, this tool would:
    # 1. Suggest 'Resource Leveling' if one segment is faster than another.
    # 2. Recommend 'Revenue Mitigation' (e.g., finding a new anchor load if one fails).
    # 3. Advice on 'Regulatory Engagement' for specific country bottlenecks.

    response = {
        "recommendations": [
            "Accelerate Phase 2 completion to capture early demand (Potential: +$8M/yr).",
            "Engage Benin environmental regulator proactively to resolve Phase 3 permits.",
            "Explore replacement anchor load (100 MW) in Togo to offset mining delay."
        ],
        "message": "3 strategic recommendations generated to optimize corridor ROI."
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
