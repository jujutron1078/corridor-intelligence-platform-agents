from pydantic import BaseModel, Field
from typing import Literal


class TodoItem(BaseModel):
    """
    A single todo item with id, label, status, and description.
    """

    id: str = Field(description="Unique identifier for the task (e.g. '1', '2').")
    label: str = Field(description="Short task title or name.")
    status: Literal["pending", "in_progress", "completed"] = Field(
        description="Task status: pending, in_progress, or completed."
    )
    description: str = Field(
        description="Description or outcome (e.g. what was done for completed tasks; can be empty for pending).",
    )