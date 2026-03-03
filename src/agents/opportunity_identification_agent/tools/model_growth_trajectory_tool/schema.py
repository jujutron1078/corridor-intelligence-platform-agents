from typing import List
from pydantic import BaseModel, Field


class GrowthTrajectoryInput(BaseModel):
    anchor_load_ids: List[str] = Field(
        ..., description="IDs to project."
    )
    horizon_years: int = Field(
        default=20, description="Forecast period."
    )
