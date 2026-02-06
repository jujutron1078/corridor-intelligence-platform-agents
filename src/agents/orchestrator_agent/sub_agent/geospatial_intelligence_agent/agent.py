from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage, HumanMessage
from langgraph.types import Command

from src.agents.geospatial_intelligence_agent.agent import agent as geo_agent


@tool(
    "geospatial_intelligence_agent",
    description=(
        "Use the Geospatial Intelligence Agent to analyze the task and "
        "return the result."
    ),
)
async def geospatial_intelligence_agent(
    task: str, runtime: ToolRuntime
) -> Command:
    response = await geo_agent.ainvoke({"messages": [HumanMessage(content=task)]})
    result = response["messages"][-1].content

    return Command(
        update={
            "messages": [
                ToolMessage(content=result, tool_call_id=runtime.tool_call_id)
            ]
        }
    )

