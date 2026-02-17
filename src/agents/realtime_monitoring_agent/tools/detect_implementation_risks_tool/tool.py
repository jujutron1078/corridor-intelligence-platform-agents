import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import RiskDetectionInput


@tool("detect_implementation_risks", description=TOOL_DESCRIPTION)
def detect_implementation_risks_tool(
    payload: RiskDetectionInput, runtime: ToolRuntime
) -> Command:
    """Flags anomalies and predicts potential project delays or cost overruns."""

    # In a real-world scenario, this tool would:
    # 1. Run statistical models to detect 'Schedule Slippage' trends.
    # 2. Flag 'Permit Stalls' by monitoring the time spent in regulatory queues.
    # 3. Detect 'Revenue Shortfalls' if anchor load ramp-up is slower than modeled.

    response = {
        "active_alerts": [
            {
                "severity": "MODERATE",
                "risk": "Anchor Load X delay",
                "impact": "-$3M Revenue Y4"
            },
            {
                "severity": "LOW",
                "risk": "Permit delay in Benin (Phase 3)",
                "impact": "3-month slip"
            }
        ],
        "resolved_risks": ["Currency volatility (Hedged)"],
        "message": "Early warning system identified 2 active risks for management attention."
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
