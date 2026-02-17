from pydantic import BaseModel, Field


class GapAnalysisInput(BaseModel):
    corridor_id: str = Field(..., description="ID of the study area.")
