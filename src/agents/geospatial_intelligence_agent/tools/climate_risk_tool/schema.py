from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ClimateRiskInput(BaseModel):
    corridor_id: str = Field(
        ...,
        description="Corridor identifier from define_corridor_tool.",
    )
    aoi_geojson: Optional[dict] = Field(
        default=None,
        description="Optional GeoJSON polygon/multipolygon to scope the analysis. "
                    "Defaults to the full corridor AOI.",
    )
    country_iso3: Optional[str] = Field(
        default=None,
        description="ISO-3 country code (CIV/GHA/TGO/BEN/NGA) to fetch a composite "
                    "multi-hazard ranking. If omitted, composite is skipped.",
    )
    hazards: List[str] = Field(
        default=["drought", "heat", "coastal_flood"],
        description="Which hazard layers to compute. Valid: drought, heat, "
                    "coastal_flood, composite.",
    )
    coastal_return_period: int = Field(
        default=100,
        description="Deltares return-period years for coastal flood. "
                    "One of 10, 100, 250, 1000.",
    )
