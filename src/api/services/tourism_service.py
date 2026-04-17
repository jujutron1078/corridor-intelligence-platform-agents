"""
Tourism service — serves corridor country tourism indicator data.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.shared.pipeline.utils import DATA_DIR

logger = logging.getLogger("corridor.api.tourism_service")

TOURISM_DATA_DIR = DATA_DIR / "tourism"

# Maps long country names (as used in the JSON) to ISO3 codes.
_NAME_TO_ISO3: dict[str, str] = {
    "Côte d'Ivoire": "CIV",
    "Ghana": "GHA",
    "Togo": "TGO",
    "Benin": "BEN",
    "Nigeria": "NGA",
}

_data: dict = {}   # keyed by ISO3 code after normalisation
_loaded = False


def init() -> None:
    """Load and normalise cached tourism data."""
    global _data, _loaded

    path = TOURISM_DATA_DIR / "tourism.json"
    if path.exists():
        raw: dict = json.load(open(path, encoding="utf-8"))
        for name, indicators in raw.items():
            iso3 = _NAME_TO_ISO3.get(name, name)
            _data[iso3] = indicators
        logger.info("Tourism service loaded: %d countries", len(_data))
    else:
        logger.warning(
            "No tourism data. Run the tourism pipeline to generate tourism.json."
        )
        _data = {}

    _loaded = True


def is_loaded() -> bool:
    return _loaded and bool(_data)


def get_indicators(country: str | None = None) -> dict[str, Any]:
    """
    Get tourism indicators, optionally filtered to a single country.

    country — ISO3 code (e.g. 'CIV', 'GHA').
    Returns a dict of {iso3: indicators} or a single country's indicators dict.
    """
    if country:
        country_upper = country.upper()
        if country_upper not in _data:
            return {}
        return {country_upper: _data[country_upper]}

    return _data


def get_comparison() -> dict[str, Any]:
    """
    Return all countries' tourism indicators side-by-side.
    """
    return _data
