from typing import List

from pydantic import BaseModel, Field


class StakeholderMappingInput(BaseModel):
    corridor_countries: List[str] = Field(
        ..., description="Countries to scan (e.g., Ghana, Togo)."
    )
    project_scope: str = Field(
        ..., description="Infrastructure types involved."
    )
