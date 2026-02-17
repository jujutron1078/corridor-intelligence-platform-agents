from typing import Dict
from pydantic import BaseModel, Field


class ImpactTrackingInput(BaseModel):
    employment_data: Dict = Field(
        ..., description="Current job counts from site and industry."
    )
    electrification_data: Dict = Field(
        ..., description="New household connection counts."
    )
