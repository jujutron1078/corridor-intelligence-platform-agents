import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import AnchorLoadScannerInput

logger = logging.getLogger("corridor.agent.opportunity.scan_anchor_loads")

# Sector classification for OSM/USGS infrastructure detection types
SECTOR_MAP = {
    "port_facility": ("Industrial", "Port & Logistics"),
    "airport": ("Industrial", "Airport & Aviation"),
    "rail_network": ("Industrial", "Rail Infrastructure"),
    "industrial_zone": ("Industrial", "Industrial Zone"),
    "border_crossing": ("Industrial", "Border Crossing & Trade"),
    "mineral_site": ("Mining", "Mineral Extraction"),
    "power_plant": ("Energy", "Power Generation"),
}

# Detection types that represent generation assets (not demand-side anchor loads)
GENERATION_TYPES = {"power_plant"}


def _classify_detection(det: dict, idx: int) -> dict:
    """Classify a raw detection into an anchor catalog entry."""
    det_type = det.get("type", "other")
    props = det.get("properties", {})
    sector, sub_sector = SECTOR_MAP.get(det_type, ("Other", det_type.replace("_", " ").title()))

    is_generation = det_type in GENERATION_TYPES

    # Try to extract country from properties
    country = (
        props.get("country", "")
        or props.get("addr:country", "")
        or props.get("country_code", "")
    )

    # For mineral sites, enrich sub_sector with commodity info
    if det_type == "mineral_site":
        commodity = props.get("commodity", props.get("commod1", ""))
        status = props.get("dev_stat", props.get("status", ""))
        if commodity:
            sub_sector = f"Mineral Extraction — {commodity}"
        if status:
            sub_sector += f" ({status})"

    # For power plants, enrich with fuel type and capacity
    if det_type == "power_plant":
        fuel = props.get("fuel_type", props.get("fuel", ""))
        capacity = props.get("capacity_mw", 0)
        if fuel:
            sub_sector = f"Power Generation — {fuel.title()}"
        if capacity:
            sub_sector += f" ({capacity} MW)"

    return {
        "anchor_id": f"AL_ANC_{idx + 1:03d}",
        "detection_id": det.get("detection_id", f"DET-{idx + 1:03d}"),
        "entity_name": det.get("name", "Unknown"),
        "sector": sector,
        "sub_sector": sub_sector,
        "country": country,
        "coordinates": det.get("coordinates", []),
        "source": det.get("source", ""),
        "confidence": det.get("confidence", 0.0),
        "is_anchor_load": not is_generation,
        "is_generation_asset": is_generation,
        "properties": props,
    }


