"""
Projects enriched service — serves corridor infrastructure project data.
Includes World Bank, AfDB/PIDA, and EU Regional Business Forum 2026 projects.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.shared.pipeline.utils import DATA_DIR

logger = logging.getLogger("corridor.api.projects_enriched_service")

PROJECTS_DATA_DIR = DATA_DIR / "projects_enriched"

_data: list = []
_loaded = False


def init() -> None:
    """Load cached projects enriched data."""
    global _data, _loaded

    path = PROJECTS_DATA_DIR / "projects.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            _data = json.load(f)
        logger.info("Projects enriched service loaded: %d projects", len(_data))
    else:
        logger.warning(
            "No projects data. Run the projects_enriched pipeline to generate projects.json."
        )
        _data = []

    _loaded = True


def is_loaded() -> bool:
    return _loaded and bool(_data)


def get_projects(
    country: str | None = None,
    sector: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get project records, optionally filtered by country code, sector, or status.

    country — ISO3 code checked for membership in each project's 'countries' list.
    sector  — case-insensitive substring match against the 'sector' field.
    status  — case-insensitive exact match against the 'status' field.
    """
    records = _data

    if country:
        country_upper = country.upper()
        records = [
            r for r in records
            if country_upper in [c.upper() for c in r.get("countries", [])]
        ]
    if sector:
        records = [
            r for r in records
            if sector.lower() in r.get("sector", "").lower()
        ]
    if status:
        records = [
            r for r in records
            if r.get("status", "").lower() == status.lower()
        ]

    return records


def get_timeline() -> dict[str, list[dict[str, Any]]]:
    """
    Return projects grouped by their expected_completion year.

    Projects without an expected_completion value are grouped under 'unknown'.
    """
    timeline: dict[str, list] = {}

    for r in _data:
        completion = r.get("expected_completion")
        if completion:
            # Accept full date strings (e.g. '2027-12') or plain years
            year = str(completion).split("-")[0]
        else:
            year = "unknown"

        if year not in timeline:
            timeline[year] = []
        timeline[year].append(r)

    # Return sorted with 'unknown' at the end if present
    unknown = timeline.pop("unknown", None)
    sorted_timeline = dict(sorted(timeline.items()))
    if unknown is not None:
        sorted_timeline["unknown"] = unknown

    return sorted_timeline


# Static policy summary per country (avoids service dependency at call time)
_POLICY_SUMMARY: dict[str, dict] = {
    "CIV": {"name": "Côte d'Ivoire", "tax": "5yr", "customs": True, "vat": True, "epz": "0%", "eia": "90d", "local": "10%",
            "priorities": ["agribusiness", "mining", "energy", "infrastructure", "manufacturing", "ict", "tourism"]},
    "GHA": {"name": "Ghana", "tax": "5yr (10yr rural)", "customs": True, "vat": True, "epz": "0%", "eia": "120d", "local": "10%",
            "priorities": ["agriculture", "manufacturing", "mining", "energy", "tourism", "ict", "infrastructure"]},
    "NGA": {"name": "Nigeria", "tax": "3yr", "customs": True, "vat": False, "epz": "0%", "eia": "90d", "local": "5%",
            "priorities": ["agriculture", "manufacturing", "mining", "infrastructure", "energy", "ict", "healthcare"]},
    "BEN": {"name": "Benin", "tax": "3yr", "customs": True, "vat": True, "epz": "0%", "eia": "90d", "local": "20%",
            "priorities": ["agriculture", "cotton", "port", "logistics", "tourism", "manufacturing", "energy"]},
    "TGO": {"name": "Togo", "tax": "5yr", "customs": True, "vat": True, "epz": "0%", "eia": "60d", "local": "15%",
            "priorities": ["logistics", "port", "phosphate", "mining", "agriculture", "manufacturing", "energy", "tourism"]},
}

_SECTOR_KEYWORDS: dict[str, list[str]] = {
    "transport": ["infrastructure", "logistics", "port"],
    "urban transport": ["infrastructure", "transport"],
    "logistics": ["logistics", "port", "infrastructure"],
    "ports/waterways": ["port", "logistics", "infrastructure"],
    "energy": ["energy"], "energy transmission and distribution": ["energy", "infrastructure"],
    "renewable energy": ["energy"], "other energy and extractives": ["energy", "mining"],
    "agro-industry": ["agriculture", "agribusiness", "cotton"],
    "trade": ["manufacturing"], "water supply": ["infrastructure"],
    "social protection": ["healthcare"], "digital": ["ict"],
    "other agriculture, fishing and forestry": ["agriculture"],
}


