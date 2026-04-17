"""
FAO GLW 3 data processor - clip GeoTIFFs to corridor AOI and extract zonal stats.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.shared.pipeline.aoi import BBOX_SOUTH, BBOX_WEST, BBOX_NORTH, BBOX_EAST
from src.shared.pipeline.utils import DATA_DIR, ensure_dir

logger = logging.getLogger("corridor.livestock")

LIVESTOCK_DATA_DIR = DATA_DIR / "livestock"

# Country approximate bounding boxes for zonal stats
COUNTRY_BBOXES = {
    "NGA": {"name": "Nigeria", "west": 2.7, "south": 4.2, "east": 4.0, "north": 7.0},
    "BEN": {"name": "Benin", "west": 1.6, "south": 6.2, "east": 2.7, "north": 7.0},
    "TGO": {"name": "Togo", "west": 0.9, "south": 6.0, "east": 1.6, "north": 6.5},
    "GHA": {"name": "Ghana", "west": -1.2, "south": 4.7, "east": 0.9, "north": 6.8},
    "CIV": {"name": "Côte d'Ivoire", "west": -4.5, "south": 4.5, "east": -1.2, "north": 6.0},
}


def extract_corridor_stats() -> dict[str, Any]:
    """
    Extract livestock density statistics for the corridor.

    If rasterio is available, reads actual GeoTIFF data.
    Otherwise, returns placeholder structure for when data is downloaded later.
    """
    results: dict[str, Any] = {}

    species_files = list(LIVESTOCK_DATA_DIR.glob("*.tif"))
    if not species_files:
        logger.warning("No livestock GeoTIFF files found in %s", LIVESTOCK_DATA_DIR)
        return results

    try:
        import rasterio
        from rasterio.windows import from_bounds
        import numpy as np
    except ImportError:
        logger.warning("rasterio not installed - cannot process livestock GeoTIFFs. Install with: pip install rasterio")
        return results

    for tif_path in species_files:
        species = tif_path.stem
        logger.info("Processing %s...", species)

        try:
            with rasterio.open(tif_path) as src:
                # Read corridor window
                window = from_bounds(
                    BBOX_WEST, BBOX_SOUTH, BBOX_EAST, BBOX_NORTH,
                    transform=src.transform,
                )
                data = src.read(1, window=window)
                nodata = src.nodata

                if nodata is not None:
                    valid = data[data != nodata]
                else:
                    valid = data[data > 0]

                if len(valid) > 0:
                    results[species] = {
                        "total_heads": float(np.sum(valid)),
                        "mean_density": float(np.mean(valid)),
                        "max_density": float(np.max(valid)),
                        "pixel_count": int(len(valid)),
                    }
                else:
                    results[species] = {"total_heads": 0, "mean_density": 0, "max_density": 0, "pixel_count": 0}

        except Exception as exc:
            logger.error("Failed to process %s: %s", species, exc)
            results[species] = {"error": str(exc)}

    return results


def save_stats(stats: dict[str, Any]) -> Path:
    """Save livestock stats as JSON."""
    ensure_dir(LIVESTOCK_DATA_DIR)
    path = LIVESTOCK_DATA_DIR / "livestock_stats.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    logger.info("Saved livestock stats: %s", path)
    return path


def load_stats() -> dict[str, Any]:
    """Load cached livestock stats."""
    path = LIVESTOCK_DATA_DIR / "livestock_stats.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
