from typing import Dict, List

from pydantic import BaseModel, Field


class PhasingInput(BaseModel):
    highway_schedule: Dict = Field(
        ..., description="Construction timeline for the highway."
    )
    anchor_load_readiness: List[Dict] = Field(
        ..., description="Timeline for when customers need power."
    )
