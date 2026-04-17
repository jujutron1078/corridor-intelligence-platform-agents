"""
Dashboard service — assembles data from existing services for the investor dashboard.

Returns a single composite snapshot containing KPIs, trade arcs, investment markers,
conflict heatmap points, corridor geometry, and nightlights tile URL.
"""

from __future__ import annotations

import logging
from typing import Any

from src.shared.pipeline.aoi import CORRIDOR, CORRIDOR_NODES, COUNTRIES, COUNTRY_NAMES

logger = logging.getLogger("corridor.api.dashboard_service")

# ── Country centroid lookup (capital-city coordinates from corridor nodes) ────
# Maps ISO3 codes to [lon, lat] for corridor countries.
_CORRIDOR_COUNTRY_CENTROIDS: dict[str, list[float]] = {
    "NGA": [3.40, 6.45],    # Lagos
    "BEN": [2.42, 6.37],    # Cotonou
    "TGO": [1.23, 6.17],    # Lomé
    "GHA": [-0.19, 5.60],   # Accra
    "CIV": [-3.97, 5.36],   # Abidjan
}

# Major trading partner centroids (approximate capital coordinates).
_PARTNER_CENTROIDS: dict[str, list[float]] = {
    "CHN": [116.40, 39.90],
    "IND": [77.21, 28.61],
    "USA": [-77.04, 38.90],
    "NLD": [4.90, 52.37],
    "FRA": [2.35, 48.86],
    "DEU": [13.40, 52.52],
    "GBR": [-0.12, 51.51],
    "BRA": [-47.88, -15.79],
    "JPN": [139.69, 35.69],
    "ZAF": [28.05, -25.75],
    "ESP": [-3.70, 40.42],
    "TUR": [32.87, 39.93],
    "KOR": [126.98, 37.57],
    "ARE": [54.37, 24.45],
    "MYS": [101.69, 3.14],
    "IDN": [106.85, -6.21],
    "THA": [100.50, 13.75],
    "VNM": [105.85, 21.03],
    "SGP": [103.85, 1.29],
    "BEL": [4.35, 50.85],
    "ITA": [12.50, 41.90],
    "CAN": [-75.70, 45.42],
    "RUS": [37.62, 55.75],
}

_ISO3_NAMES: dict[str, str] = {
    "NGA": "Nigeria", "BEN": "Benin", "TGO": "Togo", "GHA": "Ghana", "CIV": "Côte d'Ivoire",
    "CHN": "China", "IND": "India", "USA": "United States", "NLD": "Netherlands",
    "FRA": "France", "DEU": "Germany", "GBR": "United Kingdom", "BRA": "Brazil",
    "JPN": "Japan", "ZAF": "South Africa", "ESP": "Spain", "TUR": "Turkey",
    "KOR": "South Korea", "ARE": "UAE", "MYS": "Malaysia", "IDN": "Indonesia",
    "THA": "Thailand", "VNM": "Vietnam", "SGP": "Singapore", "BEL": "Belgium",
    "ITA": "Italy", "CAN": "Canada", "RUS": "Russia",
}


def get_snapshot(year: int) -> dict[str, Any]:
    """Build the full dashboard snapshot for a given year."""
    return {
        "year": year,
        "corridor": _get_corridor(),
        "trade_arcs": _get_trade_arcs(year),
        "investments": _get_investments(),
        "conflict_events": _get_conflict_events(year),
        "kpis": _get_kpis(year),
        "nightlights_tile_url": _get_nightlights_url(year),
        "data_availability": _get_data_availability(),
    }


# ── Corridor geometry ──────────────────────────────────────────────────────────

def _get_corridor() -> dict[str, Any]:
    """Return corridor AOI geometry and nodes."""
    return {
        "nodes": CORRIDOR.nodes,
        "countries": CORRIDOR.countries,
        "country_names": COUNTRY_NAMES,
        "buffer_km": CORRIDOR.buffer_km,
        "centerline": list(CORRIDOR.node_coords),
        "aoi_geojson": CORRIDOR.to_geojson(),
    }


