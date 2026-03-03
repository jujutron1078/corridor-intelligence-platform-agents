from typing import List

from pydantic import BaseModel, Field


class DebtTermInput(BaseModel):
    debt_amount: float = Field(..., description="Total debt component.")
    cash_flow_available_for_debt_service: List[float] = Field(
        ..., description="Annual CFADS (Cash Flow Available for Debt Service)."
    )
