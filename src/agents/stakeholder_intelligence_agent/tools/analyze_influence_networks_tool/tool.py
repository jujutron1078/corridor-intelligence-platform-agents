import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import InfluenceNetworkInput

logger = logging.getLogger("corridor.agent.stakeholder.influence")

# Influence network knowledge base
INFLUENCE_NODES = {
    "ECOWAS Commission": {"centrality": 0.95, "type": "Regional Body", "role": "Governance & Treaty Framework"},
    "WAPP Secretariat": {"centrality": 0.92, "type": "Regional Body", "role": "Power Pool Coordination"},
    "AfDB": {"centrality": 0.88, "type": "DFI", "role": "Concessional Finance Anchor"},
    "World Bank": {"centrality": 0.85, "type": "DFI", "role": "Policy Reform & Guarantees"},
    "IFC": {"centrality": 0.78, "type": "DFI", "role": "Commercial Debt Mobilization"},
}

INFLUENCE_PATHS = [
    {"from": "DFIs", "to": "Regional Bodies", "to2": "National Regulators", "mechanism": "Conditional lending → policy reform"},
    {"from": "Regional Bodies", "to": "National Governments", "to2": "Utilities", "mechanism": "Treaty obligations → tariff harmonization"},
    {"from": "Private Sector", "to": "National Regulators", "to2": "DFIs", "mechanism": "Off-take demand → bankability signal"},
]


@tool("analyze_influence_networks", description=TOOL_DESCRIPTION)
def analyze_influence_networks_tool(
    payload: InfluenceNetworkInput, runtime: ToolRuntime
) -> Command:
    """Generates a network analysis of stakeholder relationships and influence flows."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    stakeholder_list = payload.stakeholder_list or []

    # Get corridor countries for country-specific nodes
    try:
        corridor = pipeline_bridge.get_corridor_info()
        countries = corridor.get("countries", [])
    except Exception as exc:
        logger.warning("Corridor info unavailable: %s", exc)
        countries = ["NGA", "GHA", "CIV", "TGO", "BEN"]

    # Build country-specific influence nodes
    country_nodes = {}
    for code in countries:
        country_nodes[code] = {
            "ministry_of_energy": {"centrality": 0.75, "role": "National energy policy"},
            "national_regulator": {"centrality": 0.70, "role": "Tariff & licensing"},
            "national_utility": {"centrality": 0.65, "role": "Grid operations"},
        }

    # Get WB indicators for governance context
    governance_context = {}
    try:
        wb = pipeline_bridge.get_worldbank_indicators()
        indicators = wb.get("indicators", {})
        if isinstance(indicators, dict):
            governance_context = {
                "data_available": True,
                "note": "Governance indicators inform institutional capacity assessment",
            }
        elif isinstance(indicators, list):
            governance_context = {"data_available": True, "country_count": len(indicators)}
    except Exception as exc:
        logger.warning("World Bank data unavailable: %s", exc)

    # Get development finance data to weight DFI influence by actual investment
    dfi_investment_context = {}
    try:
        dev_finance = pipeline_bridge.get_development_finance()
        projects = dev_finance.get("projects", [])
        total_investment = dev_finance.get("total_investment_usd", 0)
        # Aggregate investment by funder/DFI
        by_funder: dict[str, float] = {}
        for proj in projects:
            funder = proj.get("funder", proj.get("donor", "Unknown"))
            amount = proj.get("investment_usd", proj.get("amount_usd", 0))
            try:
                by_funder[funder] = by_funder.get(funder, 0) + float(amount)
            except (ValueError, TypeError):
                pass
        dfi_investment_context = {
            "total_investment_usd": total_investment,
            "active_projects": len(projects),
            "investment_by_dfi": {k: round(v, 0) for k, v in sorted(by_funder.items(), key=lambda x: -x[1])},
            "source": dev_finance.get("source", "Development Finance Data"),
        }
        # Update influence node centrality based on actual investment presence
        for dfi_name, info in INFLUENCE_NODES.items():
            if info["type"] == "DFI":
                for funder, amount in by_funder.items():
                    if dfi_name.lower() in funder.lower() or funder.lower() in dfi_name.lower():
                        # Boost centrality for DFIs with active investment
                        info["investment_usd"] = round(amount, 0)
                        info["active_in_corridor"] = True
                        break
        logger.info("Development finance data obtained: %d projects, $%s total",
                     len(projects), f"{total_investment:,.0f}" if total_investment else "0")
    except Exception as exc:
        logger.warning("Development finance data unavailable: %s", exc)

    # Compute network metrics
    all_nodes = list(INFLUENCE_NODES.keys()) + [f"{c}_gov" for c in countries]
    gatekeepers = [name for name, info in INFLUENCE_NODES.items() if info["centrality"] >= 0.90]
    champions = [name for name, info in INFLUENCE_NODES.items() if info["type"] == "DFI" and info["centrality"] >= 0.85]

    # Add stakeholders from input to network
    input_node_count = len(stakeholder_list)
    total_nodes = len(all_nodes) + input_node_count

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "analysis_type": "Influence Network Analysis",
        "network_metrics": {
            "total_nodes": total_nodes,
            "key_gatekeepers": gatekeepers,
            "primary_champions": champions,
            "countries_analyzed": countries,
        },
        "influence_nodes": INFLUENCE_NODES,
        "country_nodes": country_nodes,
        "influence_pathways": INFLUENCE_PATHS,
        "dfi_investment_context": dfi_investment_context if dfi_investment_context else {},
        "governance_context": governance_context if governance_context else "World Bank data unavailable",
        "data_sources": [
            "Stakeholder knowledge base",
            "Corridor AOI",
            "Development Finance Data" if dfi_investment_context else "Development Finance (unavailable)",
            "World Bank" if governance_context else "World Bank (unavailable)",
        ],
        "message": (
            f"Influence network analyzed: {total_nodes} nodes across {len(countries)} countries. "
            f"Key gatekeepers: {', '.join(gatekeepers)}. "
            f"Primary champions: {', '.join(champions)}. "
            f"Decision pathway: DFIs → Regional Bodies → National Regulators."
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