# ── Trade arcs ─────────────────────────────────────────────────────────────────

def _get_trade_arcs(year: int) -> list[dict]:
    """Build bilateral trade arc data from COMTRADE CSVs."""
    try:
        from src.api.services.trade_service import _trade_flows
    except Exception:
        logger.warning("Trade service not available for dashboard")
        return []

    arcs: list[dict] = []
    logger.info("_get_trade_arcs called — enhanced version with processing_stage/weight_kg")

    for commodity, df in _trade_flows.items():
        if df is None or df.empty:
            continue

        # Filter to selected year
        year_mask = df["year"] == year
        year_df = df[year_mask]
        if year_df.empty:
            continue

        # Group by reporter + flow + processing_stage to preserve detail
        group_cols = ["reporter_iso3", "flow"]
        agg_cols: dict[str, str] = {"trade_value_usd": "sum"}
        if "processing_stage" in year_df.columns:
            group_cols.append("processing_stage")
        if "net_weight_kg" in year_df.columns:
            agg_cols["net_weight_kg"] = "sum"

        grouped = year_df.groupby(group_cols).agg(agg_cols).reset_index()

        for _, row in grouped.iterrows():
            reporter = row["reporter_iso3"]
            source = _CORRIDOR_COUNTRY_CENTROIDS.get(reporter)
            if not source:
                continue

            value_usd = float(row["trade_value_usd"])
            if value_usd <= 0:
                continue

            flow = row["flow"]
            processing = row.get("processing_stage", "unknown") if "processing_stage" in grouped.columns else "unknown"
            weight_kg = float(row.get("net_weight_kg", 0)) if "net_weight_kg" in grouped.columns else 0

            target_iso3, target_coords = _pick_trade_target_with_name(commodity, flow, reporter)
            if not target_coords:
                continue

            reporter_name = _ISO3_NAMES.get(reporter, reporter)
            target_name = _ISO3_NAMES.get(target_iso3, target_iso3) if target_iso3 else "Unknown"

            arcs.append({
                "source": source,
                "target": target_coords,
                "commodity": commodity,
                "value_usd": value_usd,
                "year": year,
                "flow": flow,
                "processing_stage": str(processing),
                "weight_kg": weight_kg,
                "reporter_name": reporter_name,
                "target_name": target_name,
            })

    # Keep top 150 arcs by value
    arcs.sort(key=lambda a: a["value_usd"], reverse=True)
    result = arcs[:150]
    if result:
        logger.info("Trade arcs sample keys: %s", list(result[0].keys()))
    return result


_COMMODITY_TARGETS: dict[str, list[str]] = {
    "cocoa": ["NLD", "USA", "DEU", "FRA", "BEL"],
    "gold": ["ZAF", "ARE", "CHN", "IND", "GBR"],
    "oil": ["IND", "USA", "CHN", "BRA", "ESP"],
    "cotton": ["CHN", "IND", "TUR", "VNM", "BRA"],
    "cashew": ["IND", "VNM", "CHN", "USA", "NLD"],
    "fish": ["ESP", "FRA", "JPN", "USA", "NLD"],
    "palm_oil": ["IND", "CHN", "NLD", "GBR", "DEU"],
    "rubber": ["CHN", "USA", "DEU", "JPN", "FRA"],
    "cement": ["GHA", "TGO", "BEN", "NGA", "CIV"],
    "bauxite": ["CHN", "IND", "RUS", "CAN", "ARE"],
    "manganese": ["CHN", "IND", "KOR", "JPN", "USA"],
    "timber": ["CHN", "IND", "FRA", "DEU", "USA"],
    "shea": ["FRA", "NLD", "USA", "GBR", "DEU"],
    "phosphates": ["IND", "BRA", "FRA", "USA", "ESP"],
}


