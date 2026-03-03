from pydantic import BaseModel, Field


class CreditEnhancementInput(BaseModel):
    gap_in_bankability: float = Field(
        ..., description="Amount of risk reduction needed for commercial lenders."
    )
