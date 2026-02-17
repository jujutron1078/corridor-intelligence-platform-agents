from typing import List
from pydantic import BaseModel, Field


class FetchLayersInput(BaseModel):
    corridor_id: str = Field(description="The ID of the corridor defined in Tool 2")
    layers_requested: List[str] = Field(
        default=["satellite", "dem", "land_use", "protected_areas"],
        description="The types of geospatial data to fetch and clip"
    )
    resolution_meters: int = Field(default=10, description="Desired resolution in meters")
