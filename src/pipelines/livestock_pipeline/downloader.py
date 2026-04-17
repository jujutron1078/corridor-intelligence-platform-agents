"""
FAO GLW 3 data downloader.

Downloads Gridded Livestock of the World GeoTIFF data from Harvard Dataverse.
Requires rasterio for processing.
"""

from __future__ import annotations

import logging
from pathlib import Path

import requests

from src.shared.pipeline.utils import DATA_DIR, ensure_dir

logger = logging.getLogger("corridor.livestock")

LIVESTOCK_DATA_DIR = DATA_DIR / "livestock"

# FAO GLW 3 data URLs (Harvard Dataverse)
# These are the 10km resolution global grids
SPECIES_URLS = {
    "cattle": "https://dataverse.harvard.edu/api/access/datafile/3985026",
    "goats": "https://dataverse.harvard.edu/api/access/datafile/3985031",
    "sheep": "https://dataverse.harvard.edu/api/access/datafile/3985036",
    "chickens": "https://dataverse.harvard.edu/api/access/datafile/3985016",
    "pigs": "https://dataverse.harvard.edu/api/access/datafile/3985033",
}


def download_species(species: str, url: str) -> Path | None:
    """Download a single species GeoTIFF."""
    ensure_dir(LIVESTOCK_DATA_DIR)
    path = LIVESTOCK_DATA_DIR / f"{species}.tif"

    if path.exists():
        logger.info("Livestock %s already downloaded: %s", species, path)
        return path

    logger.info("Downloading %s livestock data...", species)
    try:
        resp = requests.get(url, timeout=300, stream=True)
        resp.raise_for_status()
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info("Downloaded %s: %s (%.1f MB)", species, path, path.stat().st_size / 1e6)
        return path
    except Exception as exc:
        logger.error("Failed to download %s: %s", species, exc)
        return None


def download_all() -> dict[str, Path]:
    """Download all species GeoTIFFs."""
    results = {}
    for species, url in SPECIES_URLS.items():
        path = download_species(species, url)
        if path:
            results[species] = path
    return results
