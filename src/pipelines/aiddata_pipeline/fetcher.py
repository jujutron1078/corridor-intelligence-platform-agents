"""
AidData georeferenced development finance — corridor project data.

AidData provides geocoded international development finance tracking
(Chinese, World Bank, AfDB, etc.). Since bulk download requires registration,
this module uses curated reference data for corridor countries with real
project examples.

Source: https://www.aiddata.org/
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.shared.pipeline.utils import DATA_DIR, ensure_dir

logger = logging.getLogger("corridor.aiddata")

# -- Configuration -----------------------------------------------------------

AIDDATA_DATA_DIR = DATA_DIR / "aiddata"

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
    path = AIDDATA_DATA_DIR / "development_projects.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            _seed_cache = json.load(f)
            return _seed_cache
    return {}


# -- Fetch functions ----------------------------------------------------------

def fetch_corridor_projects() -> list[dict[str, Any]]:
    """
    Return georeferenced development finance projects for corridor countries.

    Uses curated reference data since AidData bulk downloads require
    registration. Returns projects sorted by country and year.
    """
    ref = _load_seed().get("projects", [])
    logger.info("Loading AidData corridor reference projects (%d records)", len(ref))
    projects = sorted(
        ref,
        key=lambda p: (p["country_iso3"], p["year"]),
    )
    return projects


# -- Persistence --------------------------------------------------------------

def save_projects(data: list[dict[str, Any]]) -> Path:
    """Save corridor project data as JSON."""
    ensure_dir(AIDDATA_DATA_DIR)
    path = AIDDATA_DATA_DIR / "corridor_projects.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved AidData corridor projects: %s (%d records)", path, len(data))
    return path


def load_projects() -> list[dict[str, Any]]:
    """Load cached corridor project data from disk."""
    path = AIDDATA_DATA_DIR / "corridor_projects.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -- Query helpers ------------------------------------------------------------

def get_projects_by_country(
    data: list[dict[str, Any]],
    country_iso3: str,
) -> list[dict[str, Any]]:
    """Filter projects by country ISO3 code."""
    return [p for p in data if p["country_iso3"] == country_iso3.upper()]


def get_projects_by_sector(
    data: list[dict[str, Any]],
    sector: str,
) -> list[dict[str, Any]]:
    """Filter projects by sector (transport, energy, mining, agriculture, etc.)."""
    return [p for p in data if p["sector"].lower() == sector.lower()]


def get_projects_by_donor(
    data: list[dict[str, Any]],
    donor: str,
) -> list[dict[str, Any]]:
    """Filter projects by donor name (AfDB, World Bank, IFC, EU, China, etc.)."""
    return [p for p in data if p["donor"].lower() == donor.lower()]
