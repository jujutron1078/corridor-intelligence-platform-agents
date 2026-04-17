"""
WAPP (West African Power Pool) Master Plan reference data.

Reference data loaded from seed.json (WAPP Master Plan documentation).
Covers cross-border interconnections, generation targets, and trade volumes
for the Abidjan-Lagos corridor countries.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.shared.pipeline.utils import DATA_DIR, ensure_dir

logger = logging.getLogger("corridor.wapp")

# ── Configuration ──────────────────────────────────────────────────────────

CORRIDOR_COUNTRIES = ["NGA", "BEN", "TGO", "GHA", "CIV"]

COUNTRY_NAMES = {
    "NGA": "Nigeria",
    "BEN": "Benin",
    "TGO": "Togo",
    "GHA": "Ghana",
    "CIV": "Côte d'Ivoire",
}

WAPP_DATA_DIR = DATA_DIR / "wapp"

# ── Seed data loader ──────────────────────────────────────────────────────

_seed_cache: dict | None = None


def _load_seed() -> dict:
    """Load seed/reference data from disk (cached after first read)."""
    global _seed_cache
    if _seed_cache is not None:
        return _seed_cache
    path = WAPP_DATA_DIR / "master_plan.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            _seed_cache = json.load(f)
            return _seed_cache
    return {}


# ── Access functions ───────────────────────────────────────────────────────

def get_interconnections(country_iso3: str | None = None) -> list[dict[str, Any]]:
    """
    Get WAPP interconnection data, optionally filtered by country.

    Args:
        country_iso3: If provided, return only interconnections involving this country.

    Returns:
        List of interconnection dicts.
    """
    if country_iso3:
        iso = country_iso3.upper()
        return [
            ic for ic in _load_seed().get("interconnections", [])
            if ic["from_country"] == iso or ic["to_country"] == iso
        ]
    return list(_load_seed().get("interconnections", []))


def get_generation_targets() -> dict[str, dict[str, Any]]:
    """
    Get WAPP generation capacity targets by country.

    Returns:
        Dict keyed by country ISO3 with generation target data.
    """
    return dict(_load_seed().get("generation_targets", {}))


def get_trade_volumes() -> dict[str, dict[str, Any]]:
    """
    Get cross-border electricity trade volumes by country pair.

    Returns:
        Dict keyed by country pair (e.g. "NGA-BEN") with trade volume data.
    """
    return dict(_load_seed().get("trade_volumes", {}))


# ── Persistence ────────────────────────────────────────────────────────────

def save_wapp_data(data: dict[str, Any] | None = None) -> Path:
    """
    Save WAPP Master Plan data as JSON.

    If data is None, saves the built-in reference data.
    """
    ensure_dir(WAPP_DATA_DIR)
    if data is None:
        seed = _load_seed()
        data = {
            "interconnections": seed.get("interconnections", []),
            "generation_targets": seed.get("generation_targets", {}),
            "trade_volumes": seed.get("trade_volumes", {}),
        }
    path = WAPP_DATA_DIR / "master_plan.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved WAPP Master Plan data: %s", path)
    return path


def load_wapp_data() -> dict[str, Any]:
    """
    Load cached WAPP Master Plan data from disk.

    Falls back to built-in reference data if no file exists.
    """
    path = WAPP_DATA_DIR / "master_plan.json"
    if not path.exists():
        seed = _load_seed()
        return {
            "interconnections": seed.get("interconnections", []),
            "generation_targets": seed.get("generation_targets", {}),
            "trade_volumes": seed.get("trade_volumes", {}),
        }
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
