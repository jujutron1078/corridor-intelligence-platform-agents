"""
Chat service — query classification, tool calling, response synthesis.

This is the main chatbot logic. It classifies incoming queries, routes
them to the appropriate LLM model, executes data tool calls, and
synthesizes structured responses.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field as dc_field
from typing import Any

from src.api.config import MODEL_ROUTES, AGENT_ROUTING_ENABLED
from src.api.models.responses import ChatResponse, MapLayer, ChartData, DataPoint
from src.api.services.llm_service import llm_call

logger = logging.getLogger("corridor.api.chat_service")


@dataclass
class ToolResult:
    """Structured result from a tool execution."""
    text: str
    map_layer: MapLayer | None = None
    chart: ChartData | None = None
    points: list[DataPoint] = dc_field(default_factory=list)


def _geojson_to_datapoints(
    geojson: dict, name_key: str = "name", limit: int = 200,
) -> list[DataPoint]:
    """Extract up to *limit* Point features from GeoJSON into DataPoint list."""
    points: list[DataPoint] = []
    for feat in geojson.get("features", [])[:limit]:
        geom = feat.get("geometry", {})
        if geom.get("type") != "Point":
            continue
        coords = geom.get("coordinates", [])
        if len(coords) < 2:
            continue
        props = feat.get("properties", {})
        points.append(DataPoint(
            lon=coords[0],
            lat=coords[1],
            name=str(props.get(name_key, "Unknown")),
            properties=props,
        ))
    return points


_CHART_RE = re.compile(
    r"\b("
    r"chart|charts|graph|graphs|plot|plots"
    r"|visuali[sz]e|visuali[sz]ation"
    r"|compare|comparing|comparison"
    r"|trend|trends|over\s+time|time[\s-]series"
    r"|breakdown|distribution"
    r")\b",
    re.IGNORECASE,
)


def _wants_chart(message: str) -> bool:
    """Return True when the user's message signals they want a chart."""
    return bool(_CHART_RE.search(message))


# ── Conversation store (PostgreSQL with in-memory fallback) ─────────────────

from src.api.services.conversation_store import get_conversation as _get_conversation
from src.api.services.conversation_store import save_conversation as _save_conversation


# ── System prompt ────────────────────────────────────────────────────────────

CORRIDOR_SYSTEM_PROMPT = """You are the Corridor Intelligence Platform assistant analyzing the Lagos-Abidjan economic corridor
(Nigeria → Benin → Togo → Ghana → Côte d'Ivoire).

You have access to these data functions. Call them to answer user questions:

SATELLITE & REMOTE SENSING:
- get_nightlights(year, month) → Nighttime radiance (economic activity proxy)
- get_nightlights_change(year_start, year_end) → Radiance growth/decline between years
- get_ndvi(year, month) → Vegetation index
- get_economic_index(year, month) → Composite economic activity score (0-1)
- get_urban_expansion(year_start, year_end) → Where built-up area has grown
- get_landcover() → ESA WorldCover 10m classification
- get_elevation() → SRTM terrain (elevation, slope)
- get_population(year) → WorldPop gridded population (2000-2020)
- get_forest_change() → Hansen forest loss/gain
- get_building_density() → Google Open Buildings per km²
- get_sar(year, month) → Sentinel-1 radar (all-weather)
- get_climate(year, month) → ERA5 temperature, precipitation, wind
- sample_point(lon, lat, year, month) → All data values at a specific coordinate

INFRASTRUCTURE & RESOURCES:
- get_roads(tiers) → Road network by quality tier (1=motorway, 2=primary, 3=tertiary, 4=track)
- get_infrastructure() → Ports, airports, rail, borders, industrial zones
- get_minerals(commodity, status) → Mineral production/exploration sites
- get_economic_anchors() → All high-value economic points combined

TRADE & ECONOMICS:
- get_trade_flows(country, commodity) → UN Comtrade bilateral trade data
- get_value_chain(commodity) → Raw vs. processed price differential
- get_commodity_prices(commodity, start_year, end_year) → Monthly price time-series
- get_country_indicators(indicator, country) → World Bank indicators: GDP, FDI, trade %, remittances, ease of business, inflation, electricity access, internet users
- get_country_summary(country) → Latest values for all World Bank indicators for a country

ENERGY:
- get_power_plants(fuel, country) → Power plants with capacity and fuel type (solar, wind, hydro, gas, oil, coal)

LIVESTOCK & CONNECTIVITY:
- get_livestock(species) → FAO livestock density: cattle, goats, sheep, chickens, pigs
- get_connectivity(type) → Ookla Speedtest internet speed and coverage (mobile/fixed)

CONFLICT & RISK:
- get_conflict_events(country, year, event_type) → ACLED geocoded conflict events (battles, protests, riots, violence)

ENVIRONMENT & HEALTH:
- get_protected_areas() → WDPA protected area polygons (national parks, reserves)
- get_healthcare_access() → Oxford/MAP travel time to nearest healthcare facility (minutes)

STATISTICS:
- get_zonal_stats(layer, year, month, group_by) → Mean/sum per country or admin region
- get_corridor_transect(year, month) → Data sampled at all 13 corridor nodes

RULES:
1. Always specify which data functions you need to call to answer the question.
2. Return map layers when spatial data would help the user understand the answer.
3. Return chart data when time-series or comparisons would help.
4. Cite your data sources in every response.
5. If you can't answer with available data, say so and suggest what data would be needed.
6. For corridor recommendations, explain your reasoning step by step.
7. Monetary values in USD. Distances in km. Areas in km².
8. When comparing locations, include coordinates so the frontend can place markers.
"""

