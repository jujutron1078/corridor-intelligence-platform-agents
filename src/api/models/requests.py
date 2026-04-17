"""Pydantic request models for the API."""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """POST /api/chat request body."""
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    conversation_id: str | None = Field(
        None, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$",
        description="Conversation ID for context continuity",
    )
    include_map_layers: bool = Field(True, description="Whether to include map layers in response")


ALLOWED_REPORT_TYPES = Literal["investment_brief", "due_diligence", "stakeholder_summary"]


class ReportRequest(BaseModel):
    """POST /api/chat/report request body."""
    corridor_segment: str = Field(..., min_length=1, max_length=200, description="Corridor segment name (e.g., 'Tema-Accra')")
    report_type: ALLOWED_REPORT_TYPES = Field("investment_brief", description="Report type")


class SamplePointRequest(BaseModel):
    """Query parameters for point sampling."""
    lon: float = Field(..., ge=-180, le=180)
    lat: float = Field(..., ge=-90, le=90)
    year: int = Field(2023, ge=2000, le=2030)
    month: int = Field(6, ge=1, le=12)


class TimeRangeParams(BaseModel):
    """Query parameters for change detection endpoints."""
    year_start: int = Field(..., ge=2000, le=2030)
    year_end: int = Field(..., ge=2000, le=2030)


class TemporalParams(BaseModel):
    """Query parameters for temporal data endpoints."""
    year: int = Field(2023, ge=2000, le=2030)
    month: int = Field(6, ge=1, le=12)


class ZonalStatsParams(BaseModel):
    """Query parameters for zonal statistics."""
    layer: str = Field(..., description="Layer name: nightlights, ndvi, economic_index, population, forest_loss")
    year: int | None = Field(None, ge=2000, le=2030)
    month: int | None = Field(None, ge=1, le=12)
    group_by: str = Field("country", description="Grouping: country or admin1")


class TradeFlowParams(BaseModel):
    """Query parameters for trade flow endpoints."""
    country: str = Field(..., description="ISO3 country code: NGA, BEN, TGO, GHA, CIV")
    commodity: str = Field(..., description="Commodity name: cocoa, gold, oil, etc.")


class ValueChainParams(BaseModel):
    """Query parameters for value-chain analysis."""
    commodity: str = Field(..., description="Commodity: cocoa, gold, bauxite, rubber, timber, oil")


class PriceParams(BaseModel):
    """Query parameters for commodity prices."""
    commodity: str
    start: int = Field(2015, ge=1960, le=2030)
    end: int = Field(2024, ge=1960, le=2030)
