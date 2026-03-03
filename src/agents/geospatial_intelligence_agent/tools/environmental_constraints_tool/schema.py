from pydantic import BaseModel, Field
from typing import List

class EnvironmentalInput(BaseModel):
    corridor_id: str = Field(..., description="Corridor ID from Tool 2")
    vector_uri: str = Field(..., description="The .geojson path from Tool 3 containing protected areas")
    constraint_types: List[str] = Field(
        default=["national_parks", "wetlands", "cultural_sites", "forest_reserves"],
        description="Types of legal constraints to check"
    )
    buffer_zone_meters: int = Field(default=500, description="Mandatory clearance around protected zones")