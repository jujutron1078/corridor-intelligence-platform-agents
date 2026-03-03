from typing import Literal

from pydantic import BaseModel, Field

RoutePriority = Literal["min_cost", "min_distance", "max_impact", "balance"]

PRIORITY_DESCRIPTION = (
    "What to optimize for: min_cost (cheapest route, budget primary), "
    "min_distance (shortest route, time critical), "
    "max_impact (most anchor loads, DFI development mandate), "
    "balance (default; cost, distance, impact and co-location)."
)


class RouteOptimizationInput(BaseModel):
    priority: RoutePriority = Field(
        default="balance",
        description=PRIORITY_DESCRIPTION,
    )
