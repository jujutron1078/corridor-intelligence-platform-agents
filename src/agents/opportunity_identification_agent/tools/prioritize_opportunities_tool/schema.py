from typing import Dict, List
from pydantic import BaseModel, Field


class PrioritizationInput(BaseModel):
    anchor_catalog: List[Dict] = Field(
        ..., description="Catalog with demand and bankability data."
    )