def _pick_trade_target_with_name(commodity: str, flow: str, reporter: str) -> tuple[str | None, list[float] | None]:
    """Pick a representative global trade partner. Returns (iso3, coords)."""
    targets = _COMMODITY_TARGETS.get(commodity, ["CHN", "USA", "IND", "NLD", "FRA"])
    for iso3 in targets:
        if iso3 != reporter:
            coords = _PARTNER_CENTROIDS.get(iso3) or _CORRIDOR_COUNTRY_CENTROIDS.get(iso3)
            if coords:
                return iso3, coords
    return None, None


# ── Investment markers ─────────────────────────────────────────────────────────

def _get_investments() -> list[dict]:
    """Extract investment project markers from projects_enriched data."""
    try:
        from src.api.services.projects_enriched_service import get_projects
    except Exception:
        logger.warning("Projects enriched service not available for dashboard")
        return []

    projects = get_projects()
    markers: list[dict] = []

    for p in projects:
        countries = p.get("countries", [])
        if not countries:
            continue

        # Place marker at the centroid of the first corridor country
        position = None
        for c in countries:
            if c in _CORRIDOR_COUNTRY_CENTROIDS:
                position = _CORRIDOR_COUNTRY_CENTROIDS[c]
                break

        if not position:
            continue

        # Add small jitter per project to avoid exact overlap
        idx = len(markers)
        jittered = [
            position[0] + (idx % 7 - 3) * 0.15,
            position[1] + (idx % 5 - 2) * 0.12,
        ]

        # Parse cost
        raw_cost = p.get("total_cost_usd_million") or 0
        try:
            cost = float(str(raw_cost).replace(",", ""))
            # Normalize: values > 100_000 are likely raw USD, not millions
            if cost > 100_000:
                cost = cost / 1_000_000
            cost = cost * 1_000_000  # Convert millions to raw USD for display
        except (ValueError, TypeError):
            cost = None

        # Determine status
        status = (p.get("status") or "planned").lower()
        if "active" in status or "implementation" in status:
            status = "committed"
        elif "pipeline" in status or "preparation" in status:
            status = "pipeline"
        else:
            status = "planned"

        # Parse sector
        raw_sector = p.get("sector", "Infrastructure")
        if isinstance(raw_sector, dict):
            raw_sector = raw_sector.get("Name", "Infrastructure")
        sector = str(raw_sector).split(",")[0].strip()

        financiers = p.get("financiers", [])
        financier = financiers[0] if financiers else p.get("lead_agency")

        markers.append({
            "position": jittered,
            "name": p.get("name", "Untitled Project"),
            "sector": sector,
            "cost_usd": cost,
            "status": status,
            "year": p.get("construction_start"),
            "financier": financier,
        })

    return markers


# ── Conflict heatmap ───────────────────────────────────────────────────────────

def _get_conflict_events(year: int) -> list[dict]:
    """Extract conflict events for the heatmap layer.

    Falls back to all available events if none exist for the requested year.
    """
    try:
        from src.api.services.acled_service import get_conflict_events
    except Exception:
        logger.warning("ACLED service not available for dashboard")
        return []

    result = get_conflict_events(year=year)
    features = result.get("features", [])

    # If no events for the requested year, show all cached events
    if not features:
        result = get_conflict_events()
        features = result.get("features", [])

    points: list[dict] = []
    for f in features:
        props = f.get("properties", {})
        coords = f.get("geometry", {}).get("coordinates")
        if not coords or len(coords) < 2:
            continue

        points.append({
            "position": [coords[0], coords[1]],
            "fatalities": props.get("fatalities", 0),
            "event_type": props.get("event_type", ""),
            "date": props.get("event_date", ""),
        })

    return points


# ── KPIs ───────────────────────────────────────────────────────────────────────

