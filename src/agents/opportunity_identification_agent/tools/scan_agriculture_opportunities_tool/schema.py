from pydantic import BaseModel, Field
from typing import Optional


class AgricultureOpportunityScanInput(BaseModel):
    """Input schema for agriculture opportunity scanning."""

    sector_focus: str = Field(
        default="agriculture",
        description="Focus sector: 'agriculture', 'trade', or 'both'",
    )
    country: Optional[str] = Field(
        default=None,
        description="Optional ISO3 country code to filter (e.g., 'NGA', 'GHA', 'CIV')",
    )
    crop: Optional[str] = Field(
        default=None,
        description="Optional crop to focus on (e.g., 'cocoa', 'cassava', 'rice')",
    )
