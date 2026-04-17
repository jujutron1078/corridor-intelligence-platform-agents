"""
Connectivity service — serves Ookla Speedtest internet coverage data.
"""

from __future__ import annotations

import logging
from typing import Any

from src.pipelines.connectivity_pipeline.processor import load_connectivity, get_connectivity_summary

logger = logging.getLogger("corridor.api.connectivity_service")

_mobile: dict = {}
_fixed: dict = {}
_loaded = False


def init() -> None:
    """Load cached connectivity data."""
    global _mobile, _fixed, _loaded
    _mobile = load_connectivity("mobile")
    _fixed = load_connectivity("fixed")

    mobile_count = len(_mobile.get("features", []))
    fixed_count = len(_fixed.get("features", []))

    if mobile_count or fixed_count:
        logger.info("Connectivity service loaded: %d mobile tiles, %d fixed tiles", mobile_count, fixed_count)
    else:
        logger.warning("No connectivity data cached. Run connectivity pipeline to populate.")
    _loaded = True


def is_loaded() -> bool:
    return _loaded and (bool(_mobile.get("features")) or bool(_fixed.get("features")))


def get_connectivity(network_type: str = "mobile") -> dict[str, Any]:
    """
    Get internet connectivity data.

    Args:
        network_type: "mobile" or "fixed"

    Returns GeoJSON with speed/latency stats.
    """
    data = _mobile if network_type == "mobile" else _fixed
    summary = get_connectivity_summary(data)

    return {
        "type": "FeatureCollection",
        "features": data.get("features", []),
        "summary": summary,
        "network_type": network_type,
    }
