from langchain.agents import AgentState
from typing import Annotated, NotRequired

from .schema import Todo
from .utils import replace_todos_list


class EconomicImpactModelingAgentState(AgentState):
    """State for the economic impact modeling agent."""

    todos: Annotated[NotRequired[list[Todo]], replace_todos_list]
