from typing import Dict, List
from pydantic import BaseModel, Field


class AnchorRealizationInput(BaseModel):
    committed_anchors: List[str] = Field(
        ..., description="Target list from Agent 2."
    )
    metered_consumption_data: Dict = Field(
        ..., description="Actual MW consumption from the grid."
    )
