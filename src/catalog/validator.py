"""
Data source validator — checks all pipeline data sources and produces a unified report.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.catalog.catalog import (
    DataSource, SourceType, ValidationStatus,
    get_catalog,
)
from src.shared.pipeline.utils import DATA_DIR

logger = logging.getLogger("corridor.catalog.validator")


def validate_gee_sources() -> dict[str, dict]:
    """Validate all GEE data sources."""
    results = {}
    try:
        from src.pipelines.gee_pipeline.accessor import CorridorDataAPI
        from src.pipelines.gee_pipeline.config import DATASET_CATALOG
        from src.shared.pipeline.utils import load_env, get_env

        load_env()
        project = get_env("GEE_PROJECT")
        api = CorridorDataAPI(project=project)

        for name, info in DATASET_CATALOG.items():
            result = api.validate_dataset(name, info["collection"])
            results[info["collection"]] = {
                "name": name,
                "status": "validated" if result["accessible"] else "missing",
                "count": result["count"],
                "error": result["error"],
            }
    except Exception as exc:
        logger.error("GEE validation failed: %s", exc)
        results["_error"] = {"name": "GEE", "status": "missing", "error": str(exc)}

    return results


def validate_osm_sources() -> dict[str, dict]:
    """Validate OSM data files."""
    from src.pipelines.osm_pipeline.config import OSM_OUTPUT_FILES

    results = {}
    for name, path in OSM_OUTPUT_FILES.items():
        if name == "network":
            continue
        if path.exists():
            try:
                from src.shared.pipeline.utils import load_geojson
                data = load_geojson(path)
                count = len(data.get("features", []))
                results[name] = {
                    "status": "validated" if count > 0 else "partial",
                    "count": count,
                }
            except Exception as exc:
                results[name] = {"status": "missing", "error": str(exc)}
        else:
            results[name] = {"status": "missing", "error": "File not found"}

    return results


def validate_mineral_sources() -> dict[str, dict]:
    """Validate USGS mineral data."""
    mineral_dir = DATA_DIR / "mineral" / "geojson"
    if not mineral_dir.exists():
        return {"usgs_minerals": {"status": "missing", "error": "No processed data"}}

    results = {}
    for f in mineral_dir.glob("*.geojson"):
        try:
            from src.shared.pipeline.utils import load_geojson
            data = load_geojson(f)
            count = len(data.get("features", []))
            results[f.stem] = {"status": "validated" if count > 0 else "partial", "count": count}
        except Exception as exc:
            results[f.stem] = {"status": "missing", "error": str(exc)}

    return results


def validate_trade_sources() -> dict[str, dict]:
    """Validate trade/commodity data."""
    trade_dir = DATA_DIR / "trade"
    results = {}

    # Check for CSV files
    for name in ["commodity_prices", "value_chain_analysis"]:
        csv_path = trade_dir / f"{name}.csv"
        json_path = trade_dir / f"{name}.json"
        path = csv_path if csv_path.exists() else json_path

        if path.exists():
            results[name] = {"status": "validated", "path": str(path)}
        else:
            results[name] = {"status": "missing", "error": "File not found"}

    # Check trade flow files
    for f in trade_dir.glob("trade_flows_*.csv"):
        results[f.stem] = {"status": "validated", "path": str(f)}

    if not results:
        results["trade_data"] = {"status": "missing", "error": "No trade data files found"}

    return results


def run_full_validation(include_gee: bool = True) -> dict[str, Any]:
    """
    Run validation for all data sources.

    Args:
        include_gee: Whether to validate GEE sources (requires GEE auth).

    Returns: Comprehensive validation report.
    """
    report = {
        "gee": {},
        "osm": {},
        "mineral": {},
        "trade": {},
        "summary": {},
    }

    if include_gee:
        logger.info("Validating GEE sources...")
        report["gee"] = validate_gee_sources()

    logger.info("Validating OSM sources...")
    report["osm"] = validate_osm_sources()

    logger.info("Validating mineral sources...")
    report["mineral"] = validate_mineral_sources()

    logger.info("Validating trade sources...")
    report["trade"] = validate_trade_sources()

    # Summary
    total = 0
    validated = 0
    partial = 0
    missing = 0

    for section in ["gee", "osm", "mineral", "trade"]:
        for name, info in report[section].items():
            total += 1
            status = info.get("status", "missing")
            if status == "validated":
                validated += 1
            elif status == "partial":
                partial += 1
            else:
                missing += 1

    report["summary"] = {
        "total": total,
        "validated": validated,
        "partial": partial,
        "missing": missing,
    }

    # Update catalog entries with validation results
    catalog = get_catalog()
    for ds in catalog:
        if ds.source_type == SourceType.GEE and ds.collection_id in report["gee"]:
            result = report["gee"][ds.collection_id]
            ds.status = ValidationStatus(result["status"])
        elif ds.source_type == SourceType.OSM:
            osm_results = report["osm"]
            if any(r.get("status") == "validated" for r in osm_results.values()):
                ds.status = ValidationStatus.VALIDATED
            elif osm_results:
                ds.status = ValidationStatus.PARTIAL
        elif ds.source_type == SourceType.USGS:
            mineral_results = report["mineral"]
            if any(r.get("status") == "validated" for r in mineral_results.values()):
                ds.status = ValidationStatus.VALIDATED
        elif ds.source_type == SourceType.API:
            trade_results = report["trade"]
            if any(r.get("status") == "validated" for r in trade_results.values()):
                ds.status = ValidationStatus.VALIDATED

    return report
