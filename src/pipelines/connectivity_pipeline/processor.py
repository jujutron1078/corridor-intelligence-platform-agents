"""
Ookla Speedtest data processor - filter Parquet tiles to corridor AOI, extract stats.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.shared.pipeline.aoi import BBOX_SOUTH, BBOX_WEST, BBOX_NORTH, BBOX_EAST
from src.shared.pipeline.utils import DATA_DIR, ensure_dir

logger = logging.getLogger("corridor.connectivity")

CONNECTIVITY_DATA_DIR = DATA_DIR / "connectivity"


def process_speedtest_parquet(
    parquet_path: Path,
    network_type: str = "mobile",
) -> dict:
    """
    Process Ookla Speedtest Parquet file into GeoJSON.

    Filters to corridor bbox and extracts speed/latency stats.
    """
    try:
        import pyarrow.parquet as pq
        import pandas as pd
    except ImportError:
        logger.warning("pyarrow not installed - cannot process Ookla data. Install with: pip install pyarrow")
        return {"type": "FeatureCollection", "features": []}

    if not parquet_path.exists():
        logger.warning("Parquet file not found: %s", parquet_path)
        return {"type": "FeatureCollection", "features": []}

    logger.info("Processing Ookla %s data from %s...", network_type, parquet_path)

    # Read Parquet with corridor bbox filter
    table = pq.read_table(parquet_path)
    df = table.to_pandas()

    # Ookla tiles have 'tile' (H3 hex string), 'avg_d_kbps', 'avg_u_kbps', 'avg_lat_ms', 'tests', 'devices'
    # And geometry in 'tile_x', 'tile_y' or lat/lon columns depending on version

    # Filter to corridor bbox
    if "tile_y" in df.columns and "tile_x" in df.columns:
        df = df[
            (df["tile_y"] >= BBOX_SOUTH) & (df["tile_y"] <= BBOX_NORTH) &
            (df["tile_x"] >= BBOX_WEST) & (df["tile_x"] <= BBOX_EAST)
        ]
    elif "quadkey" in df.columns:
        # Quadkey-based - need to decode to lat/lon first
        # For now, just take all rows and let the user filter
        pass

    features = []
    for _, row in df.iterrows():
        try:
            # Try different column naming conventions
            lon = float(row.get("tile_x", row.get("longitude", 0)))
            lat = float(row.get("tile_y", row.get("latitude", 0)))

            if lon == 0 and lat == 0:
                continue

            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "avg_download_mbps": round(float(row.get("avg_d_kbps", 0)) / 1000, 2),
                    "avg_upload_mbps": round(float(row.get("avg_u_kbps", 0)) / 1000, 2),
                    "avg_latency_ms": float(row.get("avg_lat_ms", 0)),
                    "tests": int(row.get("tests", 0)),
                    "devices": int(row.get("devices", 0)),
                    "network_type": network_type,
                },
            })
        except (ValueError, TypeError):
            continue

    logger.info("Processed %d Ookla tiles for corridor", len(features))
    return {"type": "FeatureCollection", "features": features}


def get_connectivity_summary(geojson: dict) -> dict[str, Any]:
    """Compute summary statistics from speedtest GeoJSON."""
    features = geojson.get("features", [])
    if not features:
        return {"total_tiles": 0}

    downloads = [f["properties"]["avg_download_mbps"] for f in features if f["properties"].get("avg_download_mbps")]
    uploads = [f["properties"]["avg_upload_mbps"] for f in features if f["properties"].get("avg_upload_mbps")]
    latencies = [f["properties"]["avg_latency_ms"] for f in features if f["properties"].get("avg_latency_ms")]

    return {
        "total_tiles": len(features),
        "avg_download_mbps": round(sum(downloads) / len(downloads), 2) if downloads else 0,
        "avg_upload_mbps": round(sum(uploads) / len(uploads), 2) if uploads else 0,
        "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
        "max_download_mbps": round(max(downloads), 2) if downloads else 0,
    }


def save_connectivity(geojson: dict, network_type: str) -> Path:
    """Save connectivity GeoJSON."""
    ensure_dir(CONNECTIVITY_DATA_DIR)
    path = CONNECTIVITY_DATA_DIR / f"speedtest_{network_type}.geojson"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)
    logger.info("Saved connectivity data: %s (%d features)", path, len(geojson["features"]))
    return path


def load_connectivity(network_type: str = "mobile") -> dict:
    """Load cached connectivity GeoJSON."""
    path = CONNECTIVITY_DATA_DIR / f"speedtest_{network_type}.geojson"
    if not path.exists():
        return {"type": "FeatureCollection", "features": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
