from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage, HumanMessage
from langgraph.types import Command

from src.agents.economic_impact_modeling_agent.agent import agent as econ_agent


@tool(
    "economic_impact_modeling_agent",
    description=(
        "Use the Economic Impact Modeling Agent to analyze the task and "
        "return the result."
    ),
)
async def economic_impact_modeling_agent(
    task: str, runtime: ToolRuntime
) -> Command:
    response = await econ_agent.ainvoke({"messages": [HumanMessage(content=task)]})
    result = response["messages"][-1].content

    return Command(
        update={
            "messages": [
                ToolMessage(content=result, tool_call_id=runtime.tool_call_id)
            ]
        }
    )

