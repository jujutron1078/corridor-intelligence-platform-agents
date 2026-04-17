"""
Global Energy Monitor data downloader.

Downloads the Africa-focused Global Power Plant Database and energy tracker CSV.
Source: https://globalenergymonitor.org/
"""

from __future__ import annotations

import logging
from pathlib import Path

import requests

from src.shared.pipeline.utils import DATA_DIR, ensure_dir

logger = logging.getLogger("corridor.energy")

ENERGY_DATA_DIR = DATA_DIR / "energy"

# Global Power Plant Database (WRI) — open data, includes Africa
GPPD_URL = "https://datasets.wri.org/dataset/56a55f65-a862-49e0-a886-4f7fb8377069/resource/bd9e3716-3e90-4ae7-a14c-c55b7b8a466c/download/globalpowerplantdatabasev130.csv"


def download_power_plants() -> Path:
    """Download the Global Power Plant Database CSV."""
    ensure_dir(ENERGY_DATA_DIR)
    path = ENERGY_DATA_DIR / "global_power_plants.csv"

    if path.exists():
        logger.info("Power plant data already downloaded: %s", path)
        return path

    logger.info("Downloading Global Power Plant Database...")
    resp = requests.get(GPPD_URL, timeout=120)
    resp.raise_for_status()

    with open(path, "wb") as f:
        f.write(resp.content)

    logger.info("Downloaded power plant data: %s (%.1f MB)", path, path.stat().st_size / 1e6)
    return path
