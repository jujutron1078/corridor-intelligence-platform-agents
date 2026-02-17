from pydantic import BaseModel, Field
from typing import List

class Location(BaseModel):
    name: str = Field(description="The name of the location")
    country: str = Field(description="The country of the location")

class GeocodeLocationInput(BaseModel):
    locations: List[Location] = Field(description="List of location objects to geocode")