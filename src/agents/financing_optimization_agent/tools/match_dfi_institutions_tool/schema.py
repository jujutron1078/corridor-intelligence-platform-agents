from typing import Dict, List

from pydantic import BaseModel, Field


class DFIMatchingInput(BaseModel):
    corridor_countries: List[str] = Field(
        ..., description="Countries involved (e.g., Ghana, Nigeria)."
    )
    sectors: List[str] = Field(
        ..., description="Project sectors (e.g., Transmission, Digital)."
    )
    development_impact_metrics: Dict = Field(
        ..., description="Key impact stats from Agent 3."
    )
