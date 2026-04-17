import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from src.shared.agents.utils.coords import extract_lon_lat

logger = logging.getLogger("corridor.agent.opportunity.prioritize")

# MCDA scoring weights
WEIGHTS = {
    "bankability": 0.35,
    "current_demand": 0.25,
    "growth_trajectory": 0.20,
    "gap_severity": 0.15,
    "cluster_bonus": 0.05,
}

# Sector bankability priors (used for scoring)
SECTOR_BANKABILITY = {
    "port_facility": 0.84,
    "airport": 0.78,
    "industrial_zone": 0.68,
    "mineral_site": 0.72,
    "rail_network": 0.55,
    "border_crossing": 0.45,
}

# Base demand by type (MW)
BASE_DEMAND = {
    "port_facility": 20.0,
    "airport": 15.0,
    "industrial_zone": 30.0,
    "mineral_site": 25.0,
    "rail_network": 5.0,
    "border_crossing": 2.0,
}

# Growth rate by sector (20-year multiplier)
GROWTH_MULTIPLIER = {
    "port_facility": 2.5,
    "airport": 2.2,
    "industrial_zone": 2.8,
    "mineral_site": 1.8,
    "rail_network": 1.5,
    "border_crossing": 1.3,
}


def _score_opportunity(det: dict) -> dict | None:
    """Score a detection using weighted MCDA methodology."""
    det_type = det.get("type", "other")

    # Skip generation assets
    if det_type == "power_plant":
        return None

    props = det.get("properties", {})
    confidence = det.get("confidence", 0.5)

    # Component scores (normalized 0-100)
    bankability_raw = SECTOR_BANKABILITY.get(det_type, 0.50)
    bankability_score = bankability_raw * 100

    demand_mw = BASE_DEMAND.get(det_type, 5.0)
    demand_score = min(demand_mw / 50.0 * 100, 100)  # 50 MW = max score

    growth_mult = GROWTH_MULTIPLIER.get(det_type, 1.5)
    growth_score = min((growth_mult - 1.0) / 2.0 * 100, 100)  # 3x growth = max

    gap_score = 70 if demand_mw >= 20.0 else 50 if demand_mw >= 10.0 else 30

    # Cluster bonus: higher for industrial zones and ports (tend to cluster)
    cluster_score = 80 if det_type in {"industrial_zone", "port_facility"} else 40

    # Weighted composite
    composite = (
        WEIGHTS["bankability"] * bankability_score
        + WEIGHTS["current_demand"] * demand_score
        + WEIGHTS["growth_trajectory"] * growth_score
        + WEIGHTS["gap_severity"] * gap_score
        + WEIGHTS["cluster_bonus"] * cluster_score
    )

    # Confidence adjustment
    composite *= (0.7 + 0.3 * confidence)
    composite = round(composite, 1)

    # Phase assignment
    if composite >= 65:
        phase = "Phase 1"
        phase_label = "Anchor & De-Risk (Years 1-3)"
    elif composite >= 45:
        phase = "Phase 2"
        phase_label = "Scale & Extend (Years 3-7)"
    else:
        phase = "Phase 3"
        phase_label = "Deepen & Catalyse (Years 7-15)"

    country = props.get("country", props.get("addr:country", "Unknown"))

    coords = det.get("coordinates", [])
    pt = extract_lon_lat(coords)
    longitude = pt[0] if pt else None
    latitude = pt[1] if pt else None

    return {
        "detection_id": det.get("detection_id", ""),
        "anchor_id": det.get("detection_id", ""),
        "entity_name": det.get("name", "Unknown"),
        "name": det.get("name", "Unknown"),
        "type": det_type,
        "sector": det_type.replace("_", " ").title(),
        "country": country,
        "latitude": latitude,
        "longitude": longitude,
        "composite_score": composite,
        "phase": phase,
        "phase_label": phase_label,
        "component_scores": {
            "bankability": round(bankability_score, 1),
            "current_demand_mw": demand_mw,
            "demand_score": round(demand_score, 1),
            "growth_multiplier_20yr": growth_mult,
            "growth_score": round(growth_score, 1),
            "gap_score": gap_score,
            "cluster_score": cluster_score,
        },
    }


