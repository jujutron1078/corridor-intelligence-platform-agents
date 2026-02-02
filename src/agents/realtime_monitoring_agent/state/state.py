from langchain.agents import AgentState
from typing import Annotated, NotRequired

from .schema import Todo
from .utils import replace_todos_list


class RealtimeMonitoringAgentState(AgentState):
    """State for the real-time monitoring agent."""

    todos: Annotated[NotRequired[list[Todo]], replace_todos_list]
