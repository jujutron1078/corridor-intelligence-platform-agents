from typing import Dict, List

from pydantic import BaseModel, Field


class StakeholderRiskInput(BaseModel):
    stakeholder_profiles: List[Dict] = Field(
        ..., description="Detailed profiles from Tool 1."
    )
