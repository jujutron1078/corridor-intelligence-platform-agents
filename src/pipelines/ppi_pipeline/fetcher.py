"""
IFC/World Bank PPI (Private Participation in Infrastructure) database fetcher.

API docs: https://ppi.worldbank.org/api/v1/ (public)
Focuses on energy and transport PPP projects in the Abidjan-Lagos corridor countries.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from src.shared.pipeline.utils import DATA_DIR, ensure_dir, retry

logger = logging.getLogger("corridor.ppi")

# ── Configuration ──────────────────────────────────────────────────────────

BASE_URL = "https://ppi.worldbank.org/api/v1"

CORRIDOR_COUNTRIES = ["NGA", "BEN", "TGO", "GHA", "CIV"]

COUNTRY_NAMES = {
    "NGA": "Nigeria",
    "BEN": "Benin",
    "TGO": "Togo",
    "GHA": "Ghana",
    "CIV": "Côte d'Ivoire",
}

PPI_DATA_DIR = DATA_DIR / "ppi"

# ── Reference data (loaded from seed.json, cached) ────────────────────────

_seed_cache: dict | None = None


def _load_seed() -> dict:
    """Load seed/reference data from disk (cached after first read)."""
    global _seed_cache
    if _seed_cache is not None:
        return _seed_cache
    path = PPI_DATA_DIR / "ppp_projects.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            _seed_cache = json.load(f)
            return _seed_cache
    return {}


# ── API fetch functions ────────────────────────────────────────────────────

def fetch_ppi_projects(
    country_iso3: str | None = None,
    sector: str | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch PPI project data from the World Bank PPI database API.

    Falls back to REFERENCE_DATA if the API is unavailable.
    Optionally filter by country_iso3 and/or sector.
    """
    try:
        url = f"{BASE_URL}/ppi"
        params: dict[str, Any] = {
            "format": "json",
        }
        if country_iso3:
            params["country"] = country_iso3.upper()
        if sector:
            params["sector"] = sector.lower()

        def _do_fetch():
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()

        data = retry(_do_fetch, max_retries=2, backoff=2.0)

        if not data or not isinstance(data, list) or len(data) == 0:
            logger.info("No PPI data returned from API, using reference data")
            return _filter_projects(_load_seed().get("projects", []), country_iso3, sector)

        # Parse API response into standardised records
        projects = []
        for item in data:
            projects.append({
                "project_id": item.get("id", ""),
                "project_name": item.get("project_name", ""),
                "country_iso3": item.get("country_iso3", ""),
                "country": item.get("country", ""),
                "sector": item.get("sector", ""),
                "sub_sector": item.get("sub_sector", ""),
                "investment_usd": item.get("total_investment", 0),
                "year_financial_close": item.get("financial_closure_year", None),
                "status": item.get("status", ""),
                "sponsor": item.get("sponsor", ""),
                "contract_type": item.get("ppi_type", ""),
                "contract_years": item.get("contract_period", None),
                "dfi_support": item.get("multilateral_support", []),
            })

        logger.info("Fetched %d PPI projects from API", len(projects))
        return projects

    except Exception as exc:
        logger.warning("PPI API unavailable (%s), using reference data", exc)
        return _filter_projects(_load_seed().get("projects", []), country_iso3, sector)


# ── Helper functions ───────────────────────────────────────────────────────

def _filter_projects(
    projects: list[dict],
    country_iso3: str | None,
    sector: str | None,
) -> list[dict]:
    """Filter projects by country and/or sector."""
    result = list(projects)
    if country_iso3:
        result = [p for p in result if p.get("country_iso3") == country_iso3.upper()]
    if sector:
        result = [p for p in result if p.get("sector", "").lower() == sector.lower()]
    return result


def get_ppi_by_sector(data: list[dict], sector: str) -> list[dict]:
    """Filter PPI project data by sector (energy, transport, telecoms, water)."""
    return [p for p in data if p.get("sector", "").lower() == sector.lower()]


def get_ppi_summary(data: list[dict]) -> dict[str, Any]:
    """
    Generate a summary of PPI project data.

    Returns dict with total_investment, by_sector, by_country, by_status, avg_contract_years.
    """
    total_investment = sum(p.get("investment_usd", 0) for p in data)

    by_sector: dict[str, dict] = {}
    for p in data:
        s = p.get("sector", "unknown")
        if s not in by_sector:
            by_sector[s] = {"count": 0, "total_investment": 0}
        by_sector[s]["count"] += 1
        by_sector[s]["total_investment"] += p.get("investment_usd", 0)

    by_country: dict[str, dict] = {}
    for p in data:
        c = p.get("country_iso3", "Unknown")
        if c not in by_country:
            by_country[c] = {"count": 0, "total_investment": 0}
        by_country[c]["count"] += 1
        by_country[c]["total_investment"] += p.get("investment_usd", 0)

    by_status: dict[str, int] = {}
    for p in data:
        st = p.get("status", "unknown")
        by_status[st] = by_status.get(st, 0) + 1

    contract_years = [p.get("contract_years", 0) for p in data if p.get("contract_years")]
    avg_contract_years = round(sum(contract_years) / len(contract_years), 1) if contract_years else 0

    return {
        "total_projects": len(data),
        "total_investment": total_investment,
        "by_sector": dict(sorted(by_sector.items())),
        "by_country": dict(sorted(by_country.items())),
        "by_status": dict(sorted(by_status.items())),
        "avg_contract_years": avg_contract_years,
    }


# ── Persistence ────────────────────────────────────────────────────────────

def save_ppi_projects(data: list[dict]) -> Path:
    """Save PPI project data as JSON."""
    ensure_dir(PPI_DATA_DIR)
    path = PPI_DATA_DIR / "ppi_projects.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved PPI projects: %s", path)
    return path


def load_ppi_projects() -> list[dict]:
    """Load cached PPI project data from disk."""
    path = PPI_DATA_DIR / "ppi_projects.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