def _get_kpis(year: int) -> list[dict]:
    """Build KPI cards with sparkline trend data."""
    kpis: list[dict] = []

    # GDP Growth (corridor average)
    gdp_kpi = _build_macro_kpi("gdp_growth_annual_pct", "GDP Growth", "%", year)
    if gdp_kpi:
        kpis.append(gdp_kpi)

    # FDI Net Inflows
    fdi_kpi = _build_macro_kpi("fdi_net_inflows_pct_gdp", "FDI Inflows", "% GDP", year)
    if fdi_kpi:
        kpis.append(fdi_kpi)

    # Trade volume
    trade_kpi = _build_trade_volume_kpi(year)
    if trade_kpi:
        kpis.append(trade_kpi)

    # Risk score (from ACLED)
    risk_kpi = _build_risk_kpi(year)
    if risk_kpi:
        kpis.append(risk_kpi)

    # Infrastructure readiness
    infra_kpi = _build_infra_readiness_kpi()
    if infra_kpi:
        kpis.append(infra_kpi)

    return kpis


def _build_macro_kpi(indicator: str, label: str, unit: str, year: int) -> dict | None:
    """Build a KPI from macro_enriched data with trend sparkline."""
    try:
        from src.api.services.macro_enriched_service import get_indicators
    except Exception:
        return None

    records = get_indicators()
    if not records:
        return None

    # Collect values across all corridor countries for each year
    all_years: dict[int, list[float]] = {}
    for r in records:
        wb = r.get("worldbank_indicators", {})
        series = wb.get(indicator, {})
        for yr_str, val in series.items():
            try:
                yr = int(yr_str)
                if val is not None:
                    all_years.setdefault(yr, []).append(float(val))
            except (ValueError, TypeError):
                continue

    if not all_years:
        return None

    # Compute corridor average per year
    trend_years = sorted(all_years.keys())
    trend_values = [round(sum(all_years[y]) / len(all_years[y]), 2) for y in trend_years]

    # Current value
    current_val = None
    if year in all_years:
        current_val = round(sum(all_years[year]) / len(all_years[year]), 2)
    elif trend_years:
        # Fall back to latest available
        latest_yr = trend_years[-1]
        current_val = round(sum(all_years[latest_yr]) / len(all_years[latest_yr]), 2)

    return {
        "label": label,
        "value": current_val,
        "unit": unit,
        "trend": trend_values,
        "trend_years": trend_years,
        "country": None,
    }


def _build_trade_volume_kpi(year: int) -> dict | None:
    """Build total corridor trade volume KPI."""
    try:
        from src.api.services.trade_service import _trade_flows
    except Exception:
        return None

    yearly_totals: dict[int, float] = {}
    for _commodity, df in _trade_flows.items():
        if df is None or df.empty:
            continue
        for yr in df["year"].unique():
            mask = df["year"] == yr
            total = df.loc[mask, "trade_value_usd"].sum()
            yearly_totals[yr] = yearly_totals.get(yr, 0) + float(total)

    if not yearly_totals:
        return None

    trend_years = sorted(yearly_totals.keys())
    # Convert to billions for display
    trend_values = [round(yearly_totals[y] / 1e9, 2) for y in trend_years]
    current = yearly_totals.get(year)
    current_val = round(current / 1e9, 2) if current else (trend_values[-1] if trend_values else None)

    return {
        "label": "Trade Volume",
        "value": current_val,
        "unit": "B USD",
        "trend": trend_values,
        "trend_years": trend_years,
        "country": None,
    }


def _build_risk_kpi(year: int) -> dict | None:
    """Build corridor risk score from ACLED event counts."""
    try:
        from src.api.services.acled_service import get_conflict_events
    except Exception:
        return None

    # Get events for all years to build trend
    all_result = get_conflict_events()
    features = all_result.get("features", [])
    if not features:
        return None

    yearly_counts: dict[int, int] = {}
    for f in features:
        yr = f.get("properties", {}).get("year")
        if yr:
            yearly_counts[yr] = yearly_counts.get(yr, 0) + 1

    if not yearly_counts:
        return None

    trend_years = sorted(yearly_counts.keys())
    trend_values = [yearly_counts[y] for y in trend_years]
    current = yearly_counts.get(year, trend_values[-1] if trend_values else 0)

    return {
        "label": "Conflict Events",
        "value": current,
        "unit": "events",
        "trend": trend_values,
        "trend_years": trend_years,
        "country": None,
    }