@tool("scan_anchor_loads", description=TOOL_DESCRIPTION)
def scan_anchor_loads_tool(
    payload: AnchorLoadScannerInput, runtime: ToolRuntime
) -> Command:
    """
    Resolves commercial identities for infrastructure detections within the
    corridor boundary using real OSM, USGS, and energy pipeline data.
    """
    from src.adapters.pipeline_bridge import pipeline_bridge

    try:
        infra = pipeline_bridge.get_infrastructure_detections()
    except Exception as exc:
        logger.error("Infrastructure detection failed: %s", exc)
        return Command(update={"messages": [ToolMessage(
            content=json.dumps({
                "error": str(exc),
                "anchor_catalog": [],
                "message": "Infrastructure data unavailable. Check OSM/mineral service initialization.",
            }),
            tool_call_id=runtime.tool_call_id,
        )]})

    # Get power plants from energy pipeline
    energy_plants: list[dict] = []
    try:
        energy = pipeline_bridge.get_energy_data()
        for i, feat in enumerate(energy.get("power_plants", {}).get("features", [])):
            coords = feat.get("geometry", {}).get("coordinates", [])
            props = feat.get("properties", {})
            energy_plants.append({
                "detection_id": f"DET-PWR-{i + 1:03d}",
                "type": "power_plant",
                "name": props.get("name", "Unknown Power Plant"),
                "coordinates": coords,
                "confidence": 0.95,
                "source": "Global Power Plant Database",
                "properties": props,
            })
    except Exception as exc:
        logger.warning("Energy data unavailable for enrichment: %s", exc)

    # Enrich with planned energy generation projects
    planned_generation = []
    try:
        planned = pipeline_bridge.get_planned_energy_projects()
        for proj in planned.get("projects", []):
            planned_generation.append({
                "name": proj.get("name", "Planned Generation"),
                "capacity_mw": proj.get("capacity_mw", 0),
                "fuel_type": proj.get("fuel_type", "unknown"),
                "country": proj.get("country", ""),
                "status": proj.get("status", "planned"),
            })
        logger.info("Planned energy projects obtained: %d", len(planned_generation))
    except Exception as exc:
        logger.warning("Planned energy projects unavailable: %s", exc)

    # Enrich with agricultural production zones as potential anchors
    agricultural_zones = []
    try:
        agri = pipeline_bridge.get_agricultural_production()
        production = agri.get("production", {})
        for zone_name, zone_data in production.items():
            if isinstance(zone_data, dict):
                agricultural_zones.append({
                    "zone": zone_name,
                    "output": zone_data.get("output", ""),
                    "crop": zone_data.get("crop", zone_name),
                    "country": zone_data.get("country", ""),
                })
        logger.info("Agricultural zones identified: %d", len(agricultural_zones))
    except Exception as exc:
        logger.warning("Agricultural production data unavailable: %s", exc)

    # Enrich port data with real throughput statistics
    port_enrichment = {}
    try:
        ports_data = pipeline_bridge.get_port_statistics()
        for port in ports_data.get("ports", []):
            port_name = port.get("name", "")
            if port_name:
                port_enrichment[port_name.lower()] = {
                    "teu_throughput": port.get("teu_throughput", 0),
                    "cargo_tons": port.get("cargo_tons", 0),
                    "country": port.get("country", ""),
                }
        logger.info("Port statistics obtained: %d ports", len(port_enrichment))
    except Exception as exc:
        logger.warning("Port statistics unavailable: %s", exc)

    # Combine all detections
    all_detections = infra.get("detections", []) + energy_plants

    # Classify each detection
    anchor_catalog = []
    generation_assets = []
    for i, det in enumerate(all_detections):
        entry = _classify_detection(det, i)
        if entry["is_anchor_load"]:
            anchor_catalog.append(entry)
        else:
            generation_assets.append(entry)

    # Summaries
    by_sector: dict[str, int] = {}
    by_country: dict[str, int] = {}
    for a in anchor_catalog:
        by_sector[a.get("sector", "Unknown")] = by_sector.get(a.get("sector", "Unknown"), 0) + 1
        c = a.get("country") or "Unknown"
        by_country[c] = by_country.get(c, 0) + 1

    # Apply port enrichment to port anchors
    for anchor in anchor_catalog:
        if anchor.get("sector") == "Industrial" and "port" in anchor.get("sub_sector", "").lower():
            name_lower = anchor.get("entity_name", "").lower()
            for port_key, port_info in port_enrichment.items():
                if port_key in name_lower or name_lower in port_key:
                    anchor["port_throughput"] = port_info
                    break

    response = {
        "status": "Scanning Complete",
        "total_detections_received": len(all_detections),
        "total_anchors_resolved": len(anchor_catalog),
        "generation_assets_found": len(generation_assets),
        "anchor_catalog": anchor_catalog,
        "generation_assets": generation_assets,
        "planned_generation": planned_generation if planned_generation else [],
        "agricultural_zones": agricultural_zones if agricultural_zones else [],
        "port_enrichment": port_enrichment if port_enrichment else {},
        "resolution_summary": {
            "total_detections_received": len(all_detections),
            "anchor_loads": len(anchor_catalog),
            "generation_assets": len(generation_assets),
            "planned_generation_projects": len(planned_generation),
            "agricultural_processing_zones": len(agricultural_zones),
            "ports_with_throughput_data": len(port_enrichment),
            "by_sector": by_sector,
            "by_country": by_country,
        },
        "data_sources": [
            "OpenStreetMap", "USGS Minerals", "Global Power Plant Database",
        ] + (["Planned Energy Projects"] if planned_generation else [])
          + (["Agricultural Production Data"] if agricultural_zones else [])
          + (["Port Statistics"] if port_enrichment else []),
        "message": (
            f"{len(all_detections)} detections processed. "
            f"{len(anchor_catalog)} anchor loads and {len(generation_assets)} generation assets "
            f"identified across {len(by_sector)} sectors and {len(by_country)} countries."
            + (f" {len(planned_generation)} planned generation projects identified." if planned_generation else "")
            + (f" {len(agricultural_zones)} agricultural processing zones identified." if agricultural_zones else "")
            + (f" {len(port_enrichment)} ports enriched with throughput data." if port_enrichment else "")
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
