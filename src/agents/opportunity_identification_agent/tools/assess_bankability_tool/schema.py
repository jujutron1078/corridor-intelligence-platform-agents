from typing import List
from pydantic import BaseModel, Field


class BankabilityInput(BaseModel):
    anchor_load_ids: List[str] = Field(
        ..., description="IDs of the companies to be scored."
    )
