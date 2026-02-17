from typing import Dict, List
from pydantic import BaseModel, Field


class RouteOptimizationInput(BaseModel):
    corridor_id: str = Field(..., description="Corridor ID from Tool 2")
    anchor_nodes: List[Dict] = Field(
        ..., description="Coordinates of detections from Tool 4"
    )
    cost_surface_uri: str = Field(
        ..., description="The slope/difficulty map from Tool 5"
    )
    constraints_uri: str = Field(
        ..., description="The No-Go zones from Tool 6"
    )
    priority: str = Field(
        default="balance",
        description="Optimization goal: 'min_cost', 'min_distance', or 'max_impact'"
    )
