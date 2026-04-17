"""Pydantic models for the investor dashboard snapshot endpoint."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TradeArc(BaseModel):
    """A bilateral trade flow rendered as an animated arc on the map."""
    source: list[float] = Field(..., description="[lon, lat] of exporter")
    target: list[float] = Field(..., description="[lon, lat] of partner")
    commodity: str
    value_usd: float
    year: int
    flow: str = Field(..., description="'export' or 'import'")
    processing_stage: str = Field("unknown", description="'raw' or 'processed'")
    weight_kg: float = Field(0, description="Net weight in kilograms")
    reporter_name: str = Field("", description="Exporting country name")
    target_name: str = Field("", description="Destination country name")


class InvestmentMarker(BaseModel):
    """An infrastructure project plotted as a pulsing marker."""
    position: list[float] = Field(..., description="[lon, lat]")
    name: str
    sector: str
    cost_usd: float | None = None
    status: str = "planned"
    year: int | None = None
    financier: str | None = None


class ConflictPoint(BaseModel):
    """A conflict event for the heatmap layer."""
    position: list[float] = Field(..., description="[lon, lat]")
    fatalities: int = 0
    event_type: str = ""
    date: str = ""


class KpiValue(BaseModel):
    """A single KPI card value with sparkline trend data."""
    label: str
    value: float | None = None
    unit: str = ""
    trend: list[float] = Field(default_factory=list)
    trend_years: list[int] = Field(default_factory=list)
    country: str | None = None


class DashboardSnapshotResponse(BaseModel):
    """Full dashboard payload — returned by GET /api/dashboard/snapshot."""
    year: int
    corridor: dict[str, Any]
    trade_arcs: list[TradeArc] = Field(default_factory=list)
    investments: list[InvestmentMarker] = Field(default_factory=list)
    conflict_events: list[ConflictPoint] = Field(default_factory=list)
    kpis: list[KpiValue] = Field(default_factory=list)
    nightlights_tile_url: str | None = None
    data_availability: dict[str, list[int]] = Field(default_factory=dict)
