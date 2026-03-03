from typing import Dict, List

from pydantic import BaseModel, Field


class SubstationPlacementInput(BaseModel):
    anchor_load_clusters: List[Dict] = Field(
        ..., description="Anchor load groupings from Agent 2."
    )
    refined_route_uri: str = Field(
        ..., description="URI of the optimized route."
    )
