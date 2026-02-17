from pydantic import BaseModel, Field


class PovertyReductionInput(BaseModel):
    baseline_electrification_rate: float = Field(
        ..., description="Current access rate in the zone."
    )
    projected_beneficiaries: int = Field(
        ..., description="Estimated people gaining access."
    )
