import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import StakeholderRiskInput

logger = logging.getLogger("corridor.agent.stakeholder.risk")

# Risk categories and base assessment
RISK_CATEGORIES = [
    {
        "category": "Political Risk",
        "risks": [
            {"risk": "Cross-border regulatory misalignment", "base_level": "High",
             "mitigation": "WAPP-led tariff and licensing harmonization"},
            {"risk": "Government contract renegotiation", "base_level": "Medium",
             "mitigation": "MIGA political risk insurance + ICSID arbitration clause"},
            {"risk": "Election-cycle policy changes", "base_level": "Medium",
             "mitigation": "Multi-government treaty framework via ECOWAS"},
        ],
    },
    {
        "category": "Social Risk",
        "risks": [
            {"risk": "Community displacement opposition", "base_level": "Medium",
             "mitigation": "Early community engagement + CSR investment in affected areas"},
            {"risk": "Land acquisition disputes", "base_level": "Medium",
             "mitigation": "Fair compensation framework aligned with IFC Performance Standard 5"},
            {"risk": "Environmental opposition from NGOs", "base_level": "Low",
             "mitigation": "ESIA compliance + climate co-benefit documentation"},
        ],
    },
    {
        "category": "Coordination Risk",
        "risks": [
            {"risk": "Multi-country approval timeline delays", "base_level": "High",
             "mitigation": "Parallel processing with ECOWAS facilitation"},
            {"risk": "Utility off-take agreement misalignment", "base_level": "Medium",
             "mitigation": "WAPP standardized wheeling agreement templates"},
        ],
    },
    {
        "category": "Security Risk",
        "risks": [
            {"risk": "Conflict disruption to construction/operations", "base_level": "Variable",
             "mitigation": "Route optimization to avoid conflict hotspots + security force agreements"},
        ],
    },
]

# Conflict event thresholds for risk escalation
CONFLICT_THRESHOLDS = {"low": 50, "medium": 200, "high": 500}


@tool("assess_stakeholder_risks", description=TOOL_DESCRIPTION)
def assess_stakeholder_risks_tool(
    payload: StakeholderRiskInput, runtime: ToolRuntime
) -> Command:
    """Populates a Risk Register with political, social, and coordination risks."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    # Get conflict data for security risk assessment
    conflict_events = 0
    conflict_hotspots = []
    try:
        conflict = pipeline_bridge.get_conflict_data()
        conflict_events = conflict.get("total_events", 0)
        # Extract hotspot areas if available
        for event in conflict.get("events", [])[:10]:
            loc = event.get("location", event.get("admin1", "Unknown"))
            if loc not in conflict_hotspots:
                conflict_hotspots.append(loc)
    except Exception as exc:
        logger.warning("Conflict data unavailable: %s", exc)

    # Get WB indicators for governance risk context
    governance_risk = "Medium"
    try:
        wb = pipeline_bridge.get_worldbank_indicators()
        indicators = wb.get("indicators")
        if indicators:
            governance_risk = "Medium"  # Could refine with actual governance scores
    except Exception as exc:
        logger.warning("World Bank data unavailable: %s", exc)

    # Get sovereign risk data for governance/corruption context
    governance_context = {}
    try:
        sov_risk = pipeline_bridge.get_sovereign_risk()
        cpi_scores = sov_risk.get("cpi_scores", [])
        governance_data = sov_risk.get("governance", {})
        governance_context = {
            "cpi_scores": cpi_scores,
            "governance_indices": governance_data,
            "source": sov_risk.get("source", "Transparency International / V-Dem"),
        }
        # Refine governance risk level using CPI data
        if cpi_scores:
            avg_cpi = sum(
                float(e.get("score", e.get("cpi_score", 35)))
                for e in cpi_scores if e.get("score") or e.get("cpi_score")
            ) / max(len(cpi_scores), 1)
            if avg_cpi < 25:
                governance_risk = "Critical"
            elif avg_cpi < 35:
                governance_risk = "High"
            elif avg_cpi < 50:
                governance_risk = "Medium"
            else:
                governance_risk = "Low"
            governance_context["average_cpi"] = round(avg_cpi, 1)
            governance_context["derived_risk_level"] = governance_risk
        logger.info("Sovereign risk data obtained: %d CPI scores, governance risk: %s",
                     len(cpi_scores), governance_risk)
    except Exception as exc:
        logger.warning("Sovereign risk data unavailable: %s", exc)

    # Get corridor countries
    try:
        corridor = pipeline_bridge.get_corridor_info()
        countries = corridor.get("countries", [])
    except Exception as exc:
        logger.warning("Corridor info unavailable: %s", exc)
        countries = ["NGA", "GHA", "CIV", "TGO", "BEN"]

    # Search for live risk-related news via Tavily
    live_risk_alerts = []
    try:
        news = pipeline_bridge.search_corridor_news(
            query="Lagos Abidjan corridor risk conflict protest regulation delay infrastructure",
            max_results=5,
        )
        if news.get("status") == "success":
            for item in news.get("results", []):
                live_risk_alerts.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "summary": item.get("content", "")[:200],
                })
    except Exception as exc:
        logger.warning("News search unavailable: %s", exc)

    # Build risk register with conflict-adjusted levels
    risk_register = []
    for category in RISK_CATEGORIES:
        for risk_item in category["risks"]:
            level = risk_item["base_level"]

            # Adjust security risk based on real conflict data
            if category["category"] == "Security Risk" and level == "Variable":
                if conflict_events >= CONFLICT_THRESHOLDS["high"]:
                    level = "Critical"
                elif conflict_events >= CONFLICT_THRESHOLDS["medium"]:
                    level = "High"
                elif conflict_events >= CONFLICT_THRESHOLDS["low"]:
                    level = "Medium"
                else:
                    level = "Low"

            risk_register.append({
                "category": category["category"],
                "risk": risk_item["risk"],
                "level": level,
                "mitigation": risk_item["mitigation"],
            })

    # Count by severity
    severity_counts = {}
    for r in risk_register:
        severity_counts[r["level"]] = severity_counts.get(r["level"], 0) + 1

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "analysis_type": "Stakeholder Risk Assessment",
        "countries_analyzed": countries,
        "risk_register": risk_register,
        "risk_summary": {
            "total_risks_identified": len(risk_register),
            "by_severity": severity_counts,
        },
        "conflict_context": {
            "total_conflict_events": conflict_events,
            "hotspot_areas": conflict_hotspots[:5],
            "security_risk_level": next(
                (r["level"] for r in risk_register if r["category"] == "Security Risk"), "Unknown"
            ),
        },
        "governance_risk_level": governance_risk,
        "governance_context": governance_context if governance_context else {},
        "live_risk_alerts": live_risk_alerts[:3] if live_risk_alerts else [],
        "data_sources": [
            "ACLED conflict data" if conflict_events > 0 else "ACLED (unavailable)",
            "Tavily live news" if live_risk_alerts else "Tavily (unavailable)",
            "Sovereign Risk (CPI/V-Dem)" if governance_context else "Sovereign Risk (unavailable)",
            "Corridor AOI",
            "IFC Performance Standards",
        ],
        "message": (
            f"Risk assessment complete: {len(risk_register)} risks identified across "
            f"{len(RISK_CATEGORIES)} categories for {len(countries)} countries. "
            f"Severity: {severity_counts}. "
            f"Conflict events: {conflict_events} "
            f"({'hotspots: ' + ', '.join(conflict_hotspots[:3]) if conflict_hotspots else 'no hotspot data'}). "
            f"Governance risk: {governance_risk}."
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
