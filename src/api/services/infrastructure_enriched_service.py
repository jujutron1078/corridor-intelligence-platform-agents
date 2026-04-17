"""
Infrastructure enriched service — serves roads, ports, and power grid data.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.shared.pipeline.utils import DATA_DIR

logger = logging.getLogger("corridor.api.infrastructure_enriched_service")

INFRA_DATA_DIR = DATA_DIR / "infrastructure_enriched"

_roads: dict = {}
_ports: list = []
_power: list = []
_loaded = False


def init() -> None:
    """Load cached infrastructure enriched data."""
    global _roads, _ports, _power, _loaded

    # Roads summary
    roads_path = INFRA_DATA_DIR / "roads_summary.json"
    if roads_path.exists():
        _roads = json.load(open(roads_path, encoding="utf-8"))
        by_country = _roads.get("by_country", {})
        logger.info(
            "Infrastructure service loaded roads: %d total segments across %d countries",
            _roads.get("total_segments", 0),
            len(by_country),
        )
    else:
        logger.warning(
            "No roads data. Run the infrastructure_enriched pipeline to generate roads_summary.json."
        )
        _roads = {}

    # Ports
    ports_path = INFRA_DATA_DIR / "ports.json"
    if ports_path.exists():
        _ports = json.load(open(ports_path, encoding="utf-8"))
        logger.info("Infrastructure service loaded ports: %d records", len(_ports))
    else:
        logger.warning(
            "No ports data. Run the infrastructure_enriched pipeline to generate ports.json."
        )
        _ports = []

    # Power — records already carry a country field (ISO3)
    power_path = INFRA_DATA_DIR / "power.json"
    if power_path.exists():
        _power = json.load(open(power_path, encoding="utf-8"))
        logger.info("Infrastructure service loaded power: %d country records", len(_power))
    else:
        logger.warning(
            "No power data. Run the infrastructure_enriched pipeline to generate power.json."
        )
        _power = []

    _loaded = True


def is_loaded() -> bool:
    return _loaded and (bool(_roads) or bool(_ports) or bool(_power))


def get_roads(country: str | None = None) -> dict[str, Any]:
    """
    Get roads summary.

    country — ISO3 code to retrieve only that country's breakdown from
              'by_country'.  When omitted the full summary dict is returned.
    """
    if not country:
        return _roads

    by_country = _roads.get("by_country", {})
    country_upper = country.upper()
    if country_upper not in by_country:
        return {}
    return {country_upper: by_country[country_upper]}


def get_ports() -> list[dict[str, Any]]:
    """Get all port records."""
    return _ports


def get_power() -> list[dict[str, Any]]:
    """Get all power grid records (one per corridor country, keyed by 'country' ISO3)."""
    return _power
