import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import GapAnalysisInput

logger = logging.getLogger("corridor.agent.opportunity.gap_analysis")

# Gap classification thresholds
SUPPRESSED_DEMAND_THRESHOLD_MW = 10.0  # Facilities with >10 MW likely suppressed
TRANSMISSION_GAP_DISTANCE_KM = 50.0    # No HV line within 50 km


def _classify_gap(det: dict, has_nearby_generation: bool) -> dict | None:
    """Classify whether a detection represents an infrastructure gap."""
    det_type = det.get("type", "other")
    props = det.get("properties", {})

    # Skip generation assets — they are supply, not gaps
    if det_type == "power_plant":
        return None

    # Demand-side facility types
    demand_types = {"port_facility", "airport", "industrial_zone", "mineral_site"}
    if det_type not in demand_types:
        return None

    # Estimate demand (simplified from calculate_current_demand)
    base_mw = {
        "port_facility": 20.0, "airport": 15.0,
        "industrial_zone": 30.0, "mineral_site": 25.0,
    }.get(det_type, 5.0)

    # Determine gap type
    if not has_nearby_generation and base_mw >= SUPPRESSED_DEMAND_THRESHOLD_MW:
        gap_type = "Transmission Gap"
        severity = "Critical" if base_mw >= 30.0 else "High"
    elif base_mw >= SUPPRESSED_DEMAND_THRESHOLD_MW:
        gap_type = "Suppressed Demand Gap"
        severity = "High" if base_mw >= 25.0 else "Medium"
    else:
        gap_type = "Catalytic Gap"
        severity = "Medium"

    country = props.get("country", props.get("addr:country", "Unknown"))

    return {
        "gap_type": gap_type,
        "severity": severity,
        "facility_name": det.get("name", "Unknown"),
        "facility_type": det_type,
        "country": country,
        "coordinates": det.get("coordinates", []),
        "estimated_unmet_mw": base_mw,
        "detection_id": det.get("detection_id", ""),
    }


