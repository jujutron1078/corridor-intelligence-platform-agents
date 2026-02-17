from pydantic import BaseModel, Field
from typing import List, Optional

class TerrainInput(BaseModel):
    corridor_id: str = Field(
        ..., 
        description="The unique identifier for the study area (generated in Tool 2)."
    )
    dem_uri: str = Field(
        ..., 
        description="The S3 URI or file path to the Digital Elevation Model (.tif) provided by Tool 3."
    )
    resolution_meters: Optional[int] = Field(
        default=30, 
        description="The spatial resolution for analysis. Higher resolution (e.g., 10m) increases accuracy but also compute time."
    )
    analysis_targets: List[str] = Field(
        default=["slope", "flood_risk", "soil_stability"],
        description="Specific terrain metrics to calculate from the elevation data."
    )
    sampling_interval_km: float = Field(
        default=5.0,
        description="The distance between cross-section samples along the corridor (e.g., every 5km)."
    )