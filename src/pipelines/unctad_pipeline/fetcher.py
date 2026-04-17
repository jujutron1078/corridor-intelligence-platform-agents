"""
UNCTAD port statistics and maritime data — key corridor ports.

Covers major ports along the Lagos-Abidjan corridor: Lagos/Apapa/Tin Can
Island (NGA), Cotonou (BEN), Lomé (TGO), Tema/Takoradi (GHA), and
Abidjan/San Pedro (CIV).

Since UNCTAD detailed API requires authentication, this module uses curated
reference data based on publicly available port statistics.

Source: https://unctadstat.unctad.org/
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.shared.pipeline.utils import DATA_DIR, ensure_dir

logger = logging.getLogger("corridor.unctad")

# -- Configuration -----------------------------------------------------------

UNCTAD_DATA_DIR = DATA_DIR / "unctad"

CORRIDOR_COUNTRIES = {
    "NGA": "Nigeria",
    "BEN": "Benin",
    "TGO": "Togo",
    "GHA": "Ghana",
    "CIV": "Côte d'Ivoire",
}

# -- Seed data loader ---------------------------------------------------------

_seed_cache: dict | None = None


def _load_seed() -> dict:
    """Load seed/reference data from disk (cached after first read)."""
    global _seed_cache
    if _seed_cache is not None:
        return _seed_cache
    path = UNCTAD_DATA_DIR / "port_statistics.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            _seed_cache = json.load(f)
            return _seed_cache
    return {}


# -- Fetch functions ----------------------------------------------------------

def get_port_statistics(
    country_iso3: str | None = None,
) -> list[dict[str, Any]]:
    """
    Return port statistics for corridor countries.

    Uses curated reference data. Optionally filter by country ISO3 code.
    Returns ports sorted by TEU volume (descending).
    """
    ports = list(_load_seed().get("ports", []))
    if country_iso3:
        ports = [p for p in ports if p["country_iso3"] == country_iso3.upper()]

    logger.info(
        "Loaded UNCTAD port statistics: %d ports%s",
        len(ports),
        f" (filtered: {country_iso3})" if country_iso3 else "",
    )
    ports.sort(key=lambda p: -p["teu_volume"])
    return ports


# -- Persistence --------------------------------------------------------------

def save_port_statistics(data: list[dict[str, Any]]) -> Path:
    """Save port statistics data as JSON."""
    ensure_dir(UNCTAD_DATA_DIR)
    path = UNCTAD_DATA_DIR / "port_statistics.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved UNCTAD port statistics: %s (%d records)", path, len(data))
    return path


def load_port_statistics() -> list[dict[str, Any]]:
    """Load cached port statistics from disk."""
    path = UNCTAD_DATA_DIR / "port_statistics.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Handle both {"ports": [...]} wrapper and bare list formats
    if isinstance(data, dict):
        return data.get("ports", [])
    return data


# -- Query helpers ------------------------------------------------------------

def get_port_by_name(
    data: list[dict[str, Any]],
    port_name: str,
) -> dict[str, Any] | None:
    """
    Find a port by name (case-insensitive partial match).

    Returns the first matching port dict, or None if not found.
    """
    port_lower = port_name.lower()
    for port in data:
        if port_lower in port["port_name"].lower():
            return port
    return None


def get_total_throughput(
    data: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Calculate total throughput across all ports in the dataset.

    Returns {total_teu, total_cargo_tonnes, total_vessel_calls, port_count,
    by_country: {iso3: {teu, cargo_tonnes}}}.
    """
    total_teu = 0
    total_tonnes = 0
    total_calls = 0
    by_country: dict[str, dict[str, float]] = {}

    for port in data:
        total_teu += port["teu_volume"]
        total_tonnes += port["cargo_tonnes"]
        total_calls += port["vessel_calls"]

        iso3 = port["country_iso3"]
        if iso3 not in by_country:
            by_country[iso3] = {"teu": 0, "cargo_tonnes": 0}
        by_country[iso3]["teu"] += port["teu_volume"]
        by_country[iso3]["cargo_tonnes"] += port["cargo_tonnes"]

    return {
        "total_teu": total_teu,
        "total_cargo_tonnes": total_tonnes,
        "total_vessel_calls": total_calls,
        "port_count": len(data),
        "by_country": by_country,
    }
