from typing import Dict
from pydantic import BaseModel, Field


class FinancialTrackingInput(BaseModel):
    actual_expenditure: float = Field(
        ..., description="Current total CAPEX spent."
    )
    revenue_data: Dict = Field(
        ..., description="Actual revenue from off-takers."
    )
    debt_service_requirements: Dict = Field(
        ..., description="Current interest and principal due."
    )
