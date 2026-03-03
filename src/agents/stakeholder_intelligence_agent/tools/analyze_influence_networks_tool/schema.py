from typing import Dict, List

from pydantic import BaseModel, Field


class InfluenceNetworkInput(BaseModel):
    stakeholder_list: List[Dict] = Field(
        ..., description="The database from Tool 1."
    )
