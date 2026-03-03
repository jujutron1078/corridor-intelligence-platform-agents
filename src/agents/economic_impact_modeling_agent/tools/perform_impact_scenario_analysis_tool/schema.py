from pydantic import BaseModel, Field


class ScenarioAnalysisInput(BaseModel):
    baseline_growth_rate: float = Field(
        ..., description="Projected GDP growth without project."
    )
    time_horizon_years: int = Field(default=20)
