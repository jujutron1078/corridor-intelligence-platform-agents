from typing import List
from pydantic import BaseModel, Field


class CurrentDemandInput(BaseModel):
    anchor_load_ids: List[str] = Field(
        ..., description="List of IDs from the anchor load scanner."
    )
    resource_type: str = Field(
        default="electricity",
        description="Type of demand to calculate (electricity/water)."
    )