# ── Tool definitions ─────────────────────────────────────────────────────────

DATA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_nightlights",
            "description": "Get VIIRS nighttime lights data for a given month. Returns tile URL for map rendering and corridor-wide statistics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "Year (2012-2024)"},
                    "month": {"type": "integer", "description": "Month (1-12)"},
                },
                "required": ["year", "month"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_nightlights_change",
            "description": "Compare nighttime radiance between two years. Returns growth/decline map and statistics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year_start": {"type": "integer"},
                    "year_end": {"type": "integer"},
                },
                "required": ["year_start", "year_end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_economic_index",
            "description": "Composite economic activity index (0-1) combining nightlights (50%), built-up index (30%), and inverse vegetation (20%).",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer"},
                    "month": {"type": "integer"},
                },
                "required": ["year", "month"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_roads",
            "description": "Road network from OpenStreetMap. Filter by quality tier. Returns GeoJSON.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tiers": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Road quality tiers: 1=motorway/trunk, 2=primary/secondary, 3=tertiary, 4=residential/track",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_minerals",
            "description": "USGS mineral production facilities, exploration sites, and deposits within the corridor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity": {"type": "string", "description": "Filter by commodity: gold, bauxite, iron_ore, limestone, oil_gas, etc."},
                    "status": {"type": "string", "description": "Filter by status: active, developing, exploration."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_value_chain",
            "description": "Value-chain gap analysis for a commodity. Shows raw vs. processed price differential and multiplier per country.",
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity": {"type": "string", "description": "Commodity: cocoa, gold, bauxite, rubber, timber, oil"},
                },
                "required": ["commodity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trade_flows",
            "description": "Bilateral trade data from UN Comtrade. Shows who exports what to whom.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {"type": "string", "description": "ISO3 code: NGA, BEN, TGO, GHA, CIV"},
                    "commodity": {"type": "string"},
                },
                "required": ["country", "commodity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sample_point",
            "description": "Get all data values at a specific coordinate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lon": {"type": "number"},
                    "lat": {"type": "number"},
                    "year": {"type": "integer", "default": 2023},
                    "month": {"type": "integer", "default": 6},
                },
                "required": ["lon", "lat"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_zonal_stats",
            "description": "Compute statistics for a data layer grouped by country or admin region.",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer": {"type": "string", "description": "Layer: nightlights, ndvi, economic_index, population, forest_loss"},
                    "year": {"type": "integer"},
                    "month": {"type": "integer"},
                    "group_by": {"type": "string", "description": "country or admin1"},
                },
                "required": ["layer"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_urban_expansion",
            "description": "Detect where urban/built-up area expanded between two years using Dynamic World.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year_start": {"type": "integer"},
                    "year_end": {"type": "integer"},
                },
                "required": ["year_start", "year_end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_infrastructure",
            "description": "All infrastructure from OSM: ports, airports, rail, border crossings, industrial zones.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_economic_anchors",
            "description": "Unified layer combining mineral sites, ports, industrial zones, power plants, and SEZs.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_commodity_prices",
            "description": "Monthly commodity price time-series from World Bank.",
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity": {"type": "string"},
                    "start_year": {"type": "integer"},
                    "end_year": {"type": "integer"},
                },
                "required": ["commodity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_landcover",
            "description": "ESA WorldCover 10m land classification. Returns tile URL and area breakdown.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_population",
            "description": "WorldPop 100m gridded population. Available 2000-2020.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "Year 2000-2020"},
                },
                "required": ["year"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_corridor_transect",
            "description": "Sample all data at the 13 major corridor nodes (Lagos through Abidjan).",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "default": 2023},
                    "month": {"type": "integer", "default": 6},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_power_plants",
            "description": "Power plants in the corridor from Global Power Plant Database. Includes capacity (MW), fuel type, commissioning year, owner.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fuel": {"type": "string", "description": "Filter by fuel category: solar, wind, hydro, gas, oil, coal, biomass"},
                    "country": {"type": "string", "description": "ISO3 country code: NGA, BEN, TGO, GHA, CIV"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_conflict_events",
            "description": "ACLED conflict and protest events in the corridor. Includes battles, protests, riots, violence against civilians, explosions. Each event has location, date, actors, fatalities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {"type": "string", "description": "Country name: Nigeria, Benin, Togo, Ghana, Ivory Coast"},
                    "year": {"type": "integer", "description": "Year filter (2020-2024)"},
                    "event_type": {"type": "string", "description": "Event type: Battles, Protests, Riots, Violence against civilians, Explosions/Remote violence"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_country_indicators",
            "description": "World Bank economic indicators for corridor countries. Available indicators: GDP, GDP_GROWTH, GDP_PER_CAPITA, FDI, TRADE_PCT_GDP, REMITTANCES, EASE_OF_BUSINESS, INFLATION, POPULATION, URBAN_POP_PCT, ELECTRICITY_ACCESS, INTERNET_USERS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "indicator": {"type": "string", "description": "Indicator key: GDP, FDI, TRADE_PCT_GDP, REMITTANCES, etc."},
                    "country": {"type": "string", "description": "ISO3 country code: NGA, BEN, TGO, GHA, CIV. Omit for all countries."},
                    "start_year": {"type": "integer", "description": "Start year filter"},
                    "end_year": {"type": "integer", "description": "End year filter"},
                },
                "required": ["indicator"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_country_summary",
            "description": "Get latest values for all World Bank economic indicators for a corridor country. Returns GDP, FDI, trade %, inflation, electricity access, internet penetration, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {"type": "string", "description": "ISO3 country code: NGA, BEN, TGO, GHA, CIV"},
                },
                "required": ["country"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_protected_areas",
            "description": "WDPA protected areas: national parks, nature reserves, wildlife sanctuaries within the corridor. Returns raster mask and vector polygons.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_healthcare_access",
            "description": "Oxford/MAP healthcare accessibility — travel time in minutes to the nearest healthcare facility. Green=close, red=far. Identifies cold chain and health coverage gaps.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_livestock",
            "description": "FAO livestock density for corridor countries. Species: cattle, goats, sheep, chickens, pigs. Returns total heads and density per pixel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "species": {"type": "string", "description": "Species: cattle, goats, sheep, chickens, pigs"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_connectivity",
            "description": "Ookla Speedtest internet connectivity data. Returns download/upload speeds (Mbps) and latency (ms) per tile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Network type: mobile or fixed", "default": "mobile"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_social_facilities",
            "description": "Social infrastructure from OSM: health, education, government, financial, religious, military, recreational facilities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Filter: health, education, government, financial, religious, military, recreational"},
                },
            },
        },
    },
]


