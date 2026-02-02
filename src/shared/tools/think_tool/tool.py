from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import THINK_TOOL_DESCRIPTION


@tool(description=THINK_TOOL_DESCRIPTION)
def think_tool(
    reflection: str,
    runtime: ToolRuntime,
) -> Command:
    """
    Reflect on the results of each delegated task and plan next steps.
    """
    messages = runtime.state.get("messages", [])
    new_messages = list(messages)

    tool_message = ToolMessage(
        content=reflection,
        tool_call_id=runtime.tool_call_id,
    )
    new_messages.append(tool_message)

    return Command(update={"messages": new_messages})
