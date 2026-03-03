from typing import Dict

from pydantic import BaseModel, Field


class CatalyticEffectsInput(BaseModel):
    sector_growth_targets: Dict[str, float] = Field(
        ..., description="Growth goals for mining, agriculture, etc."
    )