# ── Tool execution ───────────────────────────────────────────────────────────

async def execute_data_function(name: str, params: dict) -> ToolResult:
    """
    Execute a data function and return a ToolResult with text, optional
    map layer, optional chart, and optional data points.
    """
    from src.api.services import gee_service, osm_service, mineral_service, trade_service

    try:
        if name == "get_nightlights":
            result = gee_service.get_nightlights(params["year"], params["month"])
            stats = result.get("stats", {})
            return ToolResult(
                text=f"Nightlights for {params['year']}-{params['month']:02d}: "
                     f"Mean radiance={stats.get('avg_rad_mean', 'N/A')}, Max={stats.get('avg_rad_max', 'N/A')}",
                map_layer=MapLayer(
                    id="nightlights", type="raster", tile_url=result["tile_url"],
                    name=result["layer_name"], vis_params=result["vis_params"],
                ),
            )

        elif name == "get_nightlights_change":
            result = gee_service.get_nightlights_change(params["year_start"], params["year_end"])
            stats = result.get("stats", {})
            country_stats = result.get("country_stats", {})
            chart_rows = [
                {"country": k, "mean_change": v.get("mean_change", v) if isinstance(v, dict) else v}
                for k, v in country_stats.items()
            ]
            return ToolResult(
                text=f"Nightlights change {params['year_start']}-{params['year_end']}: "
                     f"Mean change={stats.get('radiance_change_mean', 'N/A')}. "
                     f"By country: {json.dumps(country_stats, default=str)}",
                map_layer=MapLayer(
                    id="nightlights_change", type="raster", tile_url=result["tile_url"],
                    name=result["layer_name"], vis_params=result["vis_params"],
                ),
                chart=ChartData(
                    type="bar",
                    title=f"Nightlights Change {params['year_start']}-{params['year_end']}",
                    data=chart_rows,
                    x_key="country", y_key="mean_change",
                ) if chart_rows else None,
            )

        elif name == "get_economic_index":
            result = gee_service.get_economic_index(params["year"], params["month"])
            stats = result.get("stats", {})
            return ToolResult(
                text=f"Economic Activity Index {params['year']}-{params['month']:02d}: "
                     f"Mean={stats.get('economic_activity_index_mean', 'N/A')}, "
                     f"Max={stats.get('economic_activity_index_max', 'N/A')}",
                map_layer=MapLayer(
                    id="economic_index", type="raster", tile_url=result["tile_url"],
                    name=result["layer_name"], vis_params=result["vis_params"],
                ),
            )

        elif name == "get_roads":
            geojson = osm_service.get_roads(params.get("tiers"))
            total_km = sum(f["properties"].get("length_km", 0) for f in geojson.get("features", []))
            return ToolResult(
                text=f"Road network: {len(geojson['features'])} segments, {total_km:.0f} km total",
                map_layer=MapLayer(id="roads", type="geojson", data=geojson, name="Road Network"),
            )

        elif name == "get_minerals":
            geojson = mineral_service.get_minerals(params.get("commodity"), params.get("status"))
            return ToolResult(
                text=f"Mineral sites: {len(geojson['features'])} features" +
                     (f" (commodity={params.get('commodity')})" if params.get("commodity") else ""),
                map_layer=MapLayer(id="minerals", type="geojson", data=geojson, name="Mineral Sites"),
                points=_geojson_to_datapoints(geojson, name_key="site_name"),
            )

        elif name == "get_value_chain":
            analysis = trade_service.get_value_chain(params["commodity"])
            gaps = analysis.get("gaps_by_country", {})
            chart_rows = [
                {"country": k, "processing_pct": v.get("processing_pct", 0)}
                for k, v in gaps.items() if isinstance(v, dict)
            ]
            return ToolResult(
                text=f"Value chain for {params['commodity']}: "
                     f"Raw price ${analysis.get('raw_price', 'N/A')}/ton, "
                     f"Processed ${analysis.get('processed_price', 'N/A')}/ton, "
                     f"Multiplier: {analysis.get('multiplier', 'N/A')}x. "
                     f"Gaps by country: {json.dumps(gaps, default=str)}",
                chart=ChartData(
                    type="bar",
                    title=f"{params['commodity'].title()} Value Chain by Country",
                    data=chart_rows,
                    x_key="country", y_key="processing_pct",
                ) if chart_rows else None,
            )

        elif name == "get_trade_flows":
            data = trade_service.get_trade_flows(params["country"], params["commodity"])
            return ToolResult(
                text=f"Trade flows for {params['country']}/{params['commodity']}: "
                     f"{data.get('total_records', 0)} records. "
                     f"Data: {json.dumps(data.get('data', [])[:5], default=str)}",
            )

        elif name == "sample_point":
            data = gee_service.sample_point(
                params["lon"], params["lat"],
                params.get("year", 2023), params.get("month", 6),
            )
            return ToolResult(
                text=f"Point sample at ({params['lon']}, {params['lat']}): {json.dumps(data, default=str)}",
                points=[DataPoint(
                    lon=params["lon"], lat=params["lat"],
                    name=f"Sample ({params['lon']}, {params['lat']})",
                    properties=data if isinstance(data, dict) else {},
                )],
            )

        elif name == "get_zonal_stats":
            stats = gee_service.zone_stats(
                params["layer"], params.get("year"), params.get("month"),
                params.get("group_by", "country"),
            )
            return ToolResult(
                text=f"Zonal stats for {params['layer']}: {json.dumps(stats, default=str)}",
            )

        elif name == "get_urban_expansion":
            result = gee_service.get_urban_expansion(params["year_start"], params["year_end"])
            return ToolResult(
                text=f"Urban expansion {params['year_start']}-{params['year_end']}",
                map_layer=MapLayer(
                    id="urban_expansion", type="raster", tile_url=result["tile_url"],
                    name=result["layer_name"], vis_params=result["vis_params"],
                ),
            )

        elif name == "get_infrastructure":
            geojson = osm_service.get_infrastructure()
            return ToolResult(
                text=f"Infrastructure: {len(geojson['features'])} features (ports, airports, rail, borders, industrial)",
                map_layer=MapLayer(id="infrastructure", type="geojson", data=geojson, name="Infrastructure"),
                points=_geojson_to_datapoints(geojson, name_key="name"),
            )

        elif name == "get_economic_anchors":
            geojson = mineral_service.get_economic_anchors()
            return ToolResult(
                text=f"Economic anchors: {len(geojson['features'])} features",
                map_layer=MapLayer(id="economic_anchors", type="geojson", data=geojson, name="Economic Anchors"),
            )

        elif name == "get_commodity_prices":
            data = trade_service.get_commodity_prices(
                params["commodity"],
                params.get("start_year", 2015),
                params.get("end_year", 2024),
            )
            price_data = data.get("data", [])
            return ToolResult(
                text=f"Commodity prices for {params['commodity']}: {len(price_data)} monthly records",
                chart=ChartData(
                    type="line",
                    title=f"{params['commodity'].title()} Prices",
                    data=price_data,
                    x_key="date", y_key="price",
                ) if price_data else None,
            )

        elif name == "get_landcover":
            result = gee_service.get_landcover()
            return ToolResult(
                text="ESA WorldCover 2021 land classification",
                map_layer=MapLayer(
                    id="landcover", type="raster", tile_url=result["tile_url"],
                    name=result["layer_name"], vis_params=result["vis_params"],
                ),
            )

        elif name == "get_population":
            result = gee_service.get_population(params["year"])
            stats = result.get("stats", {})
            return ToolResult(
                text=f"Population {params['year']}: Total within corridor ≈ {stats.get('population_sum', 'N/A')}",
                map_layer=MapLayer(
                    id="population", type="raster", tile_url=result["tile_url"],
                    name=result["layer_name"], vis_params=result["vis_params"],
                ),
            )

        elif name == "get_corridor_transect":
            data = gee_service.corridor_transect(
                params.get("year", 2023), params.get("month", 6),
            )
            transect_points = [
                DataPoint(
                    lon=node.get("lon", node.get("longitude", 0)),
                    lat=node.get("lat", node.get("latitude", 0)),
                    name=node.get("name", "Node"),
                    properties={k: v for k, v in node.items()
                                if k not in ("lon", "lat", "longitude", "latitude")},
                )
                for node in (data if isinstance(data, list) else [])
            ]
            return ToolResult(
                text=f"Corridor transect ({len(data)} nodes): {json.dumps(data[:3], default=str)}...",
                points=transect_points,
            )

        elif name == "get_power_plants":
            from src.api.services import energy_service
            result = energy_service.get_power_plants(
                params.get("fuel"), params.get("country"),
            )
            summary = result.get("summary", {})
            by_fuel = summary.get("by_fuel", {})
            chart_rows = [{"fuel": k, "count": v} for k, v in by_fuel.items()]
            pp_geojson = {"type": "FeatureCollection", "features": result.get("features", [])}
            return ToolResult(
                text=f"Power plants: {summary.get('total_plants', 0)} plants, "
                     f"{summary.get('total_capacity_mw', 0)} MW total capacity. "
                     f"By fuel: {json.dumps(by_fuel, default=str)}",
                map_layer=MapLayer(
                    id="power_plants", type="geojson", data=pp_geojson,
                    name="Power Plants",
                ),
                chart=ChartData(
                    type="pie",
                    title="Power Plants by Fuel Type",
                    data=chart_rows,
                    x_key="fuel", y_key="count",
                ) if chart_rows else None,
                points=_geojson_to_datapoints(pp_geojson, name_key="name"),
            )

        elif name == "get_conflict_events":
            from src.api.services import acled_service
            result = acled_service.get_conflict_events(
                params.get("country"), params.get("year"), params.get("event_type"),
            )
            summary = result.get("summary", {})
            conflict_geojson = {"type": "FeatureCollection", "features": result.get("features", [])[:200]}
            return ToolResult(
                text=f"Conflict events: {summary.get('total_events', 0)} events, "
                     f"{summary.get('total_fatalities', 0)} fatalities. "
                     f"By type: {json.dumps(summary.get('by_event_type', {}), default=str)}. "
                     f"By country: {json.dumps(summary.get('by_country', {}), default=str)}",
                map_layer=MapLayer(
                    id="conflict_events", type="geojson",
                    data=conflict_geojson, name="Conflict Events",
                ),
                points=_geojson_to_datapoints(conflict_geojson, name_key="event_type"),
            )

        elif name == "get_country_indicators":
            from src.api.services import worldbank_service
            result = worldbank_service.get_indicator(
                params["indicator"],
                params.get("country"),
                params.get("start_year"),
                params.get("end_year"),
            )
            data = result.get("data", [])
            return ToolResult(
                text=f"{result.get('indicator_name', params['indicator'])}: "
                     f"{result.get('total_records', 0)} records. "
                     f"Latest: {json.dumps(data[-5:] if data else [], default=str)}",
                chart=ChartData(
                    type="line",
                    title=result.get("indicator_name", params["indicator"]),
                    data=data,
                    x_key="year", y_key="value",
                ) if data else None,
            )

        elif name == "get_country_summary":
            from src.api.services import worldbank_service
            result = worldbank_service.get_country_summary(params["country"])
            indicators = result.get("indicators", {})
            chart_rows = [
                {"indicator": k, "value": v}
                for k, v in indicators.items() if isinstance(v, (int, float))
            ]
            return ToolResult(
                text=f"Economic summary for {result.get('country_name', params['country'])}: "
                     f"{json.dumps(indicators, default=str)}",
                chart=ChartData(
                    type="bar",
                    title=f"Economic Indicators: {result.get('country_name', params['country'])}",
                    data=chart_rows,
                    x_key="indicator", y_key="value",
                ) if chart_rows else None,
            )

        elif name == "get_protected_areas":
            result = gee_service.get_protected_areas()
            geojson = result.get("geojson")
            count = len(geojson.get("features", [])) if geojson else 0
            return ToolResult(
                text=f"WDPA Protected Areas: {count} protected areas in corridor",
                map_layer=MapLayer(
                    id="protected_areas", type="raster", tile_url=result["tile_url"],
                    name=result["layer_name"], vis_params=result["vis_params"],
                ),
            )

        elif name == "get_healthcare_access":
            result = gee_service.get_healthcare_access()
            stats = result.get("stats", {})
            return ToolResult(
                text=f"Healthcare Accessibility: Mean travel time={stats.get('travel_time_minutes_mean', 'N/A')} min, "
                     f"Max={stats.get('travel_time_minutes_max', 'N/A')} min",
                map_layer=MapLayer(
                    id="healthcare_access", type="raster", tile_url=result["tile_url"],
                    name=result["layer_name"], vis_params=result["vis_params"],
                ),
            )

        elif name == "get_livestock":
            from src.api.services import livestock_service
            result = livestock_service.get_livestock(params.get("species"))
            return ToolResult(
                text=f"Livestock data: {json.dumps(result, default=str)}",
            )

        elif name == "get_connectivity":
            from src.api.services import connectivity_service
            result = connectivity_service.get_connectivity(params.get("type", "mobile"))
            summary = result.get("summary", {})
            return ToolResult(
                text=f"Internet connectivity ({result.get('network_type', 'mobile')}): "
                     f"{summary.get('total_tiles', 0)} tiles, "
                     f"Avg download={summary.get('avg_download_mbps', 0)} Mbps, "
                     f"Avg latency={summary.get('avg_latency_ms', 0)} ms",
                map_layer=MapLayer(
                    id="connectivity", type="geojson",
                    data={"type": "FeatureCollection", "features": result.get("features", [])[:500]},
                    name="Internet Connectivity",
                ) if result.get("features") else None,
            )

        elif name == "get_social_facilities":
            geojson = osm_service.get_social_facilities(params.get("type"))
            return ToolResult(
                text=f"Social facilities: {len(geojson['features'])} features" +
                     (f" (type={params.get('type')})" if params.get("type") else " (all types)"),
                map_layer=MapLayer(id="social_facilities", type="geojson", data=geojson, name="Social Facilities"),
                points=_geojson_to_datapoints(geojson, name_key="name"),
            )

        else:
            return ToolResult(text=f"Unknown function: {name}")

    except Exception as exc:
        logger.error("Tool execution error (%s): %s", name, exc)
        return ToolResult(text=f"Error executing {name}: {str(exc)}")


