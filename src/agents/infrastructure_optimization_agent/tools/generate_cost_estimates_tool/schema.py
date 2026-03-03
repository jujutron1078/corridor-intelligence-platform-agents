from typing import Dict

from pydantic import BaseModel, Field


class CostEstimationInput(BaseModel):
    technical_specs: Dict = Field(
        ..., description="Voltage and conductor data."
    )
    route_length_km: float = Field(
        ..., description="Total distance."
    )
    substation_count: int = Field(
        ..., description="Number of substations."
    )
