from typing import Dict, List

from pydantic import BaseModel, Field


class EmploymentModelingInput(BaseModel):
    anchor_load_portfolio: List[Dict] = Field(
        ..., description="Portfolio from Agent 2."
    )
    construction_duration_years: int = Field(default=5)

