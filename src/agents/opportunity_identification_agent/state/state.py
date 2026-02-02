from langchain.agents import AgentState
from typing import Annotated, NotRequired

from .schema import Todo
from .utils import replace_todos_list


class OpportunityIdentificationAgentState(AgentState):
    """State for the opportunity identification agent."""

    todos: Annotated[NotRequired[list[Todo]], replace_todos_list]
