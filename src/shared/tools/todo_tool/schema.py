from pydantic import BaseModel, Field
from typing import Literal


class TodoItem(BaseModel):
    """
    A single todo item.
    """

    content: str = Field(description="Task description.")
    status: Literal["pending", "in_progress", "completed"] = Field(description="Task status.")
