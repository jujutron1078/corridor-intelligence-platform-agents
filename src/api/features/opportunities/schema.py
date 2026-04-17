from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OpportunityCreate(BaseModel):
    """Request body for saving an opportunity from chat."""

    title: str = Field(..., min_length=1, max_length=200)
    sector: str = Field(..., description="agriculture | trade | energy | manufacturing")
    sub_sector: Optional[str] = None
    country: str = Field(..., min_length=1)
    location: dict = Field(..., description='{"lat": float, "lng": float, "name": str}')

    # Assessment metrics
    bankability_score: Optional[float] = Field(None, ge=0, le=1)
    estimated_value_usd: Optional[float] = None
    estimated_return_usd: Optional[float] = None
    employment_impact: Optional[int] = None
    gdp_multiplier: Optional[float] = None
    risk_level: Optional[str] = Field(None, description="low | medium | high")

    # Context
    summary: str = Field(..., min_length=1)
    analysis_detail: str = ""
    data_sources: list[str] = []
    nearby_infrastructure: list[str] = []
    thread_id: Optional[str] = None

    # Justification
    methodology: str = ""
    data_evidence: list[dict] = []
    calculations: dict = {}
    assumptions: list[str] = []
    data_gaps: list[str] = []
    risk_breakdown: dict = {}


class OpportunityUpdate(BaseModel):
    """Request body for updating opportunity status."""

    status: str = Field(..., description="identified | under_review | shortlisted | archived")


class Opportunity(BaseModel):
    """Full opportunity record as stored."""

    id: str
    title: str
    sector: str
    sub_sector: Optional[str] = None
    country: str
    location: dict

    bankability_score: Optional[float] = None
    estimated_value_usd: Optional[float] = None
    estimated_return_usd: Optional[float] = None
    employment_impact: Optional[int] = None
    gdp_multiplier: Optional[float] = None
    risk_level: Optional[str] = None

    summary: str
    analysis_detail: str = ""
    data_sources: list[str] = []
    nearby_infrastructure: list[str] = []

    # Justification
    methodology: str = ""
    data_evidence: list[dict] = []
    calculations: dict = {}
    assumptions: list[str] = []
    data_gaps: list[str] = []
    risk_breakdown: dict = {}

    status: str = "identified"
    created_at: str
    thread_id: Optional[str] = None
    project_id: str


class OpportunityListResponse(BaseModel):
    """Response for listing opportunities."""

    opportunities: list[Opportunity]
    total: int
    sectors: dict[str, int]


class ExportRequest(BaseModel):
    """Request body for exporting investment brief."""

    opportunity_ids: list[str] = Field(..., min_length=1)
