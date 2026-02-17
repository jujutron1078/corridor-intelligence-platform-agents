from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    latitude: float = Field(description="The latitude of the point")
    longitude: float = Field(description="The longitude of the point")

class DefineCorridorInput(BaseModel):
    source: Coordinate = Field(description="The starting point coordinates")
    destination: Coordinate = Field(description="The ending point coordinates")
    buffer_width_km: float = Field(
        default=50.0, 
        description="The width of the corridor in kilometers (total width)"
    )