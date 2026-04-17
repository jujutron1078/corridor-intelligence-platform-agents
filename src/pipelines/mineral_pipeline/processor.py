"""
USGS mineral geodatabase processor.

Parses File GDB with Fiona/GDAL, filters to corridor AOI,
classifies by commodity and status, exports to GeoJSON.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import fiona
import geopandas as gpd
from shapely.geometry import box, mapping, shape

from src.shared.pipeline.aoi import CORRIDOR, BBOX_WEST, BBOX_SOUTH, BBOX_EAST, BBOX_NORTH
from src.shared.pipeline.utils import DATA_DIR, ensure_dir, save_geojson

logger = logging.getLogger("corridor.mineral.processor")

MINERAL_DATA_DIR = DATA_DIR / "mineral"
MINERAL_OUTPUT_DIR = DATA_DIR / "mineral" / "geojson"

# Corridor bounding box with buffer for filtering
AOI_BUFFER_DEG = 0.5
FILTER_BBOX = (
    BBOX_WEST - AOI_BUFFER_DEG,
    BBOX_SOUTH - AOI_BUFFER_DEG,
    BBOX_EAST + AOI_BUFFER_DEG,
    BBOX_NORTH + AOI_BUFFER_DEG,
)

# ── Commodity classification ─────────────────────────────────────────────────

COMMODITY_MAP = {
    "gold": ["gold"],
    "bauxite": ["bauxite", "alumina", "aluminum"],
    "iron_ore": ["iron", "fe"],
    "limestone": ["limestone", "cement", "calcium"],
    "oil_gas": ["oil", "gas", "petroleum", "crude", "lng", "natural gas"],
    "diamond": ["diamond"],
    "manganese": ["manganese", "mn"],
    "phosphate": ["phosphate", "phosphorus"],
    "tin": ["tin", "cassiterite"],
    "coal": ["coal"],
    "uranium": ["uranium"],
    "copper": ["copper", "cu"],
    "zinc": ["zinc", "zn"],
    "lead": ["lead", "pb"],
    "titanium": ["titanium", "rutile", "ilmenite"],
    "other": [],
}


def classify_commodity(text: str | None) -> str:
    """Classify a commodity string into a category."""
    import re
    if not text:
        return "other"
    text_lower = text.lower()
    for category, keywords in COMMODITY_MAP.items():
        if category == "other":
            continue
        for kw in keywords:
            # Use word boundary for short keywords to prevent substring matches
            if len(kw) <= 3:
                if re.search(rf'\b{re.escape(kw)}\b', text_lower):
                    return category
            elif kw in text_lower:
                return category
    return "other"


# ── Status classification ────────────────────────────────────────────────────

STATUS_KEYWORDS = {
    "active": ["active", "operating", "producing", "production", "open"],
    "developing": ["developing", "construction", "development", "feasibility", "planned"],
    "exploration": ["exploration", "prospect", "occurrence", "deposit", "drill"],
    "closed": ["closed", "abandoned", "inactive", "past producer"],
}


def classify_status(text: str | None) -> str:
    """Classify a facility status string."""
    if not text:
        return "unknown"
    text_lower = text.lower()
    for status, keywords in STATUS_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return status
    return "unknown"


def list_gdb_layers(gdb_path: Path) -> list[str]:
    """List all layers in a File GDB."""
    try:
        return fiona.listlayers(str(gdb_path))
    except Exception as exc:
        logger.error("Failed to list GDB layers: %s", exc)
        return []


def read_and_filter_layer(
    gdb_path: Path,
    layer_name: str,
) -> gpd.GeoDataFrame | None:
    """
    Read a GDB layer and filter to the corridor bounding box.

    Returns a GeoDataFrame or None if the layer can't be read.
    """
    try:
        gdf = gpd.read_file(str(gdb_path), layer=layer_name, bbox=FILTER_BBOX)
        if gdf.empty:
            logger.info("Layer '%s': empty after AOI filter", layer_name)
            return None
        logger.info("Layer '%s': %d features within corridor", layer_name, len(gdf))
        return gdf
    except Exception as exc:
        logger.warning("Failed to read layer '%s': %s", layer_name, exc)
        return None


def _find_commodity_col(gdf: gpd.GeoDataFrame) -> str | None:
    """Find the best commodity column in the GeoDataFrame."""
    # USGS Africa GDB uses DsgAttr01/DsgAttr02 for commodity, FeatureTyp for type
    # Generic datasets may use "commodity", "mineral", etc.
    candidates = (
        ["DsgAttr01", "DsgAttr02", "FeatureTyp"]
        + [c for c in gdf.columns if any(kw in c.lower() for kw in ["commod", "mineral", "resource", "product"])]
    )
    for col in candidates:
        if col in gdf.columns:
            return col
    return None


def _find_status_col(gdf: gpd.GeoDataFrame) -> str | None:
    """Find the best status column in the GeoDataFrame."""
    candidates = (
        ["LocOpStat"]
        + [c for c in gdf.columns if any(kw in c.lower() for kw in ["status", "activity", "state"])]
    )
    for col in candidates:
        if col in gdf.columns:
            return col
    return None


def process_mineral_facilities(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Add commodity_type and status classifications to mineral facility data."""
    commodity_col = _find_commodity_col(gdf)
    status_col = _find_status_col(gdf)

    if commodity_col:
        # Combine DsgAttr01 + DsgAttr02 if both exist (e.g., "Fuel" + "Petroleum")
        if commodity_col == "DsgAttr01" and "DsgAttr02" in gdf.columns:
            combined = gdf["DsgAttr01"].astype(str).fillna("") + " " + gdf["DsgAttr02"].astype(str).fillna("")
            gdf["commodity_type"] = combined.apply(classify_commodity)
        else:
            gdf["commodity_type"] = gdf[commodity_col].astype(str).apply(classify_commodity)
    else:
        gdf["commodity_type"] = "other"

    gdf["facility_status"] = gdf[status_col].apply(classify_status) if status_col else "unknown"

    # Carry forward human-readable name
    if "FeatureNam" in gdf.columns:
        gdf["site_name"] = gdf["FeatureNam"]
    if "Country" in gdf.columns:
        gdf["country"] = gdf["Country"]

    return gdf


