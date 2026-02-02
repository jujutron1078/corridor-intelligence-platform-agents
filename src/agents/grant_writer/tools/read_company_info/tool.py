from langchain.tools import tool, ToolRuntime
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from langchain.chat_models import init_chat_model

from src.shared.utils.company_info import load_company_info_text
from .description import READ_COMPANY_INFO_DESCRIPTION
from .prompt import READ_COMPANY_INFO_QA_PROMPT


# Initialize the LLM (used only when a query is provided)
llm = init_chat_model(
    model="openai:gpt-5.2",
    streaming=False,
)


@tool(description=READ_COMPANY_INFO_DESCRIPTION)
def read_company_info(query: str, runtime: ToolRuntime) -> Command:
    """
    Retrieve company information for the current organization (from runtime context).

    - If `query` is provided: return a concise answer grounded in the company info.
    """
    org_name = getattr(runtime.context, "organization_name", "") or ""
    company_text = load_company_info_text(org_name)

    if not company_text:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=(
                            f"No company information found for organization {org_name!r}. "
                            f"Please create  the company information file in the company_information directory"
                        ),
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )

    messages = [
        {
            "role": "system",
            "content": READ_COMPANY_INFO_QA_PROMPT,
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"Company information: {company_text}"},
                {"type": "text", "text": f"Please answer the following question using the company information: {query}"},
            ],
        }
    ]
    
    response = llm.invoke(
        messages
    )

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=response.content,
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )

