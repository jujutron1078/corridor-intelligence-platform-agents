import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import MessagingInput


@tool("generate_tailored_messaging", description=TOOL_DESCRIPTION)
def generate_tailored_messaging_tool(
    payload: MessagingInput, runtime: ToolRuntime
) -> Command:
    """Produces customized messaging templates for outreach campaigns."""

    # In a real-world scenario, this tool would:
    # 1. Use an LLM to draft outreach emails, briefs, and social media posts.
    # 2. Align messaging with the specific 'Value Proposition' of the corridor for that entity.
    # 3. Translate technical findings into the 'language' of the specific stakeholder.

    response = {
        "messaging_package": {
            "core_narrative": "Sustainable Regional Prosperity",
            "specific_template": "Draft: Investment Brief for [Stakeholder_Name]",
            "key_data_points_to_emphasize": ["IRR 14%", "300k Jobs", "Colocation Savings"],
        },
        "message": "Tailored messaging generated for the selected stakeholder group.",
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
