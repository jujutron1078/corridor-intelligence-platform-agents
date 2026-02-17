from typing import Dict, List
from pydantic import BaseModel, Field


class AnchorLoadScannerInput(BaseModel):
    detections: List[Dict] = Field(
        ..., description="The infrastructure coordinates and types detected by Agent 1 (Tool 4)."
    )
    sectors: List[str] = Field(
        default=["energy", "mining", "agriculture", "industrial", "digital"],
        description="Sectors to cross-reference against economic databases."
    )
