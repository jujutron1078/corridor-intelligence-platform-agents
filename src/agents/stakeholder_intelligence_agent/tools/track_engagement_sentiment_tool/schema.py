from typing import List

from pydantic import BaseModel, Field


class SentimentTrackingInput(BaseModel):
    stakeholder_ids: List[str] = Field(
        ..., description="IDs to monitor."
    )
    tracking_period_days: int = Field(default=30)
