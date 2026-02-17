from typing import List
from pydantic import BaseModel, Field


class DetectionInput(BaseModel):
    satellite_image_uri: str = Field(description="S3 URI from Tool 3")
    types: List[str] = Field(description="Infrastructure types to detect")
