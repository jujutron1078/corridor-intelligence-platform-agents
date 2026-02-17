import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import PhasingInput


@tool("generate_phasing_strategy", description=TOOL_DESCRIPTION)
def generate_phasing_strategy_tool(
    payload: PhasingInput, runtime: ToolRuntime
) -> Command:
    """Generates a multi-phase construction plan for the infrastructure."""

    # In a real-world scenario, this tool would:
    # 1. Identify 'Quick Wins' where power can be deployed in 24 months.
    # 2. Sequence construction to match highway 'Lots' (segments).
    # 3. Schedule substation energization to match mining expansion dates.

    response = {
        "phasing_plan": [
            {
                "phase": 1,
                "years": "1-3",
                "segment": "Abidjan to Accra",
                "focus": "Anchor Connectivity",
            },
            {
                "phase": 2,
                "years": "3-6",
                "segment": "Accra to Lagos",
                "focus": "Regional Integration",
            },
        ],
        "message": "2-Phase strategy generated, aligned with Abidjan-Lagos highway Lots.",
    }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response), tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )
