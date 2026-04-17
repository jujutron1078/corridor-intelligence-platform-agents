"""Pydantic response models for the API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MapLayer(BaseModel):
    """A map layer that the frontend can render."""
    id: str
    type: str = Field(..., description="'raster' for tile URLs, 'geojson' for vector data")
    tile_url: str | None = None
    data: dict | None = None
    vis_params: dict | None = None
    name: str
    visible: bool = True


class ChartData(BaseModel):
    """Structured chart data for the frontend (Recharts compatible)."""
    type: str = Field("bar", description="Chart type: bar, line, pie, area")
    title: str
    data: list[dict[str, Any]]
    x_key: str | None = None
    y_key: str | None = None


class DataPoint(BaseModel):
    """A spatial data point for the frontend to place as a marker."""
    lon: float
    lat: float
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """POST /api/chat response."""
    response: str
    map_layers: list[MapLayer] = Field(default_factory=list)
    chart_data: list[ChartData] = Field(default_factory=list)
    data_points: list[DataPoint] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    model_used: str = ""
    conversation_id: str | None = None


class CorridorInfoResponse(BaseModel):
    """GET /api/corridor/info response."""
    name: str = "Lagos-Abidjan Corridor"
    countries: list[str]
    nodes: list[dict[str, Any]]
    buffer_km: float
    aoi_geojson: dict


class LayerInfo(BaseModel):
    """Metadata about an available data layer."""
    name: str
    id: str
    type: str
    temporal_range: str
    resolution: str
    description: str


class TileResponse(BaseModel):
    """Response for raster tile endpoints."""
    tile_url: str
    stats: dict[str, Any] | None = None
    vis_params: dict | None = None
    layer_name: str


class StatsResponse(BaseModel):
    """Response for statistics endpoints."""
    layer: str
    stats: dict[str, Any]
    group_by: str | None = None


class HealthResponse(BaseModel):
    """GET /api/health response."""
    status: str = "ok"
    gee_connected: bool = False
    datasets_loaded: int = 0
    osm_loaded: bool = False
    llm_connected: bool = False
    model_routes: dict[str, str] = Field(default_factory=dict)
    cache_stats: dict[str, Any] = Field(default_factory=dict)
    data_freshness: dict[str, Any] = Field(default_factory=dict)
    scheduler: dict[str, Any] = Field(default_factory=dict)


class UsageResponse(BaseModel):
    """GET /api/usage response."""
    total_queries: int = 0
    total_cost_usd: float = 0.0
    by_route: dict[str, dict[str, Any]] = Field(default_factory=dict)
