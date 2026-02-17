import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import SentimentTrackingInput


@tool("track_engagement_sentiment", description=TOOL_DESCRIPTION)
def track_engagement_sentiment_tool(
    payload: SentimentTrackingInput, runtime: ToolRuntime
) -> Command:
    """Monitors real-time sentiment and flags shifts in stakeholder support."""

    # In a real-world scenario, this tool would:
    # 1. Monitor local news feeds in French (Cote d'Ivoire) and English (Ghana/Nigeria).
    # 2. Score 'Sentiment' from -1.0 (Opposed) to +1.0 (Strong Support).
    # 3. Update the engagement status (e.g., 'Not Contacted' -> 'Supportive').

    response = {
        "sentiment_trends": {
            "government_support": 0.85,
            "community_sentiment": 0.42,
            "private_sector_excitement": 0.78,
        },
        "alert": "Community sentiment dropped in Region X; review land-use communication.",
        "message": "Real-time stakeholder intelligence dashboard updated.",
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
