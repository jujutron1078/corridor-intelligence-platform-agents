import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import DFIMatchingInput

logger = logging.getLogger("corridor.agent.financing.dfi_match")

# DFI knowledge base — real institutions with mandate profiles
DFI_DATABASE = [
    {
        "name": "African Development Bank (AfDB)",
        "abbreviation": "AfDB",
        "focus": "Regional Integration & Energy Access",
        "instrument_types": ["Concessional Loan", "Grant", "Equity", "Guarantee"],
        "typical_ticket_usd": (50_000_000, 500_000_000),
        "concessional_rate_range": "2%–4%",
        "tenor_range_years": "20–30",
        "grace_period_years": 5,
        "avg_approval_months": 14,
        "mandate_keywords": ["regional integration", "energy", "transmission", "wapp", "agro-processing"],
        "geo_priority": ["West Africa", "Pan-African"],
        "ida_eligibility": {"ADF": ["TGO", "BEN"], "ADB": ["CIV", "GHA", "NGA"]},
        "esg_requirements": ["ESAP compliance", "Climate co-benefit minimum 40%"],
    },
    {
        "name": "EU Global Gateway",
        "abbreviation": "EU-GG",
        "focus": "Green Energy, Digital Infrastructure & Climate",
        "instrument_types": ["Grant", "Blended Finance Guarantee", "Technical Assistance"],
        "typical_ticket_usd": (50_000_000, 200_000_000),
        "concessional_rate_range": "Grant (0%)",
        "tenor_range_years": "N/A (grant)",
        "grace_period_years": 0,
        "avg_approval_months": 18,
        "mandate_keywords": ["green energy", "digital", "climate", "cross-border"],
        "geo_priority": ["West Africa", "Francophone Africa"],
        "esg_requirements": ["Paris Agreement alignment", "DNSH assessment"],
    },
    {
        "name": "International Finance Corporation (IFC)",
        "abbreviation": "IFC",
        "focus": "Private Sector Infrastructure & Capital Markets",
        "instrument_types": ["Senior Loan", "Equity", "Quasi-Equity", "Guarantee (via MIGA)"],
        "typical_ticket_usd": (50_000_000, 300_000_000),
        "concessional_rate_range": "SOFR + 2.5%–3.5% (market rate)",
        "tenor_range_years": "12–18",
        "grace_period_years": 3,
        "avg_approval_months": 12,
        "mandate_keywords": ["private sector", "infrastructure", "capital markets"],
        "geo_priority": ["Sub-Saharan Africa"],
        "ida_eligibility": {"IDA_PSW": ["CIV", "TGO", "BEN"], "IBRD": ["GHA", "NGA"]},
        "esg_requirements": ["IFC Performance Standards PS1–PS8"],
    },
    {
        "name": "World Bank (IDA/IBRD)",
        "abbreviation": "WB",
        "focus": "Public Sector Infrastructure & Policy Reform",
        "instrument_types": ["IDA Credit", "IBRD Loan", "Partial Risk Guarantee", "Project Preparation Facility"],
        "typical_ticket_usd": (100_000_000, 500_000_000),
        "concessional_rate_range": "1.25%–2% (IDA) / SOFR + 0.5% (IBRD)",
        "tenor_range_years": "25–40 (IDA) / 15–25 (IBRD)",
        "grace_period_years": 5,
        "avg_approval_months": 20,
        "mandate_keywords": ["infrastructure", "policy reform", "energy access", "wapp"],
        "geo_priority": ["Global", "IDA countries"],
        "ida_eligibility": {"IDA": ["TGO", "BEN"], "IDA_blend": ["CIV"], "IBRD": ["GHA", "NGA"]},
        "esg_requirements": ["ESF compliance", "ESCP required"],
    },
    {
        "name": "U.S. International Development Finance Corporation (DFC)",
        "abbreviation": "DFC",
        "focus": "U.S. Strategic Private Sector Investment",
        "instrument_types": ["Direct Loan", "Loan Guarantee", "Political Risk Insurance", "Equity"],
        "typical_ticket_usd": (50_000_000, 250_000_000),
        "concessional_rate_range": "SOFR + 2%–3% (near-market)",
        "tenor_range_years": "10–20",
        "grace_period_years": 2,
        "avg_approval_months": 10,
        "mandate_keywords": ["energy", "digital", "private sector"],
        "geo_priority": ["Sub-Saharan Africa"],
        "esg_requirements": ["OPIC Environmental Handbook"],
    },
    {
        "name": "Agence Française de Développement (AFD)",
        "abbreviation": "AFD",
        "focus": "Francophone Africa Development & Climate",
        "instrument_types": ["Concessional Loan", "Grant", "Equity (via Proparco)", "Technical Assistance"],
        "typical_ticket_usd": (30_000_000, 150_000_000),
        "concessional_rate_range": "1.5%–3.5%",
        "tenor_range_years": "20–25",
        "grace_period_years": 5,
        "avg_approval_months": 16,
        "mandate_keywords": ["climate", "renewable", "francophone"],
        "geo_priority": ["Francophone Africa", "West Africa"],
        "francophone_priority": ["CIV", "TGO", "BEN"],
        "esg_requirements": ["AFD Exclusion List compliance"],
    },
]