def _build_infra_readiness_kpi() -> dict | None:
    """Build infrastructure readiness score from roads, ports, power data."""
    try:
        from src.api.services.infrastructure_enriched_service import get_roads, get_ports, get_power
    except Exception:
        return None

    scores: list[float] = []

    # Road quality: % of roads in good condition
    try:
        roads = get_roads()
        by_country = roads.get("by_country", {})
        for _country, data in by_country.items():
            condition = data.get("condition", {})
            total = sum(condition.values())
            good = condition.get("good", 0)
            if total > 0:
                scores.append(good / total * 100)
    except Exception:
        pass

    # Port capacity utilization average
    try:
        ports = get_ports()
        for p in ports:
            util = p.get("capacity_utilization_pct")
            if util:
                try:
                    scores.append(float(util))
                except (ValueError, TypeError):
                    pass
    except Exception:
        pass

    if not scores:
        return None

    avg_score = round(sum(scores) / len(scores), 1)

    return {
        "label": "Infrastructure Score",
        "value": avg_score,
        "unit": "%",
        "trend": [],
        "trend_years": [],
        "country": None,
    }


# ── Nightlights ────────────────────────────────────────────────────────────────

def _get_nightlights_url(year: int) -> str | None:
    """Fetch GEE nightlights tile URL for a given year.

    Falls back to NASA GIBS VIIRS Black Marble tiles when GEE is unavailable.
    """
    # Try GEE first
    try:
        from src.api.services import gee_service
        result = gee_service.get_nightlights(year, 6)  # June composite
        url = result.get("tile_url")
        if url:
            return url
    except Exception as exc:
        logger.debug("GEE nightlights unavailable: %s", exc)

    # Fallback: NASA GIBS VIIRS Black Marble (free, no auth required)
    # Yearly composite showing nighttime lights; reliable at all zoom levels.
    # {z}/{y}/{x} placeholders filled by MapLibre on the frontend.
    return (
        "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/"
        "VIIRS_Black_Marble/default/2016-01-01/"
        "GoogleMapsCompatible_Level8/{z}/{y}/{x}.png"
    )


# ── Data availability ──────────────────────────────────────────────────────────

def _get_data_availability() -> dict[str, list[int]]:
    """Report which years have data for each layer."""
    availability: dict[str, list[int]] = {}

    # Trade
    try:
        from src.api.services.trade_service import _trade_flows
        trade_years: set[int] = set()
        for _commodity, df in _trade_flows.items():
            if df is not None and not df.empty and "year" in df.columns:
                trade_years.update(df["year"].unique().tolist())
        availability["trade"] = sorted(trade_years)
    except Exception:
        availability["trade"] = []

    # ACLED conflict
    try:
        from src.api.services.acled_service import get_conflict_events
        result = get_conflict_events()
        features = result.get("features", [])
        conflict_years: set[int] = set()
        for f in features:
            yr = f.get("properties", {}).get("year")
            if yr:
                conflict_years.add(yr)
        availability["conflict"] = sorted(conflict_years)
    except Exception:
        availability["conflict"] = []

    # Nightlights (VIIRS available 2012+)
    availability["nightlights"] = list(range(2012, 2026))

    # Macro/KPIs
    try:
        from src.api.services.macro_enriched_service import get_indicators
        records = get_indicators()
        macro_years: set[int] = set()
        for r in records:
            wb = r.get("worldbank_indicators", {})
            for _ind, series in wb.items():
                for yr_str in series.keys():
                    try:
                        macro_years.add(int(yr_str))
                    except ValueError:
                        continue
        availability["macro"] = sorted(macro_years)
    except Exception:
        availability["macro"] = []

    return availability
