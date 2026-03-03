from typing import List

from pydantic import BaseModel, Field


class MessagingInput(BaseModel):
    stakeholder_type: str = Field(
        ..., description="e.g., DFI, Local Community, Mining CEO."
    )
    key_interests: List[str] = Field(
        ..., description="Interest data from Tool 1/2."
    )