def gdf_to_geojson(gdf: gpd.GeoDataFrame) -> dict:
    """Convert a GeoDataFrame to a GeoJSON dict, handling serialization."""
    # Ensure WGS84
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    geojson_str = gdf.to_json()
    import json
    return json.loads(geojson_str)


def process_geodatabase(gdb_path: Path) -> dict[str, dict]:
    """
    Process all layers in the geodatabase.

    Returns: {"layer_name": GeoJSON_dict, ...}
    """
    layers = list_gdb_layers(gdb_path)
    logger.info("Found %d layers in geodatabase", len(layers))

    results = {}
    for layer_name in layers:
        gdf = read_and_filter_layer(gdb_path, layer_name)
        if gdf is None or gdf.empty:
            continue

        # Classify mineral/resource layers (USGS uses DsgAttr01 for commodity across many layer types)
        if any(kw in layer_name.lower() for kw in ["mineral", "mine", "facility", "production", "occurrence", "deposit", "exploration", "resource", "og_"]):
            gdf = process_mineral_facilities(gdf)

        # Convert to GeoJSON
        geojson = gdf_to_geojson(gdf)
        clean_name = layer_name.replace(" ", "_").lower()
        results[clean_name] = geojson

    return results


def create_economic_anchors(
    mineral_geojson: dict | None = None,
    ports_geojson: dict | None = None,
    industrial_geojson: dict | None = None,
    power_geojson: dict | None = None,
) -> dict:
    """
    Create a unified "economic anchors" GeoJSON combining:
    mineral sites + ports + industrial zones + power plants.
    """
    features = []

    def _add_features(geojson: dict | None, anchor_type: str):
        if not geojson:
            return
        for f in geojson.get("features", []):
            f = dict(f)
            f["properties"] = dict(f.get("properties", {}))
            f["properties"]["anchor_type"] = anchor_type
            features.append(f)

    _add_features(mineral_geojson, "mineral")
    _add_features(ports_geojson, "port")
    _add_features(industrial_geojson, "industrial")
    _add_features(power_geojson, "power")

    logger.info("Created economic anchors layer: %d features", len(features))
    return {"type": "FeatureCollection", "features": features}


def export_all(results: dict[str, dict]) -> None:
    """Save all processed layers as GeoJSON files."""
    ensure_dir(MINERAL_OUTPUT_DIR)
    for name, geojson in results.items():
        path = MINERAL_OUTPUT_DIR / f"{name}.geojson"
        save_geojson(geojson, path)
