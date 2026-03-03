from pydantic import BaseModel, Field


class ScenarioGenerationInput(BaseModel):
    total_capex: float = Field(..., description="CAPEX from Agent 4.")
    target_equity_irr: float = Field(
        default=0.14, description="Target return for equity investors."
    )
    max_commercial_debt_ratio: float = Field(
        default=0.4, description="Maximum ceiling for high-interest debt."
    )
