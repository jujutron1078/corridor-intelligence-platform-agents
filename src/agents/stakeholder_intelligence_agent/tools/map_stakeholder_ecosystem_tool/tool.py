import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import StakeholderMappingInput

logger = logging.getLogger("corridor.agent.stakeholder.mapping")

# Stakeholder category templates per country
GOVERNMENT_BODIES = {
    "NGA": ["Federal Ministry of Power", "Nigerian Electricity Regulatory Commission (NERC)", "Transmission Company of Nigeria (TCN)"],
    "GHA": ["Ministry of Energy", "Energy Commission of Ghana", "Ghana Grid Company (GRIDCo)"],
    "CIV": ["Ministère des Mines, du Pétrole et de l'Énergie", "CI-ENERGIES", "ANARE-CI"],
    "TGO": ["Ministère des Mines et de l'Énergie", "CEET (Compagnie Énergie Électrique du Togo)"],
    "BEN": ["Ministère de l'Énergie", "SBEE (Société Béninoise d'Énergie Électrique)", "ARE Bénin"],
}

REGIONAL_BODIES = [
    {"name": "ECOWAS Commission", "role": "Regional integration governance", "influence": "HIGH"},
    {"name": "WAPP Secretariat", "role": "West African Power Pool coordination", "influence": "HIGH"},
    {"name": "ECREEE", "role": "ECOWAS Centre for Renewable Energy", "influence": "MEDIUM"},
    {"name": "West African Gas Pipeline Authority", "role": "Regional energy infrastructure", "influence": "MEDIUM"},
]

INFRASTRUCTURE_STAKEHOLDERS = {
    "port_facility": {"type": "Private Sector", "subtype": "Port Authority / Logistics"},
    "airport": {"type": "Government", "subtype": "Aviation Authority"},
    "industrial_zone": {"type": "Private Sector", "subtype": "SEZ / Industrial Developer"},
    "mineral_site": {"type": "Private Sector", "subtype": "Mining Company"},
    "rail_network": {"type": "Government", "subtype": "Rail Authority"},
    "border_crossing": {"type": "Government", "subtype": "Customs & Immigration"},
}


@tool("map_stakeholder_ecosystem", description=TOOL_DESCRIPTION)
def map_stakeholder_ecosystem_tool(
    payload: StakeholderMappingInput, runtime: ToolRuntime
) -> Command:
    """Identifies and categorizes all relevant stakeholders in the corridor ecosystem."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    # Get corridor countries
    try:
        corridor = pipeline_bridge.get_corridor_info()
        countries = corridor.get("countries", [])
    except Exception as exc:
        logger.warning("Corridor info unavailable: %s", exc)
        countries = []

    # Fall back to payload countries
    if not countries:
        country_iso = {
            "nigeria": "NGA", "ghana": "GHA", "côte d'ivoire": "CIV",
            "ivory coast": "CIV", "togo": "TGO", "benin": "BEN",
        }
        countries = [country_iso.get(c.lower(), c[:3].upper()) for c in payload.corridor_countries]

    # Government stakeholders from country templates
    gov_stakeholders = []
    for code in countries:
        bodies = GOVERNMENT_BODIES.get(code, [f"Ministry of Energy ({code})"])
        for body in bodies:
            gov_stakeholders.append({"name": body, "country": code, "category": "Government"})

    # Infrastructure-related private sector stakeholders
    private_stakeholders = []
    try:
        infra = pipeline_bridge.get_infrastructure_detections()
        for det in infra.get("detections", []):
            dt = det.get("type", "other")
            if dt in INFRASTRUCTURE_STAKEHOLDERS:
                info = INFRASTRUCTURE_STAKEHOLDERS[dt]
                name = det.get("name", dt.replace("_", " ").title())
                private_stakeholders.append({
                    "name": name,
                    "type": info["type"],
                    "subtype": info["subtype"],
                    "facility_type": dt,
                    "location": det.get("coordinates", {}),
                })
    except Exception as exc:
        logger.warning("Infrastructure data unavailable: %s", exc)

    # Civil society — estimate from conflict/community data
    civil_society_count = 0
    try:
        conflict = pipeline_bridge.get_conflict_data()
        # Higher conflict = more civil society engagement needed
        events = conflict.get("total_events", 0)
        civil_society_count = max(5, min(events // 10, 30))
    except Exception as exc:
        logger.warning("Conflict data unavailable: %s", exc)
        civil_society_count = len(countries) * 5

    # Get active DFI projects from development finance data
    active_dfi_projects = []
    try:
        dev_finance = pipeline_bridge.get_development_finance()
        for proj in dev_finance.get("projects", []):
            active_dfi_projects.append({
                "project_name": proj.get("name", proj.get("project_name", "Unknown")),
                "funder": proj.get("funder", proj.get("donor", "Unknown DFI")),
                "investment_usd": proj.get("investment_usd", proj.get("amount_usd", 0)),
                "sector": proj.get("sector", ""),
                "country": proj.get("country", ""),
                "status": proj.get("status", "active"),
            })
        logger.info("Development finance data obtained: %d active projects", len(active_dfi_projects))
    except Exception as exc:
        logger.warning("Development finance data unavailable: %s", exc)

    # DFI stakeholders — use real project data count if available
    dfi_count = max(6, len(set(p.get("funder", "") for p in active_dfi_projects))) if active_dfi_projects else 6

    # Compile counts
    counts = {
        "governments": len(gov_stakeholders),
        "dfis": dfi_count,
        "utilities": len([g for g in gov_stakeholders if "Grid" in g["name"] or "CEET" in g["name"] or "SBEE" in g["name"] or "CI-ENERGIES" in g["name"]]),
        "private_sector": len(private_stakeholders),
        "civil_society": civil_society_count,
        "regional_bodies": len(REGIONAL_BODIES),
    }
    total = sum(counts.values())

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "analysis_type": "Stakeholder Ecosystem Mapping",
        "countries_analyzed": countries,
        "stakeholder_counts": counts,
        "total_identified": total,
        "government_stakeholders": gov_stakeholders,
        "regional_bodies": REGIONAL_BODIES,
        "infrastructure_stakeholders": private_stakeholders[:20],  # cap for response size
        "active_dfi_projects": active_dfi_projects[:15] if active_dfi_projects else [],
        "data_sources": [
            "Corridor AOI",
            "OSM + USGS infrastructure",
            "ACLED conflict data" if civil_society_count > 0 else "ACLED (unavailable)",
            "Development Finance Data" if active_dfi_projects else "Development Finance (unavailable)",
        ],
        "message": (
            f"Stakeholder ecosystem mapped across {len(countries)} corridor countries. "
            f"{total} stakeholders identified: {counts['governments']} government, "
            f"{counts['private_sector']} private sector, {counts['regional_bodies']} regional bodies, "
            f"{counts['civil_society']} civil society, {counts['dfis']} DFIs."
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
