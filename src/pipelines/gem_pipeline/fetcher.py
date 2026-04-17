"""
Global Energy Monitor (GEM) — planned and under-construction energy projects.

GEM tracks planned, announced, under construction, and shelved power projects
worldwide. This module provides curated reference data for corridor countries
covering solar, wind, gas, hydro, coal, and battery storage facilities.

Source: https://globalenergymonitor.org/
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.shared.pipeline.utils import DATA_DIR, ensure_dir

logger = logging.getLogger("corridor.gem")

# -- Configuration -----------------------------------------------------------

GEM_DATA_DIR = DATA_DIR / "gem"

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
    path = GEM_DATA_DIR / "planned_energy_projects.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            _seed_cache = json.load(f)
            return _seed_cache
    return {}


# -- Fetch functions ----------------------------------------------------------

def fetch_planned_projects(
    country_iso3: str | None = None,
) -> list[dict[str, Any]]:
    """
    Return energy projects tracked by Global Energy Monitor for corridor countries.

    Uses curated reference data. Optionally filter by country ISO3 code.
    Returns projects sorted by country and capacity (descending).
    """
    projects = list(_load_seed().get("projects", []))
    if country_iso3:
        projects = [p for p in projects if p["country_iso3"] == country_iso3.upper()]

    logger.info(
        "Loaded GEM energy projects: %d records%s",
        len(projects),
        f" (filtered: {country_iso3})" if country_iso3 else "",
    )
    projects.sort(key=lambda p: (p["country_iso3"], -p["capacity_mw"]))
    return projects


# -- Persistence --------------------------------------------------------------

def save_projects(data: list[dict[str, Any]]) -> Path:
    """Save planned project data as JSON."""
    ensure_dir(GEM_DATA_DIR)
    path = GEM_DATA_DIR / "planned_projects.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved GEM planned projects: %s (%d records)", path, len(data))
    return path


def load_projects() -> list[dict[str, Any]]:
    """Load cached planned project data from disk."""
    path = GEM_DATA_DIR / "planned_projects.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -- Query helpers ------------------------------------------------------------

def get_projects_by_status(
    data: list[dict[str, Any]],
    status: str,
) -> list[dict[str, Any]]:
    """
    Filter projects by status.

    Valid statuses: announced, pre-construction, construction, operating, shelved.
    """
    return [p for p in data if p["status"].lower() == status.lower()]


def get_total_planned_capacity(
    data: list[dict[str, Any]],
    country_iso3: str | None = None,
) -> dict[str, Any]:
    """
    Calculate total planned capacity with breakdown by fuel type.

    Includes only non-operating projects (announced, pre-construction, construction).
    Optionally filter by country ISO3 code.

    Returns {total_mw, by_fuel: {fuel_type: mw}, project_count}.
    """
    planned_statuses = {"announced", "pre-construction", "construction"}

    projects = data
    if country_iso3:
        projects = [p for p in projects if p["country_iso3"] == country_iso3.upper()]

    planned = [p for p in projects if p["status"].lower() in planned_statuses]

    by_fuel: dict[str, float] = {}
    for p in planned:
        fuel = p["fuel_type"]
        by_fuel[fuel] = by_fuel.get(fuel, 0) + p["capacity_mw"]

    return {
        "total_mw": sum(p["capacity_mw"] for p in planned),
        "by_fuel": by_fuel,
        "project_count": len(planned),
    }