# ── Query classification ─────────────────────────────────────────────────────

async def classify_query(message: str) -> str:
    """
    Quick classification of user intent to pick the right model route.
    Uses the cheapest model.
    """
    try:
        classification = await llm_call(
            route="simple",
            messages=[{"role": "user", "content": message}],
            system="""Classify this user message into exactly one category:
- "data_query" — asking about corridor data, maps, statistics, comparisons
- "report" — requesting a report, brief, summary document
- "simple" — greeting, help, general question not about corridor data
- "complex" — multi-step analysis, cross-corridor comparison, investment recommendation
Reply with ONLY the category name, nothing else.""",
        )

        category = classification["choices"][0]["message"]["content"].strip().lower().strip('"')

        route_map = {
            "data_query": "chat_agent",
            "report": "report",
            "simple": "simple",
            "complex": "synthesis",
        }
        return route_map.get(category, "chat_agent")
    except Exception as exc:
        logger.warning("Query classification failed: %s. Defaulting to chat_agent.", exc)
        return "chat_agent"


# ── Main chat processing ────────────────────────────────────────────────────

async def process_chat(
    message: str,
    conversation_id: str | None = None,
    include_map_layers: bool = True,
) -> ChatResponse:
    """
    Full chat processing flow:
    1. Classify query → pick model route
    2. Send to LLM with tools → get tool calls
    3. Execute data functions
    4. Send results back to LLM → get synthesis
    5. Return structured response
    """
    conversation_history = _get_conversation(conversation_id)

    # Step 1: Pick the right model
    route = await classify_query(message)
    logger.info("Query classified as: %s", route)

    # Step 1.5: Route to orchestrator agent when enabled
    # Routes all non-simple queries through the multi-agent system
    if AGENT_ROUTING_ENABLED and route != "simple":
        try:
            from src.api.services.agent_bridge import invoke_agent
            logger.info("Routing '%s' query to orchestrator agent", route)
            agent_resp = await invoke_agent(
                message, conversation_id, conversation_history,
            )
            # Persist conversation so follow-ups still work
            new_history = conversation_history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": agent_resp.response},
            ]
            _save_conversation(conversation_id, new_history)
            agent_resp.conversation_id = conversation_id
            return agent_resp
        except Exception as exc:
            logger.warning("Agent routing failed, falling back to normal flow: %s", exc)

    # Step 2: For simple queries, skip tool calling
    if route == "simple":
        response = await llm_call(
            route="simple",
            messages=conversation_history + [{"role": "user", "content": message}],
            system=CORRIDOR_SYSTEM_PROMPT,
        )
        text = response["choices"][0]["message"]["content"] or ""

        # Save conversation
        new_history = conversation_history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": text},
        ]
        _save_conversation(conversation_id, new_history)

        return ChatResponse(
            response=text,
            model_used=MODEL_ROUTES["simple"]["model"],
            conversation_id=conversation_id,
        )

    # Step 3: For data/complex queries, use tool calling
    response = await llm_call(
        route=route,
        messages=conversation_history + [{"role": "user", "content": message}],
        system=CORRIDOR_SYSTEM_PROMPT,
        tools=DATA_TOOLS,
    )

    assistant_message = response["choices"][0]["message"]
    tool_calls = assistant_message.get("tool_calls", [])

    # Step 4: Execute tool calls
    tool_results = []
    map_layers = []
    chart_data_list: list[ChartData] = []
    data_points: list[DataPoint] = []
    sources = set()
    include_charts = _wants_chart(message)

    for tc in tool_calls:
        fn_name = tc["function"]["name"]
        raw_args = tc["function"].get("arguments", "") or "{}"
        fn_args = json.loads(raw_args) if raw_args.strip() else {}
        logger.info("Executing tool: %s(%s)", fn_name, fn_args)

        result = await execute_data_function(fn_name, fn_args)
        tool_results.append({
            "tool_call_id": tc["id"],
            "role": "tool",
            "content": result.text,
        })
        if result.map_layer and include_map_layers:
            map_layers.append(result.map_layer)
        if result.chart and include_charts:
            chart_data_list.append(result.chart)
        data_points.extend(result.points)

        # Track source
        source_map = {
            "get_nightlights": "VIIRS Nightlights",
            "get_nightlights_change": "VIIRS Nightlights",
            "get_economic_index": "VIIRS Nightlights + Sentinel-2",
            "get_roads": "OpenStreetMap",
            "get_minerals": "USGS Africa Minerals",
            "get_value_chain": "World Bank Pink Sheet",
            "get_trade_flows": "UN Comtrade",
            "get_landcover": "ESA WorldCover",
            "get_population": "WorldPop",
            "get_urban_expansion": "Google Dynamic World",
            "get_infrastructure": "OpenStreetMap",
            "get_economic_anchors": "USGS + OpenStreetMap",
            "get_commodity_prices": "World Bank Pink Sheet",
            "sample_point": "Multiple (VIIRS, Sentinel-2, SRTM, WorldPop, ESA WorldCover)",
            "get_zonal_stats": "GEE Analytics",
            "get_corridor_transect": "Multiple (all corridor datasets)",
            "get_power_plants": "Global Power Plant Database (WRI)",
            "get_conflict_events": "ACLED (Armed Conflict Location & Event Data)",
            "get_country_indicators": "World Bank Open Data",
            "get_country_summary": "World Bank Open Data",
            "get_protected_areas": "WDPA (World Database on Protected Areas)",
            "get_healthcare_access": "Oxford/MAP Healthcare Accessibility 2019",
            "get_social_facilities": "OpenStreetMap + healthsites.io",
            "get_livestock": "FAO Gridded Livestock of the World (GLW 3)",
            "get_connectivity": "Ookla Speedtest Open Data",
        }
        sources.add(source_map.get(fn_name, fn_name))

    # If no tool calls, just use the direct response
    if not tool_calls:
        text = assistant_message.get("content", "")
        new_history = conversation_history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": text},
        ]
        _save_conversation(conversation_id, new_history)

        return ChatResponse(
            response=text,
            map_layers=map_layers,
            chart_data=chart_data_list,
            data_points=data_points,
            sources=list(sources),
            model_used=MODEL_ROUTES[route]["model"],
            conversation_id=conversation_id,
        )

    # Step 5: Send results back for synthesis
    synthesis_messages = [
        *conversation_history,
        {"role": "user", "content": message},
        assistant_message,
        *tool_results,
    ]

    synthesis_route = "synthesis" if route == "synthesis" else "chat_agent"
    synthesis = await llm_call(
        route=synthesis_route,
        messages=synthesis_messages,
        system=CORRIDOR_SYSTEM_PROMPT,
    )

    synthesis_text = synthesis["choices"][0]["message"]["content"] or ""

    # Save conversation (simplified — don't store tool calls)
    new_history = conversation_history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": synthesis_text},
    ]
    _save_conversation(conversation_id, new_history)

    return ChatResponse(
        response=synthesis_text,
        map_layers=map_layers,
        chart_data=chart_data_list,
        data_points=data_points,
        sources=list(sources),
        model_used=MODEL_ROUTES[synthesis_route]["model"],
        conversation_id=conversation_id,
    )
