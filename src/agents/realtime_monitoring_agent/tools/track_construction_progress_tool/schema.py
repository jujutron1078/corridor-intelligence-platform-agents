from typing import Dict, List
from pydantic import BaseModel, Field


class ConstructionProgressInput(BaseModel):
    baseline_schedule_uri: str = Field(
        ..., description="The original Gantt chart/timeline."
    )
    monthly_site_reports: List[Dict] = Field(
        ..., description="Data on km built and towers erected."
    )
