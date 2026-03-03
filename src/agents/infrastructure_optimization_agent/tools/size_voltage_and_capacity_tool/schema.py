from pydantic import BaseModel, Field


class CapacitySizingInput(BaseModel):
    peak_demand_mw: float = Field(
        ..., description="Total demand from Agent 2."
    )
    transmission_distance_km: float = Field(
        ..., description="Route length."
    )
