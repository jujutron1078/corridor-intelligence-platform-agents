from typing import Dict

from pydantic import BaseModel, Field


class RiskAnalysisInput(BaseModel):
    financial_model_data: Dict = Field(
        ..., description="Output from Tool 3 (build_financial_model)."
    )
    variable_variances: Dict = Field(
        default={"capex": 0.15, "revenue": 0.20, "interest_rate": 0.02},
        description="Variance assumptions for sensitivity (e.g. capex 15%, revenue 20%)."
    )
