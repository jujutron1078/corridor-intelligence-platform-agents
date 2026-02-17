from typing import Dict, List

from pydantic import BaseModel, Field


class ColocationInput(BaseModel):
    refined_routes: List[Dict] = Field(
        ..., description="Output from Tool 1."
    )
    shared_infrastructure_types: List[str] = Field(
        default=["access_roads", "land_clearing", "security"],
    )
