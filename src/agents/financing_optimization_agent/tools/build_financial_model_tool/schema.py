from typing import Dict, List

from pydantic import BaseModel, Field


class FinancialModelInput(BaseModel):
    revenue_projections: List[float] = Field(
        ..., description="Annual revenues from Agent 2."
    )
    capex_opex_data: Dict = Field(
        ..., description="Cost data from Agent 4."
    )
    financing_structure: Dict = Field(
        ..., description="The chosen scenario from Tool 2."
    )
