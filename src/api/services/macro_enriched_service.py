"""
Macro enriched service — serves macroeconomic indicators, trade composition,
tax rates, and ease-of-doing-business data.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.shared.pipeline.utils import DATA_DIR

logger = logging.getLogger("corridor.api.macro_enriched_service")

MACRO_DATA_DIR = DATA_DIR / "macro_enriched"

_data: list = []
_loaded = False


def init() -> None:
    """Load cached macro enriched data."""
    global _data, _loaded

    path = MACRO_DATA_DIR / "macro.json"
    if path.exists():
        _data = json.load(open(path, encoding="utf-8"))
        logger.info("Macro enriched service loaded: %d country records", len(_data))
    else:
        logger.warning(
            "No macro data. Run the macro_enriched pipeline to generate macro.json."
        )
        _data = []

    _loaded = True


def is_loaded() -> bool:
    return _loaded and bool(_data)


def get_indicators(country: str | None = None) -> list[dict[str, Any]]:
    """
    Get macro indicator records, optionally filtered by country code.

    country — ISO3 code (e.g. 'CIV', 'NGA').
    Returns the full list when no filter is applied.
    """
    if not country:
        return _data

    country_upper = country.upper()
    return [
        r for r in _data
        if r.get("country_code", "").upper() == country_upper
    ]


def get_trade_composition() -> list[dict[str, Any]]:
    """
    Extract export composition data for every country.

    Returns a list of dicts, each containing country_code, country_name,
    and export_composition.
    """
    return [
        {
            "country_code": r.get("country_code"),
            "country_name": r.get("country_name"),
            "export_composition": r.get("export_composition", {}),
        }
        for r in _data
    ]
