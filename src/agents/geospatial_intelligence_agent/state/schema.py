from typing import TypedDict, Literal


class Todo(TypedDict):
    """A single todo item with content and status."""

    content: str
    status: Literal["pending", "in_progress", "completed"]
