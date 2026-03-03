from typing import Dict

from pydantic import BaseModel, Field


class EngagementRoadmapInput(BaseModel):
    influence_data: Dict = Field(
        ..., description="Output from Tool 2."
    )
    project_timeline_months: int = Field(default=24)