def _get_policy_for_project(sector: str, countries: list[str]) -> str:
    """Build a policy context string for a project based on sector and countries."""
    lines = []
    sector_lower = sector.lower()
    keywords = _SECTOR_KEYWORDS.get(sector_lower, [sector_lower.split()[0] if sector else ""])

    for code in countries:
        pol = _POLICY_SUMMARY.get(code.upper())
        if not pol:
            continue
        priorities = pol["priorities"]
        is_priority = any(kw in p for kw in keywords for p in priorities)

        parts = [pol["name"] + ":"]
        if is_priority:
            parts.append("PRIORITY SECTOR")
        parts.append(f"Tax holiday {pol['tax']}")
        if pol["customs"]:
            parts.append("Customs exempt")
        if pol["vat"]:
            parts.append("VAT exempt")
        parts.append(f"EPZ tax {pol['epz']}")
        parts.append(f"EIA {pol['eia']}")
        parts.append(f"Local employ >={pol['local']}")
        lines.append(" | ".join(parts))

    return " // ".join(lines) if lines else ""


def get_geojson() -> dict[str, Any]:
    """Return projects as GeoJSON FeatureCollection for map rendering with policy context."""
    # Always read from disk for GeoJSON — _data may lack coordinates if loaded before enrichment
    path = PROJECTS_DATA_DIR / "projects.json"
    if path.exists():
        import json as _json
        with open(path, encoding="utf-8") as _f:
            source = _json.load(_f)
    else:
        source = _data

    features = []
    for r in source:
        lat = r.get("latitude")
        lon = r.get("longitude")
        if lat is None or lon is None:
            continue
        try:
            lat, lon = float(lat), float(lon)
        except (ValueError, TypeError):
            continue

        raw_sec = r.get("sector", "Other")
        if isinstance(raw_sec, dict):
            sec = raw_sec.get("Name", "Other")
        else:
            sec = str(raw_sec).replace("(Historic)", "").strip()

        countries_list = r.get("countries", [])
        policy_ctx = _get_policy_for_project(sec, countries_list)

        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "name": r.get("name", "Unknown"),
                "sector": sec,
                "status": r.get("status", "Unknown"),
                "countries": ", ".join(countries_list),
                "cost_usd_million": r.get("total_cost_usd_million", 0),
                "source": r.get("source", ""),
                "type": r.get("type", ""),
                "policy": policy_ctx,
            },
        })
    return {"type": "FeatureCollection", "features": features}


def get_summary() -> dict[str, Any]:
    """
    Return summary statistics: total projects, total cost, and breakdowns
    by sector, status, and country.
    """
    total_cost: float = 0.0
    by_sector: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_country: dict[str, int] = {}

    for r in _data:
        raw_cost = r.get("total_cost_usd_million") or 0
        try:
            cost = float(str(raw_cost).replace(",", ""))
        except (ValueError, TypeError):
            cost = 0.0
        # Normalize: values > 100_000 are likely raw USD, not millions
        if cost > 100_000:
            cost = cost / 1_000_000
        total_cost += cost

        raw_sec = r.get("sector", "UNKNOWN")
        # Handle World Bank sector format: {'Name': '...', 'Percent': N} or plain string
        if isinstance(raw_sec, dict):
            sec = raw_sec.get("Name", "UNKNOWN")
        elif isinstance(raw_sec, str) and raw_sec.startswith("{"):
            # String representation of dict
            try:
                import ast
                sec = ast.literal_eval(raw_sec).get("Name", "UNKNOWN")
            except (ValueError, SyntaxError):
                sec = raw_sec
        else:
            sec = str(raw_sec)
        # Clean up historic prefix
        sec = sec.replace("(Historic)", "").strip()
        by_sector[sec] = by_sector.get(sec, 0) + 1

        st = r.get("status", "UNKNOWN")
        by_status[st] = by_status.get(st, 0) + 1

        for c in r.get("countries", []):
            by_country[c] = by_country.get(c, 0) + 1

    return {
        "total_projects": len(_data),
        "total_cost_usd_million": round(total_cost, 2),
        "by_sector": by_sector,
        "by_status": by_status,
        "by_country": by_country,
    }
# policy-mapping v2