@tool("economic_gap_analysis", description=TOOL_DESCRIPTION)
def economic_gap_analysis_tool(
    payload: GapAnalysisInput, runtime: ToolRuntime
) -> Command:
    """
    Identifies underserved geographic zones within the corridor where
    significant demand exists but current infrastructure fails to serve it.
    """
    from src.adapters.pipeline_bridge import pipeline_bridge

    try:
        infra = pipeline_bridge.get_infrastructure_detections()
    except Exception as exc:
        logger.error("Infrastructure data unavailable: %s", exc)
        return Command(update={"messages": [ToolMessage(
            content=json.dumps({
                "error": str(exc),
                "gaps": [],
                "message": "Cannot perform gap analysis — infrastructure data unavailable.",
            }),
            tool_call_id=runtime.tool_call_id,
        )]})

    # Get energy data to identify where generation exists
    generation_coords: list[tuple[float, float]] = []
    try:
        energy = pipeline_bridge.get_energy_data()
        for feat in energy.get("power_plants", {}).get("features", []):
            coords = feat.get("geometry", {}).get("coordinates", [])
            pt = _extract_lon_lat(coords)
            if pt:
                generation_coords.append(pt)
    except Exception as exc:
        logger.warning("Energy data unavailable for gap analysis: %s", exc)

    # Get World Bank indicators for economic context
    wb_context = None
    try:
        wb_data = pipeline_bridge.get_worldbank_indicators()
        wb_context = wb_data.get("indicators")
    except Exception as exc:
        logger.warning("World Bank data unavailable: %s", exc)

    # Get transmission grid data to check proximity to existing grid for gap severity
    existing_grid_context = {}
    grid_line_coords = []
    try:
        grid_data = pipeline_bridge.get_transmission_grid()
        grid_info = grid_data.get("grid", {})
        transmission_lines = grid_info.get("transmission_lines", [])
        substations = grid_info.get("substations", [])
        grid_summary = grid_data.get("summary", {})
        existing_grid_context = {
            "transmission_lines_count": len(transmission_lines),
            "substations_count": len(substations),
            "summary": grid_summary,
        }
        # Extract line coordinates for proximity checks
        for line in transmission_lines:
            coords = line.get("coordinates", line.get("geometry", {}).get("coordinates", []))
            if coords and isinstance(coords, list):
                # Handle MultiLineString: [[[lon,lat],...],...]
                if (isinstance(coords[0], list)
                        and len(coords[0]) > 0
                        and isinstance(coords[0][0], list)):
                    for segment in coords:
                        if segment:
                            mid = segment[len(segment) // 2]
                            pt = _extract_lon_lat(mid)
                            if pt:
                                grid_line_coords.append(pt)
                # LineString: [[lon,lat], ...]
                elif isinstance(coords[0], list):
                    mid = coords[len(coords) // 2]
                    pt = _extract_lon_lat(mid)
                    if pt:
                        grid_line_coords.append(pt)
                # Flat [lon, lat] or [lon, lat, alt]
                else:
                    pt = _extract_lon_lat(coords)
                    if pt:
                        grid_line_coords.append(pt)
        logger.info("Transmission grid data obtained: %d lines, %d substations",
                     len(transmission_lines), len(substations))
    except Exception as exc:
        logger.warning("Transmission grid data unavailable: %s", exc)

    detections = infra.get("detections", [])

    # Check proximity to existing transmission grid
    def _has_nearby_grid(det_coords: list) -> bool:
        if not grid_line_coords or not det_coords:
            return False
        pt = _extract_lon_lat(det_coords)
        if not pt:
            return False
        dx, dy = pt
        for gx, gy in grid_line_coords:
            dist_deg = ((dx - gx) ** 2 + (dy - gy) ** 2) ** 0.5
            if dist_deg < (TRANSMISSION_GAP_DISTANCE_KM / 111.0):
                return True
        return False

    def _extract_lon_lat(coords: list) -> tuple[float, float] | None:
        """Safely extract (lon, lat) from various coordinate formats."""
        if not coords:
            return None
        # Nested: [[lon, lat]] or [[[lon, lat]]]
        c = coords
        while isinstance(c, list) and len(c) > 0 and isinstance(c[0], list):
            c = c[0]
        if isinstance(c, list) and len(c) >= 2:
            try:
                return (float(c[0]), float(c[1]))
            except (TypeError, ValueError):
                return None
        return None

    # Simple proximity check for nearby generation
    def _has_nearby_gen(det_coords: list) -> bool:
        if not generation_coords or not det_coords:
            return False
        pt = _extract_lon_lat(det_coords)
        if not pt:
            return False
        dx, dy = pt
        for gx, gy in generation_coords:
            # Rough degree-distance check (~1 degree ≈ 111 km at equator)
            dist_deg = ((dx - gx) ** 2 + (dy - gy) ** 2) ** 0.5
            if dist_deg < (TRANSMISSION_GAP_DISTANCE_KM / 111.0):
                return True
        return False

    gaps = []
    total_unmet_mw = 0.0
    gap_type_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}

    for i, det in enumerate(detections):
        coords = det.get("coordinates", [])
        has_gen = _has_nearby_gen(coords)
        gap = _classify_gap(det, has_gen)
        if gap:
            gap["gap_id"] = f"GAP_{len(gaps) + 1:03d}"
            # Adjust severity based on grid proximity
            has_grid = _has_nearby_grid(coords)
            gap["near_existing_grid"] = has_grid
            if has_grid and gap["severity"] == "Critical":
                gap["severity"] = "High"
                gap["severity_note"] = "Downgraded from Critical: existing grid infrastructure nearby"
            elif not has_grid and gap["severity"] == "Medium":
                gap["severity"] = "High"
                gap["severity_note"] = "Upgraded from Medium: no existing grid infrastructure nearby"
            gaps.append(gap)
            total_unmet_mw += gap["estimated_unmet_mw"]
            gt = gap["gap_type"]
            gap_type_counts[gt] = gap_type_counts.get(gt, 0) + 1
            sv = gap["severity"]
            severity_counts[sv] = severity_counts.get(sv, 0) + 1

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "gaps_found": len(gaps),
        "total_unmet_demand_mw": round(total_unmet_mw, 1),
        "gap_type_summary": gap_type_counts,
        "severity_summary": severity_counts,
        "gaps": gaps,
        "generation_plants_in_corridor": len(generation_coords),
        "existing_grid_context": existing_grid_context if existing_grid_context else {},
        "wb_indicators_available": wb_context is not None,
        "data_sources": ["OpenStreetMap", "USGS Minerals", "Global Power Plant Database",
                         "World Bank" if wb_context else "World Bank (unavailable)",
                         "Transmission Grid" if existing_grid_context else "Transmission Grid (unavailable)"],
        "message": (
            f"{len(gaps)} economic gaps identified along the corridor with "
            f"{total_unmet_mw:,.1f} MW of unmet demand. "
            f"{len(generation_coords)} generation plants detected in corridor for proximity analysis."
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
