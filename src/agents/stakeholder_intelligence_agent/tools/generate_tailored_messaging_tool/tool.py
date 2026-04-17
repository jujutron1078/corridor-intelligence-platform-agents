import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import MessagingInput

logger = logging.getLogger("corridor.agent.stakeholder.messaging")

# Messaging templates by stakeholder type
MESSAGING_FRAMEWORKS = {
    "dfi": {
        "narrative": "Catalytic Infrastructure for Regional Integration",
        "value_props": [
            "Cross-border transmission unlocks regional power trade",
            "Blended finance structure reduces WACC below 6%",
            "Climate co-benefits from renewable integration",
        ],
        "tone": "Technical, data-driven, development impact focused",
        "format": "Investment Brief + Board Paper Summary",
    },
    "government": {
        "narrative": "National Development Through Regional Connectivity",
        "value_props": [
            "GDP uplift and employment creation",
            "Energy access expansion for underserved populations",
            "Revenue generation from wheeling charges",
        ],
        "tone": "Policy-oriented, sovereignty-respecting, jobs-focused",
        "format": "Policy Brief + Cabinet Memo",
    },
    "private_sector": {
        "narrative": "Reliable Power for Industrial Growth",
        "value_props": [
            "Reduced energy costs through grid-scale supply",
            "Improved power reliability (N-1 redundancy)",
            "Co-location benefits reduce infrastructure costs",
        ],
        "tone": "Commercial, ROI-focused, operational",
        "format": "Commercial Proposal + Off-take Term Sheet",
    },
    "community": {
        "narrative": "Shared Prosperity and Local Benefits",
        "value_props": [
            "Local employment during construction",
            "Electrification of surrounding communities",
            "CSR investment in education and health facilities",
        ],
        "tone": "Accessible, empathetic, benefits-focused",
        "format": "Community Brochure + Town Hall Presentation",
    },
    "civil_society": {
        "narrative": "Sustainable Development with Social Safeguards",
        "value_props": [
            "ESIA compliance and environmental monitoring",
            "Fair compensation for land acquisition",
            "Climate-positive infrastructure design",
        ],
        "tone": "Transparent, evidence-based, accountability-focused",
        "format": "Environmental & Social Impact Summary + Public Consultation Report",
    },
}


@tool("generate_tailored_messaging", description=TOOL_DESCRIPTION)
def generate_tailored_messaging_tool(
    payload: MessagingInput, runtime: ToolRuntime
) -> Command:
    """Produces customized messaging frameworks for stakeholder outreach."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    stakeholder_type = payload.stakeholder_type.lower().replace(" ", "_")
    key_interests = payload.key_interests or []

    # Get real project metrics for messaging data points
    metrics = {}
    try:
        corridor = pipeline_bridge.get_corridor_info()
        metrics["corridor_length_km"] = corridor.get("length_km", 0)
        metrics["countries"] = corridor.get("countries", [])
    except Exception as exc:
        logger.warning("Corridor info unavailable: %s", exc)

    try:
        wb = pipeline_bridge.get_worldbank_indicators()
        indicators = wb.get("indicators")
        if indicators:
            metrics["wb_data_available"] = True
    except Exception as exc:
        logger.warning("World Bank data unavailable: %s", exc)

    # Get infrastructure scale for messaging
    try:
        infra = pipeline_bridge.get_infrastructure_detections()
        detections = infra.get("detections", [])
        metrics["infrastructure_nodes"] = len(detections)
        metrics["facility_types"] = list(set(d.get("type", "other") for d in detections))
    except Exception as exc:
        logger.warning("Infrastructure data unavailable: %s", exc)

    # Match messaging framework
    framework = MESSAGING_FRAMEWORKS.get(
        stakeholder_type,
        MESSAGING_FRAMEWORKS.get("private_sector")  # default
    )

    # Customize value props with real data
    data_points = []
    if metrics.get("corridor_length_km"):
        data_points.append(f"{metrics['corridor_length_km']} km corridor")
    if metrics.get("countries"):
        data_points.append(f"{len(metrics['countries'])} countries connected")
    if metrics.get("infrastructure_nodes"):
        data_points.append(f"{metrics['infrastructure_nodes']} infrastructure nodes")

    # Add key interests to messaging
    if key_interests:
        framework = dict(framework)  # copy
        framework["stakeholder_interests"] = key_interests

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "analysis_type": "Tailored Messaging Generation",
        "stakeholder_type": stakeholder_type,
        "messaging_framework": framework,
        "key_data_points": data_points,
        "project_metrics": metrics,
        "data_sources": ["Corridor AOI", "OSM + USGS infrastructure"],
        "message": (
            f"Messaging framework generated for '{stakeholder_type}' stakeholder type. "
            f"Narrative: '{framework['narrative']}'. "
            f"Format: {framework['format']}. "
            f"Key data points: {', '.join(data_points) if data_points else 'corridor data pending'}."
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
