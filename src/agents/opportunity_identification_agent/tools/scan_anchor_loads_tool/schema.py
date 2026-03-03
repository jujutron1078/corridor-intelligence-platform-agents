from typing import List
from pydantic import BaseModel, Field


class AnchorLoadScannerInput(BaseModel):
    sectors: List[str] = Field(
        default=["energy", "mining", "agriculture", "industrial", "digital"],
        description="Sectors to cross-reference against economic databases."
    )
