from langchain.agents import AgentState
from typing import Annotated, NotRequired

from .schema import Todo
from .utils import replace_todos_list


class GeospatialIntelligenceAgentState(AgentState):
    """State for the geospatial intelligence agent."""

    todos: Annotated[NotRequired[list[Todo]], replace_todos_list]
