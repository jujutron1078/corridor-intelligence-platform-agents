from pydantic import BaseModel, Field


class RegionalIntegrationInput(BaseModel):
    trade_volume_baseline: float = Field(
        ..., description="Current intra-regional trade value."
    )
    transport_cost_reduction: float = Field(
        default=0.25, description="Expected 25% cost reduction."
    )
