"""
HDX Health Facilities downloader.

Source: https://data.humdata.org/dataset/health-facilities-in-sub-saharan-africa
Format: Excel spreadsheet with geocoded facility locations.
"""

from __future__ import annotations

import logging
from pathlib import Path

import requests

from src.shared.pipeline.utils import DATA_DIR, ensure_dir

logger = logging.getLogger("corridor.health")

HEALTH_DATA_DIR = DATA_DIR / "health"

# HDX sub-Saharan Africa health facilities dataset
HDX_HEALTH_URL = "https://data.humdata.org/dataset/health-facilities-in-sub-saharan-africa"

# Direct download URLs per country (HDX API)
COUNTRY_URLS = {
    "NGA": "https://data.humdata.org/dataset/nigeria-healthsites/resource_download/",
    "BEN": "https://data.humdata.org/dataset/benin-healthsites/resource_download/",
    "TGO": "https://data.humdata.org/dataset/togo-healthsites/resource_download/",
    "GHA": "https://data.humdata.org/dataset/ghana-healthsites/resource_download/",
    "CIV": "https://data.humdata.org/dataset/cote-d-ivoire-healthsites/resource_download/",
}

# healthsites.io API (free, no key needed for basic access)
HEALTHSITES_API_URL = "https://healthsites.io/api/v3/facilities/"


def download_healthsites(country_iso: str = "NGA") -> list[dict]:
    """
    Download health facility data from healthsites.io API.

    This is the most reliable free source for geocoded health facilities.
    """
    facilities = []
    page = 1
    per_page = 100

    # Map ISO3 to ISO2 for healthsites API
    iso3_to_iso2 = {"NGA": "NG", "BEN": "BJ", "TGO": "TG", "GHA": "GH", "CIV": "CI"}
    country_code = iso3_to_iso2.get(country_iso, country_iso)

    while True:
        try:
            resp = requests.get(
                HEALTHSITES_API_URL,
                params={
                    "country": country_code,
                    "page": page,
                    "page_size": per_page,
                    "output": "json",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            if not data or (isinstance(data, list) and len(data) == 0):
                break
            if isinstance(data, dict) and "results" in data:
                results = data["results"]
            elif isinstance(data, list):
                results = data
            else:
                break

            if not results:
                break

            facilities.extend(results)
            logger.info("  %s page %d: %d facilities", country_iso, page, len(results))

            if len(results) < per_page:
                break
            page += 1

        except Exception as exc:
            logger.warning("healthsites.io API error for %s page %d: %s", country_iso, page, exc)
            break

    return facilities


def download_all_countries() -> dict[str, list[dict]]:
    """Download health facilities for all corridor countries."""
    all_facilities = {}
    for iso3 in ["NGA", "BEN", "TGO", "GHA", "CIV"]:
        logger.info("Downloading health facilities for %s...", iso3)
        facilities = download_healthsites(iso3)
        all_facilities[iso3] = facilities
        logger.info("  %s: %d facilities", iso3, len(facilities))
    return all_facilities