# Country name to ISO mapping for matching
COUNTRY_ISO = {
    "nigeria": "NGA", "ghana": "GHA", "côte d'ivoire": "CIV",
    "ivory coast": "CIV", "togo": "TGO", "benin": "BEN",
    "senegal": "SEN", "mali": "MLI", "niger": "NER",
    "cameroon": "CMR", "burkina faso": "BFA",
}


def _score_dfi(dfi: dict, countries: list[str], sectors: list[str], capex: float) -> float:
    """Score a DFI against project characteristics (0-1 scale)."""
    score = 0.0
    weights_total = 0.0

    # Sector match (40% weight)
    sector_lower = [s.lower() for s in sectors]
    keyword_hits = sum(
        1 for kw in dfi["mandate_keywords"]
        if any(kw in s for s in sector_lower)
    )
    sector_score = min(keyword_hits / max(len(dfi["mandate_keywords"]), 1), 1.0)
    score += sector_score * 0.4
    weights_total += 0.4

    # Geographic match (30% weight)
    geo_score = 0.5  # baseline
    if any("West Africa" in g or "Pan-African" in g or "Global" in g for g in dfi.get("geo_priority", [])):
        geo_score = 0.8
    if any("Francophone" in g for g in dfi.get("geo_priority", [])):
        francophone_countries = {"CIV", "TGO", "BEN", "SEN", "MLI", "NER", "BFA"}
        if set(countries) & francophone_countries:
            geo_score = max(geo_score, 0.9)
    score += geo_score * 0.3
    weights_total += 0.3

    # Ticket size match (20% weight)
    min_t, max_t = dfi["typical_ticket_usd"]
    if min_t <= capex * 0.3 <= max_t:
        ticket_score = 1.0
    elif capex * 0.1 <= max_t:
        ticket_score = 0.7
    else:
        ticket_score = 0.4
    score += ticket_score * 0.2
    weights_total += 0.2

    # Country coverage (10% weight)
    coverage = len(countries) / max(len(countries), 1)
    score += coverage * 0.1
    weights_total += 0.1

    return round(score / weights_total, 2) if weights_total > 0 else 0.5


