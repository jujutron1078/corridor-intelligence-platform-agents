import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import StakeholderRiskInput


@tool("assess_stakeholder_risks", description=TOOL_DESCRIPTION)
def assess_stakeholder_risks_tool(
    payload: StakeholderRiskInput, runtime: ToolRuntime
) -> Command:
    """Populates a Risk Register with political, social, and coordination risks."""

    # In a real-world scenario, this tool would:
    # 1. Perform sentiment analysis on public statements from local NGOs.
    # 2. Identify 'Coordination Risks' between cross-border regulators.
    # 3. Flag 'Conflicts of Interest' in land-use and SEZ ownership.

    response = {
        "risk_register": [
            {
                "risk": "Cross-border regulatory misalignment",
                "level": "High",
                "mitigation": "WAPP-led harmonization",
            },
            {
                "risk": "Community displacement opposition",
                "level": "Medium",
                "mitigation": "Early CSR investment",
            },
        ],
        "message": "Risk assessment complete; 12 critical social/political risks identified.",
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
