import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import EngagementRoadmapInput

logger = logging.getLogger("corridor.agent.stakeholder.roadmap")

# Engagement phase templates
PHASE_TEMPLATES = [
    {
        "phase": 1,
        "name": "Champion Mobilization",
        "month_pct": (0.0, 0.17),  # first ~17% of timeline
        "target_groups": ["DFIs", "Regional Bodies", "Key Government Ministers"],
        "focus": "Secure political buy-in and concessional finance commitment",
        "kpis": ["MOU signatures", "DFI pre-appraisal initiated", "ECOWAS endorsement letter"],
    },
    {
        "phase": 2,
        "name": "Private Sector & Utility Engagement",
        "month_pct": (0.17, 0.42),
        "target_groups": ["Anchor Load Companies", "National Utilities", "IPPs"],
        "focus": "Off-take agreements and commercial partnership",
        "kpis": ["LOIs from anchor loads", "Wheeling agreement drafts", "PPP framework agreed"],
    },
    {
        "phase": 3,
        "name": "Community & Social License",
        "month_pct": (0.42, 0.75),
        "target_groups": ["Affected Communities", "Local NGOs", "Traditional Leaders"],
        "focus": "Social license to operate and land acquisition",
        "kpis": ["Community consultations completed", "RAP approved", "CSR commitments signed"],
    },
    {
        "phase": 4,
        "name": "Regulatory & Final Approval",
        "month_pct": (0.75, 1.0),
        "target_groups": ["National Regulators", "Environmental Agencies", "Finance Ministries"],
        "focus": "Licensing, permits, and financial close preparation",
        "kpis": ["Generation/transmission licenses", "ESIA approval", "Tariff determination"],
    },
]


@tool("generate_engagement_roadmap", description=TOOL_DESCRIPTION)
def generate_engagement_roadmap_tool(
    payload: EngagementRoadmapInput, runtime: ToolRuntime
) -> Command:
    """Creates a phased engagement roadmap aligned with the project lifecycle."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    timeline_months = payload.project_timeline_months or 24
    influence_data = payload.influence_data or {}

    # Get corridor info for scale
    try:
        corridor = pipeline_bridge.get_corridor_info()
        countries = corridor.get("countries", [])
    except Exception as exc:
        logger.warning("Corridor info unavailable: %s", exc)
        countries = ["NGA", "GHA", "CIV", "TGO", "BEN"]

    # Get infrastructure for private sector stakeholder count
    private_sector_count = 0
    try:
        infra = pipeline_bridge.get_infrastructure_detections()
        private_sector_count = len(infra.get("detections", []))
    except Exception as exc:
        logger.warning("Infrastructure data unavailable: %s", exc)
        private_sector_count = 30

    # Build roadmap phases with actual timeline
    roadmap = []
    for template in PHASE_TEMPLATES:
        start_month = max(1, round(timeline_months * template["month_pct"][0]) + 1)
        end_month = round(timeline_months * template["month_pct"][1])

        # Estimate stakeholder count per phase
        if template["phase"] == 1:
            target_count = 6 + len(countries) * 2  # DFIs + regional + ministers
        elif template["phase"] == 2:
            target_count = private_sector_count + len(countries) * 2  # utilities
        elif template["phase"] == 3:
            target_count = len(countries) * 5  # communities per country
        else:
            target_count = len(countries) * 3  # regulators per country

        roadmap.append({
            "phase": template["phase"],
            "name": template["name"],
            "months": f"{start_month}–{end_month}",
            "duration_months": end_month - start_month + 1,
            "target_groups": template["target_groups"],
            "target_stakeholder_count": target_count,
            "focus": template["focus"],
            "kpis": template["kpis"],
        })

    total_stakeholders = sum(p["target_stakeholder_count"] for p in roadmap)

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "analysis_type": "Engagement Roadmap",
        "project_timeline_months": timeline_months,
        "countries": countries,
        "roadmap": roadmap,
        "summary": {
            "total_phases": len(roadmap),
            "total_stakeholders_targeted": total_stakeholders,
            "critical_path": "Phase 1 (DFI buy-in) → Phase 2 (off-take) must complete before Phase 4 (financial close)",
        },
        "data_sources": ["Corridor AOI", "OSM + USGS infrastructure"],
        "message": (
            f"Engagement roadmap generated: {len(roadmap)} phases over {timeline_months} months "
            f"targeting {total_stakeholders} stakeholders across {len(countries)} countries. "
            f"Critical path: DFI champion mobilization (Phase 1) must precede financial close (Phase 4)."
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