@tool("match_dfi_institutions", description=TOOL_DESCRIPTION)
def match_dfi_institutions_tool(
    payload: DFIMatchingInput, runtime: ToolRuntime
) -> Command:
    """Matches the project to potential DFI funders based on mandate and eligibility."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    # Get corridor info for real country list and CAPEX estimation
    try:
        corridor = pipeline_bridge.get_corridor_info()
        corridor_countries_iso = corridor.get("countries", [])
        total_km = corridor.get("length_km", 1080)
    except Exception as exc:
        logger.warning("Corridor info unavailable: %s", exc)
        corridor_countries_iso = []
        total_km = 1080

    # Use payload countries if corridor countries unavailable
    countries_input = payload.corridor_countries
    iso_countries = corridor_countries_iso or [
        COUNTRY_ISO.get(c.lower(), c[:3].upper()) for c in countries_input
    ]

    # Estimate project CAPEX from real infrastructure
    capex = total_km * 980_000 + len(iso_countries) * 50_000_000
    try:
        infra = pipeline_bridge.get_infrastructure_detections()
        n_substations = sum(
            1 for d in infra.get("detections", [])
            if d.get("type") in ("border_crossing", "industrial_zone")
        )
        capex += n_substations * 15_000_000  # substation cost per major node
    except Exception as exc:
        logger.warning("Infrastructure data unavailable: %s", exc)

    # Get WB indicators for country risk context
    wb_data = None
    try:
        wb_result = pipeline_bridge.get_worldbank_indicators()
        wb_data = wb_result.get("indicators")
    except Exception as exc:
        logger.warning("World Bank data unavailable: %s", exc)

    # Get DFI track record — which DFIs have actually funded projects in the corridor
    dfi_track_record = None
    try:
        dev_finance = pipeline_bridge.get_development_finance()
        if dev_finance.get("status") == "ok" and dev_finance.get("projects"):
            projects = dev_finance["projects"]
            # Group by funder/donor to show which DFIs are active
            funder_map: dict[str, list] = {}
            for proj in projects:
                funder = proj.get("funder") or proj.get("donor") or "Unknown"
                funder_map.setdefault(funder, []).append({
                    "title": proj.get("title", "Untitled"),
                    "country": proj.get("country", "Unknown"),
                    "sector": proj.get("sector", "Unknown"),
                    "investment_usd": proj.get("investment_usd") or proj.get("total_investment_usd"),
                })
            dfi_track_record = {
                "total_projects_in_corridor": dev_finance.get("project_count", len(projects)),
                "total_investment_usd": dev_finance.get("total_investment_usd"),
                "active_funders": [
                    {
                        "funder": funder,
                        "project_count": len(projs),
                        "sample_projects": projs[:3],
                    }
                    for funder, projs in sorted(funder_map.items(), key=lambda x: len(x[1]), reverse=True)[:10]
                ],
                "source": dev_finance.get("source", "AidData/development finance"),
            }
    except Exception as exc:
        logger.warning("Development finance data unavailable: %s", exc)

    # Get PPI/PPP track record for precedent analysis
    ppi_precedents = None
    try:
        ppi_data = pipeline_bridge.get_ppi_projects()
        if ppi_data.get("status") == "ok" and ppi_data.get("projects"):
            summary = ppi_data.get("summary", {})
            ppi_precedents = {
                "total_ppi_projects": ppi_data.get("project_count", len(ppi_data["projects"])),
                "total_investment_usd": summary.get("total_investment"),
                "by_sector": summary.get("by_sector", {}),
                "by_country": summary.get("by_country", {}),
                "by_status": summary.get("by_status", {}),
                "avg_contract_years": summary.get("avg_contract_years"),
                "sample_projects": [
                    {
                        "name": p.get("name") or p.get("title", "Untitled"),
                        "country": p.get("country", "Unknown"),
                        "sector": p.get("sector", "Unknown"),
                        "investment_usd": p.get("investment_usd") or p.get("total_investment_usd"),
                        "status": p.get("status", "Unknown"),
                    }
                    for p in ppi_data["projects"][:5]
                ],
                "source": ppi_data.get("source", "PPI Database"),
            }
    except Exception as exc:
        logger.warning("PPI projects data unavailable: %s", exc)

    # Score each DFI against project characteristics
    sectors = payload.sectors
    scored_dfis = []
    for dfi in DFI_DATABASE:
        relevance = _score_dfi(dfi, iso_countries, sectors, capex)
        scored_dfis.append({
            "name": dfi["name"],
            "abbreviation": dfi["abbreviation"],
            "focus": dfi["focus"],
            "relevance": relevance,
            "instrument_types": dfi["instrument_types"],
            "typical_ticket_size_usd": f"${dfi['typical_ticket_usd'][0] / 1e6:.0f}M–${dfi['typical_ticket_usd'][1] / 1e6:.0f}M",
            "concessional_rate_range": dfi["concessional_rate_range"],
            "tenor_range_years": dfi["tenor_range_years"],
            "grace_period_years": dfi["grace_period_years"],
            "avg_approval_timeline_months": dfi["avg_approval_months"],
            "esg_requirements": dfi["esg_requirements"],
        })

    # Sort by relevance
    scored_dfis.sort(key=lambda x: x["relevance"], reverse=True)

    # Build engagement sequence — concessional anchor first
    concessional_first = [d for d in scored_dfis if "Concessional Loan" in d["instrument_types"] or "Grant" in d["instrument_types"]]
    commercial_after = [d for d in scored_dfis if d not in concessional_first]

    engagement = []
    for i, dfi in enumerate(concessional_first[:3] + commercial_after[:2], 1):
        engagement.append({
            "step": i,
            "institution": dfi["abbreviation"],
            "relevance": dfi["relevance"],
            "rationale": f"{'Concessional anchor' if i <= 2 else 'Commercial tranche'} — {dfi['focus']}",
        })

    # Compute aggregate capacity estimates
    total_concessional = sum(
        d["typical_ticket_usd"][1] for d in DFI_DATABASE
        if "Concessional Loan" in d["instrument_types"] or "Grant" in d["instrument_types"]
    )
    total_commercial = sum(
        d["typical_ticket_usd"][1] for d in DFI_DATABASE
        if "Senior Loan" in d["instrument_types"] or "Direct Loan" in d["instrument_types"]
    )

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "analysis_type": "DFI Institution Matching",
        "project_parameters": {
            "countries": iso_countries,
            "sectors": sectors,
            "estimated_capex_usd": capex,
            "corridor_length_km": total_km,
        },
        "eligible_institutions": scored_dfis,
        "engagement_sequence": engagement,
        "summary": {
            "total_institutions_scanned": len(DFI_DATABASE),
            "eligible_count": len([d for d in scored_dfis if d["relevance"] >= 0.5]),
            "total_concessional_capacity_usd": total_concessional,
            "total_commercial_capacity_usd": total_commercial,
            "highest_relevance_institution": scored_dfis[0]["abbreviation"] if scored_dfis else "N/A",
            "fastest_approval_institution": min(scored_dfis, key=lambda x: x["avg_approval_timeline_months"])["abbreviation"] if scored_dfis else "N/A",
        },
        "wb_indicators": wb_data if wb_data else "World Bank data unavailable",
        "dfi_track_record": dfi_track_record if dfi_track_record else "Development finance track record unavailable",
        "ppi_precedents": ppi_precedents if ppi_precedents else "PPI/PPP precedent data unavailable",
        "data_sources": [
            "DFI mandate database",
            "Corridor AOI",
            "World Bank" if wb_data else "World Bank (unavailable)",
            "AidData/Development Finance" if dfi_track_record else "Development Finance (unavailable)",
            "PPI Database" if ppi_precedents else "PPI Database (unavailable)",
        ],
        "message": (
            f"DFI matching complete across {len(DFI_DATABASE)} institutions. "
            f"{len([d for d in scored_dfis if d['relevance'] >= 0.5])} eligible funders identified. "
            f"Top match: {scored_dfis[0]['abbreviation']} (relevance: {scored_dfis[0]['relevance']}) "
            f"for ${capex / 1e6:,.0f}M estimated CAPEX across {len(iso_countries)} countries. "
            f"Concessional capacity: ${total_concessional / 1e6:,.0f}M. "
            f"Commercial capacity: ${total_commercial / 1e6:,.0f}M."
            + (f" DFI track record: {dfi_track_record['total_projects_in_corridor']} past projects found in corridor." if dfi_track_record else "")
            + (f" PPI precedents: {ppi_precedents['total_ppi_projects']} past PPP/PFI projects." if ppi_precedents else "")
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
