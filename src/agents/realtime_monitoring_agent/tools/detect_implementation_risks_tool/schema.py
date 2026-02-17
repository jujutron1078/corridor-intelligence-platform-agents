from typing import Dict, List
from pydantic import BaseModel, Field


class RiskDetectionInput(BaseModel):
    current_performance_data: Dict = Field(
        ..., description="Combined data from tools 1-4."
    )
    external_feeds: List[str] = Field(
        default=["news", "weather", "currency_exchange"]
    )
