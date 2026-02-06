from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage, HumanMessage
from langgraph.types import Command

from src.agents.financing_optimization_agent.agent import agent as fin_agent


@tool(
    "financing_optimization_agent",
    description=(
        "Use the Financing Optimization Agent to analyze the task and "
        "return the result."
    ),
)
async def financing_optimization_agent(
    task: str, runtime: ToolRuntime
) -> Command:
    response = await fin_agent.ainvoke({"messages": [HumanMessage(content=task)]})
    result = response["messages"][-1].content

    return Command(
        update={
            "messages": [
                ToolMessage(content=result, tool_call_id=runtime.tool_call_id)
            ]
        }
    )

