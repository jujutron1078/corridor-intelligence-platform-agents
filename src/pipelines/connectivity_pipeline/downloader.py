"""
Ookla Speedtest Open Data downloader.

Source: s3://ookla-open-data/ (public Parquet tiles)
Resolution: ~610m (H3 resolution 8), quarterly releases.
Requires pyarrow for Parquet reading.
"""

from __future__ import annotations

import logging
from pathlib import Path

import requests

from src.shared.pipeline.utils import DATA_DIR, ensure_dir

logger = logging.getLogger("corridor.connectivity")

CONNECTIVITY_DATA_DIR = DATA_DIR / "connectivity"

# Ookla provides data as quarterly Parquet shapefiles on GitHub/S3
# Using the GitHub-hosted Parquet files for easier access
OOKLA_BASE_URL = "https://ookla-open-data.s3.amazonaws.com/parquet/performance"

# Most recent quarter available (update periodically)
LATEST_QUARTER = "2024-01-01"

NETWORK_TYPES = {
    "fixed": "type=fixed",
    "mobile": "type=mobile",
}


def download_ookla_tiles(
    network_type: str = "mobile",
    quarter: str = LATEST_QUARTER,
) -> Path | None:
    """
    Download Ookla Speedtest tile data for the corridor region.

    Note: The full global Parquet files are very large (~2GB each).
    This function downloads if available, or creates a placeholder
    for manual download.
    """
    ensure_dir(CONNECTIVITY_DATA_DIR)
    path = CONNECTIVITY_DATA_DIR / f"speedtest_{network_type}.parquet"

    if path.exists():
        logger.info("Ookla %s data already exists: %s", network_type, path)
        return path

    # The actual S3 paths follow: performance/type=mobile/year=2024/quarter=1/*.parquet
    year = quarter[:4]
    q = {"01": "1", "04": "2", "07": "3", "10": "4"}.get(quarter[5:7], "1")

    url = f"{OOKLA_BASE_URL}/type={network_type}/year={year}/quarter={q}/2024-01-01_performance_{network_type}_tiles.parquet"

    logger.info("Attempting to download Ookla %s data from: %s", network_type, url)
    try:
        resp = requests.get(url, timeout=300, stream=True)
        resp.raise_for_status()
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info("Downloaded Ookla %s: %s (%.1f MB)", network_type, path, path.stat().st_size / 1e6)
        return path
    except Exception as exc:
        logger.warning(
            "Could not download Ookla data: %s. "
            "Manual download may be required from https://github.com/teamookla/ookla-open-data",
            exc,
        )
        # Create a marker file so we know the data is missing
        marker = CONNECTIVITY_DATA_DIR / f".{network_type}_not_downloaded"
        marker.touch()
        return None
