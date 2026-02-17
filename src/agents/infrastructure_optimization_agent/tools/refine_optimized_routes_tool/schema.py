from typing import Dict, List

from pydantic import BaseModel, Field


class RouteRefinementInput(BaseModel):
    geospatial_variants: List[Dict] = Field(
        ..., description="Route variants from Agent 1."
    )
    corridor_proximity_limit_m: float = Field(
        default=500.0, description="Max distance from highway center-line."
    )