@tool("prioritize_opportunities", description=TOOL_DESCRIPTION)
def prioritize_opportunities_tool(
    payload: dict, runtime: ToolRuntime
) -> Command:
    """
    Synthesizes all upstream analysis into a ranked, phased action plan
    for infrastructure investment using real pipeline data.
    """
    from src.adapters.pipeline_bridge import pipeline_bridge

    try:
        infra = pipeline_bridge.get_infrastructure_detections()
    except Exception as exc:
        logger.error("Infrastructure data unavailable: %s", exc)
        return Command(update={"messages": [ToolMessage(
            content=json.dumps({
                "error": str(exc),
                "priority_list": [],
                "message": "Cannot prioritize — infrastructure data unavailable.",
            }),
            tool_call_id=runtime.tool_call_id,
        )]})

    detections = infra.get("detections", [])

    # Get live market signals to enrich growth trajectory scoring
    growth_boost_sectors = set()
    market_signals = []
    try:
        news = pipeline_bridge.search_corridor_news(
            query="West Africa port industrial mining expansion investment growth corridor",
            max_results=3,
        )
        if news.get("status") == "success":
            sector_keywords = {
                "port_facility": ["port", "shipping", "maritime", "logistics"],
                "airport": ["airport", "aviation", "air cargo"],
                "industrial_zone": ["industrial", "factory", "manufacturing", "SEZ"],
                "mineral_site": ["mining", "mineral", "gold", "bauxite", "lithium"],
            }
            for item in news.get("results", []):
                content = item.get("content", "").lower()
                market_signals.append({"title": item.get("title", ""), "url": item.get("url", "")})
                for sector, keywords in sector_keywords.items():
                    if any(kw in content for kw in keywords):
                        growth_boost_sectors.add(sector)
    except Exception as exc:
        logger.warning("Market signals unavailable: %s", exc)

    # Get planned energy projects for generation proximity bonus
    generation_pipeline_context = {}
    try:
        planned = pipeline_bridge.get_planned_energy_projects()
        projects = planned.get("projects", [])
        capacity_summary = planned.get("capacity_summary", {})
        generation_pipeline_context = {
            "total_planned_projects": len(projects),
            "capacity_summary": capacity_summary,
            "projects_by_country": {},
        }
        for proj in projects:
            c = proj.get("country", "Unknown")
            generation_pipeline_context["projects_by_country"].setdefault(c, []).append({
                "name": proj.get("name", ""),
                "capacity_mw": proj.get("capacity_mw", 0),
                "status": proj.get("status", ""),
            })
        logger.info("Planned energy projects obtained: %d", len(projects))
    except Exception as exc:
        logger.warning("Planned energy projects unavailable: %s", exc)

    # Score and rank all demand-side detections
    scored = []
    generation_excluded = 0
    for det in detections:
        result = _score_opportunity(det)
        if result is None:
            generation_excluded += 1
            continue
        # Apply live news growth boost for sectors with positive signals
        if det.get("type") in growth_boost_sectors:
            result["composite_score"] = round(result["composite_score"] * 1.05, 1)
            result["news_boosted"] = True
        # Apply generation proximity bonus if planned projects exist in same country
        if generation_pipeline_context:
            det_country = det.get("properties", {}).get("country", det.get("properties", {}).get("addr:country", ""))
            if det_country in generation_pipeline_context.get("projects_by_country", {}):
                result["composite_score"] = round(result["composite_score"] * 1.03, 1)
                result["generation_proximity_bonus"] = True
        scored.append(result)

    # Sort by composite score descending
    scored.sort(key=lambda x: x["composite_score"], reverse=True)

    # Assign ranks
    for i, entry in enumerate(scored):
        entry["rank"] = i + 1

    # Phase summaries
    phase_counts: dict[str, int] = {}
    phase_demand: dict[str, float] = {}
    for entry in scored:
        p = entry["phase"]
        phase_counts[p] = phase_counts.get(p, 0) + 1
        mw = entry["component_scores"]["current_demand_mw"]
        phase_demand[p] = phase_demand.get(p, 0) + mw

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "total_anchors_ranked": len(scored),
        "generation_assets_excluded": generation_excluded,
        "scoring_methodology": WEIGHTS,
        "priority_list": scored,
        "phase_summary": {
            phase: {
                "count": phase_counts.get(phase, 0),
                "total_demand_mw": round(phase_demand.get(phase, 0), 1),
            }
            for phase in ["Phase 1", "Phase 2", "Phase 3"]
        },
        "generation_pipeline_context": generation_pipeline_context if generation_pipeline_context else {},
        "market_signals": market_signals[:3] if market_signals else [],
        "growth_boost_sectors": list(growth_boost_sectors) if growth_boost_sectors else [],
        "data_sources": [
            "OpenStreetMap", "USGS Minerals", "Global Power Plant Database",
        ] + (["Tavily live news"] if market_signals else [])
          + (["Planned Energy Projects"] if generation_pipeline_context else []),
        "message": (
            f"{len(scored)} opportunities ranked across 3 phases. "
            f"Phase 1: {phase_counts.get('Phase 1', 0)} anchors, "
            f"Phase 2: {phase_counts.get('Phase 2', 0)} scale targets, "
            f"Phase 3: {phase_counts.get('Phase 3', 0)} catalytic opportunities."
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
