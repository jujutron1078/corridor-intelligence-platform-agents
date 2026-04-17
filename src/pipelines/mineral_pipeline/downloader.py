"""
USGS Africa mineral geodatabase downloader.

Source: USGS Compilation of Geospatial Data (GIS) for the Mineral Industries
        and Related Infrastructure of Africa
DOI: https://doi.org/10.5066/P97EQWXP
ScienceBase: https://www.sciencebase.gov/catalog/item/607611a9d34e018b3201cbbf
"""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path

import requests

from src.shared.pipeline.utils import DATA_DIR, ensure_dir, retry

logger = logging.getLogger("corridor.mineral.downloader")

MINERAL_DATA_DIR = DATA_DIR / "mineral"
GDB_DIR = MINERAL_DATA_DIR / "geodatabase"

# ScienceBase item ID for the USGS Africa mineral data
SCIENCEBASE_ITEM_ID = "607611a9d34e018b3201cbbf"
SCIENCEBASE_API = "https://www.sciencebase.gov/catalog/item"


def get_download_urls() -> list[dict]:
    """
    Query ScienceBase API for the download URLs of the geodatabase files.

    Returns a list of {"name": str, "url": str, "size": int} dicts.
    """
    url = f"{SCIENCEBASE_API}/{SCIENCEBASE_ITEM_ID}?format=json"
    logger.info("Querying ScienceBase for download links...")

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    item = resp.json()

    files = []
    for f in item.get("files", []):
        files.append({
            "name": f.get("name", ""),
            "url": f.get("url", ""),
            "size": f.get("size", 0),
            "content_type": f.get("contentType", ""),
        })

    # Also check for facets / extensions
    for ext in item.get("facets", []):
        for f in ext.get("files", []):
            files.append({
                "name": f.get("name", ""),
                "url": f.get("url", ""),
                "size": f.get("size", 0),
                "content_type": f.get("contentType", ""),
            })

    logger.info("Found %d downloadable files", len(files))
    return files


def download_file(url: str, dest: Path, chunk_size: int = 8192) -> Path:
    """Download a file with progress tracking."""
    ensure_dir(dest.parent)

    if dest.exists():
        logger.info("File already exists, skipping: %s", dest.name)
        return dest

    logger.info("Downloading %s...", dest.name)

    def _do_download():
        resp = requests.get(url, stream=True, timeout=300)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0

        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0 and downloaded % (chunk_size * 100) == 0:
                    pct = (downloaded / total) * 100
                    logger.debug("  %.1f%% (%d / %d bytes)", pct, downloaded, total)

        logger.info("Downloaded: %s (%d bytes)", dest.name, downloaded)
        return dest

    return retry(_do_download, max_retries=3, backoff=5.0, exceptions=(requests.RequestException,))


def extract_gdb(zip_path: Path, extract_to: Path | None = None) -> Path:
    """
    Extract a geodatabase from a zip archive.

    Returns the path to the .gdb directory.
    """
    extract_to = extract_to or zip_path.parent
    ensure_dir(extract_to)

    logger.info("Extracting %s...", zip_path.name)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)

    # Find the .gdb directory
    for item in extract_to.rglob("*.gdb"):
        if item.is_dir():
            logger.info("Found geodatabase: %s", item)
            return item

    # If no .gdb found, return extract directory
    logger.warning("No .gdb directory found in %s", zip_path.name)
    return extract_to


def download_geodatabase() -> Path | None:
    """
    Download the USGS Africa mineral geodatabase.

    Returns the path to the extracted .gdb, or None on failure.
    """
    ensure_dir(MINERAL_DATA_DIR)

    try:
        files = get_download_urls()
    except Exception as exc:
        logger.error("Failed to query ScienceBase: %s", exc)
        return None

    # Look for File GDB or Shapefile downloads
    gdb_files = [f for f in files if f["name"].endswith((".gdb.zip", ".zip")) and "gdb" in f["name"].lower()]
    shp_files = [f for f in files if f["name"].endswith(".zip") and "shp" in f["name"].lower()]

    target_files = gdb_files or shp_files or [f for f in files if f["name"].endswith(".zip")]

    if not target_files:
        logger.error("No downloadable geodatabase files found")
        return None

    for tf in target_files:
        dest = MINERAL_DATA_DIR / tf["name"]
        try:
            downloaded = download_file(tf["url"], dest)
            if downloaded.suffix == ".zip":
                return extract_gdb(downloaded, GDB_DIR)
            return downloaded
        except Exception as exc:
            logger.error("Failed to download %s: %s", tf["name"], exc)
            continue

    return None
