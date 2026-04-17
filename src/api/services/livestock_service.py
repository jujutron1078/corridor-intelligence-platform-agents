"""
Livestock service — serves FAO GLW 3 livestock density data.
"""

from __future__ import annotations

import logging
from typing import Any

from src.pipelines.livestock_pipeline.processor import load_stats

logger = logging.getLogger("corridor.api.livestock_service")

_stats: dict[str, Any] = {}
_loaded = False


def init() -> None:
    """Load cached livestock statistics."""
    global _stats, _loaded
    _stats = load_stats()
    if _stats:
        logger.info("Livestock service loaded: %d species", len(_stats))
    else:
        logger.warning("No livestock data cached. Run livestock pipeline to populate.")
    _loaded = True


def is_loaded() -> bool:
    return _loaded and bool(_stats)


def get_livestock(species: str | None = None) -> dict[str, Any]:
    """
    Get livestock density statistics.

    Args:
        species: Optional filter: cattle, goats, sheep, chickens, pigs

    Returns dict with density stats per species.
    """
    if species:
        data = _stats.get(species.lower())
        if data:
            return {"species": species.lower(), **data}
        return {"error": f"No data for species: {species}. Available: {list(_stats.keys())}"}

    return {
        "total_species": len(_stats),
        "species": _stats,
    }
