from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage, HumanMessage
from langgraph.types import Command

from src.agents.realtime_monitoring_agent.agent import agent as rt_agent


@tool(
    "realtime_monitoring_agent",
    description=(
        "Use the Realtime Monitoring Agent to analyze the task and "
        "return the result."
    ),
)
async def realtime_monitoring_agent(
    task: str, runtime: ToolRuntime
) -> Command:
    response = await rt_agent.ainvoke({"messages": [HumanMessage(content=task)]})
    result = response["messages"][-1].content

    return Command(
        update={
            "messages": [
                ToolMessage(content=result, tool_call_id=runtime.tool_call_id)
            ]
        }
    )

