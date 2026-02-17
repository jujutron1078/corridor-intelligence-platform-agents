from typing import Dict, List
from pydantic import BaseModel, Field


class AdaptiveRecommendationsInput(BaseModel):
    risk_alerts: List[Dict] = Field(
        ..., description="Alerts from Tool 5."
    )
    performance_gaps: Dict = Field(
        ..., description="Variances from Tools 1-3."
    )
