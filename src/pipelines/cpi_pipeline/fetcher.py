"""
Transparency International Corruption Perceptions Index client — CPI scores for corridor countries.

CPI scores range from 0 (highly corrupt) to 100 (very clean).
Loads reference data from data/cpi/seed.json as a reliable fallback.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from src.shared.pipeline.utils import DATA_DIR, ensure_dir, retry

logger = logging.getLogger("corridor.cpi")

# ── Configuration ──────────────────────────────────────────────────────────

# Transparency International CPI data download endpoint
CPI_URL = "https://images.transparencycdn.org/images/CPI2024_Global_Results_Trends.csv"

CORRIDOR_COUNTRIES = {
    "NGA": "Nigeria",
    "BEN": "Benin",
    "TGO": "Togo",
    "GHA": "Ghana",
    "CIV": "Côte d'Ivoire",
}

CPI_DATA_DIR = DATA_DIR / "cpi"

# ── Seed / reference data loader ──────────────────────────────────────────

_seed_cache: dict | None = None


def _load_seed() -> dict:
    """Load seed/reference data from disk (cached after first read)."""
    global _seed_cache
    if _seed_cache is not None:
        return _seed_cache
    path = CPI_DATA_DIR / "corruption_scores.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            _seed_cache = json.load(f)
            return _seed_cache
    return {}


# ── API fetch functions ──────────────────────────────────────────────────────

def fetch_cpi_scores() -> list[dict[str, Any]]:
    """
    Fetch CPI scores for corridor countries.

    Attempts to download from Transparency International's CSV.
    Falls back to hardcoded reference data if download fails.

    Returns a list of {country_iso3, country, score, rank, year} dicts.
    """
    try:
        records = _fetch_from_csv()
        if records:
            logger.info("Fetched %d CPI records from Transparency International", len(records))
            return records
    except Exception as exc:
        logger.warning("Failed to fetch CPI from TI, using reference data: %s", exc)

    # Fallback to reference data
    logger.info("Using CPI reference data (2024)")
    return list(_load_seed().get("scores", {}).values())


def _fetch_from_csv() -> list[dict[str, Any]]:
    """
    Download and parse CPI CSV from Transparency International.

    Returns corridor country records or empty list on failure.
    """
    def _do_fetch():
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; CorridorIntelligencePlatform/1.0)',
            'Accept': 'text/csv,application/octet-stream',
        }
        resp = requests.get(CPI_URL, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.text

    csv_text = retry(_do_fetch, max_retries=3, backoff=2.0)

    if not csv_text:
        return []

    records = []
    lines = csv_text.strip().split("\n")

    # Find header row and parse
    header = None
    for i, line in enumerate(lines):
        # Look for ISO3 column header
        if "ISO3" in line or "iso3" in line.lower():
            header = [col.strip().strip('"') for col in line.split(",")]
            data_lines = lines[i + 1:]
            break

    if not header:
        logger.warning("Could not find header row in CPI CSV")
        return []

    # Find relevant column indices
    iso3_idx = None
    score_idx = None
    rank_idx = None
    country_idx = None

    for idx, col in enumerate(header):
        col_lower = col.lower()
        if col_lower in ("iso3", "iso"):
            iso3_idx = idx
        elif "cpi score" in col_lower or col_lower == "cpi_score_2024":
            score_idx = idx
        elif "rank" in col_lower:
            rank_idx = idx
        elif col_lower in ("country", "country / territory"):
            country_idx = idx

    if iso3_idx is None:
        logger.warning("Could not find ISO3 column in CPI CSV")
        return []

    for line in data_lines:
        cols = [col.strip().strip('"') for col in line.split(",")]
        if len(cols) <= iso3_idx:
            continue

        iso3 = cols[iso3_idx].upper()
        if iso3 not in CORRIDOR_COUNTRIES:
            continue

        record: dict[str, Any] = {
            "country_iso3": iso3,
            "country": CORRIDOR_COUNTRIES[iso3],
            "year": 2024,
        }

        if score_idx is not None and len(cols) > score_idx:
            try:
                record["score"] = int(cols[score_idx])
            except (ValueError, TypeError):
                record["score"] = _load_seed().get("scores", {})[iso3]["score"]
        else:
            record["score"] = _load_seed().get("scores", {})[iso3]["score"]

        if rank_idx is not None and len(cols) > rank_idx:
            try:
                record["rank"] = int(cols[rank_idx])
            except (ValueError, TypeError):
                record["rank"] = _load_seed().get("scores", {})[iso3]["rank"]
        else:
            record["rank"] = _load_seed().get("scores", {})[iso3]["rank"]

        records.append(record)

    return records


# ── Persistence ───────────────────────────────────────────────────────────

def save_cpi_scores(data: list[dict]) -> Path:
    """Save CPI score data as JSON."""
    ensure_dir(CPI_DATA_DIR)
    path = CPI_DATA_DIR / "cpi_scores.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved CPI scores: %s", path)
    return path


def load_cpi_scores() -> list[dict]:
    """Load cached CPI score data from disk."""
    path = CPI_DATA_DIR / "cpi_scores.json"
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed to load CPI scores: %s", exc)
        return []


def get_country_score(
    data: list[dict],
    country_iso3: str,
) -> dict[str, Any]:
    """
    Get the CPI score for a specific country.

    Returns {country_iso3, country, score, rank, year} or empty dict if not found.
    """
    country_iso3 = country_iso3.upper()
    for record in data:
        if record.get("country_iso3") == country_iso3:
            return record

    # Fallback to reference data
    ref = _load_seed().get("scores", {})
    if country_iso3 in ref:
        logger.info("Using reference CPI data for %s", country_iso3)
        return ref[country_iso3]

    return {}
