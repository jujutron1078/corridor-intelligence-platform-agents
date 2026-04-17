"""
Stakeholders registry service — serves corridor stakeholder organisation data.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.shared.pipeline.utils import DATA_DIR

logger = logging.getLogger("corridor.api.stakeholders_registry_service")

STAKEHOLDERS_DATA_DIR = DATA_DIR / "stakeholders_registry"

_data: list = []
_loaded = False


def init() -> None:
    """Load cached stakeholders data."""
    global _data, _loaded

    path = STAKEHOLDERS_DATA_DIR / "stakeholders.json"
    if path.exists():
        _data = json.load(open(path, encoding="utf-8"))
        logger.info("Stakeholders registry service loaded: %d stakeholders", len(_data))
    else:
        logger.warning(
            "No stakeholders data. Run the stakeholders pipeline to generate stakeholders.json."
        )
        _data = []

    _loaded = True


def is_loaded() -> bool:
    return _loaded and bool(_data)


def get_stakeholders(
    country: str | None = None,
    org_type: str | None = None,
    sector: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get stakeholders, optionally filtered by country code, organisation type,
    or sector (matched against the 'sectors' field where present).
    """
    records = _data

    if country:
        records = [
            r for r in records
            if r.get("country_code", "").upper() == country.upper()
        ]
    if org_type:
        records = [
            r for r in records
            if org_type.lower() in r.get("org_type", "").lower()
        ]
    if sector:
        sector_lower = sector.lower()
        records = [
            r for r in records
            if sector_lower in (
                " ".join(r["sectors"]).lower() if isinstance(r.get("sectors"), list)
                else r.get("sectors", "").lower()
            )
        ]

    return records


def get_summary() -> dict[str, Any]:
    """
    Return summary statistics: total count, breakdown by country and org type.
    """
    by_country: dict[str, int] = {}
    by_type: dict[str, int] = {}

    for r in _data:
        cc = r.get("country_code", "UNKNOWN")
        by_country[cc] = by_country.get(cc, 0) + 1

        ot = r.get("org_type", "UNKNOWN")
        by_type[ot] = by_type.get(ot, 0) + 1

    return {
        "total": len(_data),
        "by_country": by_country,
        "by_type": by_type,
    }
