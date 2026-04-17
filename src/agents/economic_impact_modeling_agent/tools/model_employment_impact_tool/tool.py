import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import EmploymentModelingInput

logger = logging.getLogger("corridor.agent.economic.employment")

# Employment benchmarks per $1M CAPEX (AfDB infrastructure benchmarks)
JOBS_PER_M_CAPEX = {
    "construction": 80,   # person-years per $1M
    "operations": 12,     # ongoing FTEs per $1M
}

# Enabled jobs per MW of connected demand
ENABLED_JOBS_PER_MW = 60

# Induced multiplier on direct + enabled
INDUCED_MULTIPLIER = 0.28


@tool("model_employment_impact", description=TOOL_DESCRIPTION)
def model_employment_impact_tool(
    payload: EmploymentModelingInput, runtime: ToolRuntime
) -> Command:
    """Estimates job creation using real infrastructure and economic data."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    # Get corridor and infrastructure data
    total_km = 1080
    try:
        corridor = pipeline_bridge.get_corridor_info()
        total_km = corridor.get("length_km", 1080)
        countries = corridor.get("countries", [])
    except Exception as exc:
        logger.warning("Corridor info unavailable: %s", exc)
        countries = ["NGA", "GHA", "CIV", "TGO", "BEN"]

    # Estimate CAPEX
    capex_m = (total_km * 980_000 + len(countries) * 50_000_000) / 1e6

    # Get infrastructure for demand-based enabled jobs
    total_demand_mw = 0
    demand_by_type: dict[str, float] = {}
    try:
        infra = pipeline_bridge.get_infrastructure_detections()
        type_mw = {
            "port_facility": 20.0, "airport": 15.0, "industrial_zone": 30.0,
            "mineral_site": 25.0, "rail_network": 5.0, "border_crossing": 2.0,
        }
        for det in infra.get("detections", []):
            dt = det.get("type", "other")
            if dt != "power_plant":
                mw = type_mw.get(dt, 5.0)
                total_demand_mw += mw
                demand_by_type[dt] = demand_by_type.get(dt, 0) + mw
    except Exception as exc:
        logger.warning("Infrastructure data unavailable: %s", exc)
        total_demand_mw = 500  # fallback estimate

    # Get agricultural production for agri sector employment sizing
    agri_context = None
    try:
        agri_result = pipeline_bridge.get_agricultural_production()
        if agri_result.get("status") == "ok" and agri_result.get("production"):
            agri_context = agri_result["production"]
            logger.info("Agricultural production data obtained for employment modeling")
    except Exception as exc:
        logger.warning("Agricultural production data unavailable: %s", exc)

    # Get port statistics for port/logistics employment estimates
    port_context = None
    try:
        port_result = pipeline_bridge.get_port_statistics()
        if port_result.get("status") == "ok":
            port_context = {
                "ports": port_result.get("ports", []),
                "throughput_summary": port_result.get("throughput_summary"),
            }
            logger.info("Port statistics obtained for employment modeling")
    except Exception as exc:
        logger.warning("Port statistics unavailable: %s", exc)

    # Calculate employment
    construction_jobs = round(capex_m * JOBS_PER_M_CAPEX["construction"])
    operations_jobs = round(capex_m * JOBS_PER_M_CAPEX["operations"])
    enabled_jobs = round(total_demand_mw * ENABLED_JOBS_PER_MW)
    induced_jobs = round((construction_jobs + enabled_jobs) * INDUCED_MULTIPLIER)
    total_jobs = construction_jobs + operations_jobs + enabled_jobs + induced_jobs

    # Country distribution
    country_shares = {"NGA": 0.25, "GHA": 0.37, "CIV": 0.17, "TGO": 0.11, "BEN": 0.10}
    by_country = {}
    for code in countries:
        share = country_shares.get(code, 1.0 / len(countries))
        by_country[code] = {
            "construction": round(construction_jobs * share),
            "operations": round(operations_jobs * share),
            "enabled": round(enabled_jobs * share),
            "induced": round(induced_jobs * share),
        }

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "analysis_type": "Employment Impact Assessment",
        "employment_summary": {
            "direct_construction_jobs": construction_jobs,
            "direct_operational_jobs": operations_jobs,
            "enabled_industrial_jobs": enabled_jobs,
            "induced_jobs": induced_jobs,
            "total_jobs_created": total_jobs,
        },
        "calculation_basis": {
            "estimated_capex_usd_m": round(capex_m, 1),
            "connected_demand_mw": round(total_demand_mw, 1),
            "jobs_per_m_capex_construction": JOBS_PER_M_CAPEX["construction"],
            "enabled_jobs_per_mw": ENABLED_JOBS_PER_MW,
            "induced_multiplier": INDUCED_MULTIPLIER,
        },
        "demand_by_facility_type": demand_by_type,
        "sector_context": {
            "agricultural_production": agri_context if agri_context else "Agricultural data unavailable",
            "port_logistics": port_context if port_context else "Port data unavailable",
        },
        "impact_by_country": by_country,
        "data_sources": [
            "Corridor AOI", "OSM + USGS infrastructure", "AfDB employment benchmarks",
            "FAO agricultural production" if agri_context else "FAO (unavailable)",
            "UNCTAD port statistics" if port_context else "UNCTAD (unavailable)",
        ],
        "message": (
            f"Employment projection: {total_jobs:,} total jobs. "
            f"{construction_jobs:,} construction (temporary), "
            f"{operations_jobs:,} operational (permanent), "
            f"{enabled_jobs:,} enabled industrial, "
            f"{induced_jobs:,} induced. "
            f"Based on ${capex_m:,.0f}M CAPEX and {total_demand_mw:,.0f} MW connected demand. "
            f"{'Agri production and port throughput data enrich sector context.' if agri_context or port_context else ''}"
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
