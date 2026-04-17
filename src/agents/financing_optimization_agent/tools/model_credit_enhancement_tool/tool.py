import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import CreditEnhancementInput

logger = logging.getLogger("corridor.agent.financing.credit_enhancement")

# Credit enhancement instrument knowledge base
ENHANCEMENT_INSTRUMENTS = [
    {
        "instrument": "MIGA Political Risk Insurance (PRI)",
        "provider": "MIGA (World Bank Group)",
        "coverage_type": "Political risk — expropriation, currency transfer, breach of contract",
        "premium_bps": 75,
        "spread_reduction_bps": 145,
        "max_coverage_pct": 1.0,  # 100% of commercial debt
        "gap_components": ["political_risk", "currency_risk"],
        "gap_share": 0.57,
        "procurement_months": 6,
    },
    {
        "instrument": "World Bank Partial Risk Guarantee (PRG)",
        "provider": "World Bank IBRD/IDA",
        "coverage_type": "Government obligation risk — tariff payments, concession terms",
        "premium_bps": 50,
        "spread_reduction_bps": 110,
        "max_coverage_pct": 0.60,
        "gap_components": ["revenue_risk"],
        "gap_share": 0.24,
        "procurement_months": 9,
    },
    {
        "instrument": "GuarantCo Partial Credit Guarantee (PCG)",
        "provider": "GuarantCo (PIDG)",
        "coverage_type": "Credit risk — first-loss portion of commercial debt",
        "premium_bps": 95,
        "spread_reduction_bps": 80,
        "max_coverage_pct": 0.30,
        "gap_components": ["construction_risk", "credit_risk"],
        "gap_share": 0.19,
        "procurement_months": 5,
    },
    {
        "instrument": "USAID Development Credit Authority (DCA)",
        "provider": "USAID DCA",
        "coverage_type": "Partial credit guarantee for U.S.-linked lenders",
        "premium_bps": 40,
        "spread_reduction_bps": 60,
        "max_coverage_pct": 0.20,
        "gap_components": ["credit_risk"],
        "gap_share": 0.10,
        "procurement_months": 4,
    },
    {
        "instrument": "AfDB Partial Risk Guarantee",
        "provider": "African Development Bank",
        "coverage_type": "Government obligation risk for non-sovereign operations",
        "premium_bps": 65,
        "spread_reduction_bps": 90,
        "max_coverage_pct": 0.40,
        "gap_components": ["political_risk"],
        "gap_share": 0.20,
        "procurement_months": 7,
    },
]

LENDER_COMFORT_THRESHOLD = 0.05  # 5% breach probability
PRE_ENHANCEMENT_BREACH_PROB = 0.068  # baseline without enhancement


@tool("model_credit_enhancement", description=TOOL_DESCRIPTION)
def model_credit_enhancement_tool(
    payload: CreditEnhancementInput, runtime: ToolRuntime
) -> Command:
    """Models the impact of risk mitigation instruments on the final WACC."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    gap = payload.gap_in_bankability

    # Get corridor info for commercial debt estimation
    try:
        corridor = pipeline_bridge.get_corridor_info()
        total_km = corridor.get("length_km", 1080)
        countries = corridor.get("countries", [])
        total_capex = total_km * 980_000 + len(countries) * 50_000_000
    except Exception as exc:
        logger.warning("Corridor info unavailable: %s", exc)
        total_capex = 900_000_000

    commercial_debt = total_capex * 0.30  # 30% commercial tranche
    base_wacc = 0.0566  # pre-enhancement WACC

    # Get sovereign risk for real country risk assessment
    country_risk_profile = None
    adjusted_breach_prob = PRE_ENHANCEMENT_BREACH_PROB
    try:
        sov = pipeline_bridge.get_sovereign_risk()
        if sov.get("status") == "ok":
            cpi_scores = sov.get("cpi_scores", [])
            governance = sov.get("governance", {})
            country_risk_profile = {
                "cpi_scores": cpi_scores,
                "governance_indices": governance,
                "source": sov.get("source", "TI/V-Dem"),
            }
            # Adjust breach probability based on actual CPI/governance
            # CPI 0-100 (higher = cleaner): low CPI means higher breach risk
            if cpi_scores:
                avg_cpi = sum(
                    s.get("score", 50) for s in cpi_scores
                ) / len(cpi_scores)
                # CPI < 30 → increase breach prob, CPI > 50 → decrease
                cpi_adjustment = (40 - avg_cpi) / 500  # ±0.02 range
                adjusted_breach_prob = max(0.02, min(0.15, PRE_ENHANCEMENT_BREACH_PROB + cpi_adjustment))
                country_risk_profile["avg_cpi_score"] = round(avg_cpi, 1)
                country_risk_profile["breach_prob_adjustment"] = round(cpi_adjustment, 4)
    except Exception as exc:
        logger.warning("Sovereign risk data unavailable: %s", exc)

    # Evaluate each instrument
    evaluated = []
    for instr in ENHANCEMENT_INSTRUMENTS:
        coverage = min(gap * instr["max_coverage_pct"] / 0.30, commercial_debt * instr["max_coverage_pct"])
        coverage = min(coverage, gap)  # can't exceed gap

        annual_premium = coverage * instr["premium_bps"] / 10000
        annual_saving = commercial_debt * instr["spread_reduction_bps"] / 10000
        net_benefit = annual_saving - annual_premium
        cost_benefit = round(annual_saving / annual_premium, 2) if annual_premium > 0 else 0

        evaluated.append({
            "instrument": instr["instrument"],
            "provider": instr["provider"],
            "coverage_type": instr["coverage_type"],
            "coverage_amount_usd": round(coverage),
            "annual_premium_bps": instr["premium_bps"],
            "annual_premium_usd": round(annual_premium),
            "spread_reduction_bps": instr["spread_reduction_bps"],
            "annual_interest_saving_usd": round(annual_saving),
            "net_annual_benefit_usd": round(net_benefit),
            "cost_benefit_ratio": f"{cost_benefit}x",
            "gap_share_addressed": f"{instr['gap_share'] * 100:.0f}%",
            "procurement_months": instr["procurement_months"],
            "recommended": net_benefit > 0 and instr["gap_share"] >= 0.15,
        })

    # Select recommended instruments (positive net benefit, significant gap coverage)
    selected = [e for e in evaluated if e["recommended"]]
    selected.sort(key=lambda x: x["net_annual_benefit_usd"], reverse=True)
    selected = selected[:3]  # top 3

    # Compute package economics
    total_premium = sum(s["annual_premium_usd"] for s in selected)
    total_saving = sum(s["annual_interest_saving_usd"] for s in selected)
    total_coverage = sum(s["coverage_amount_usd"] for s in selected)
    net_package_benefit = total_saving - total_premium

    # WACC impact
    premium_wacc_add = total_premium / total_capex
    saving_wacc_reduce = total_saving / total_capex
    net_wacc_change = premium_wacc_add - saving_wacc_reduce
    final_wacc = base_wacc + net_wacc_change

    # Breach probability reduction (using risk-adjusted baseline if sovereign data available)
    coverage_ratio = min(total_coverage / max(gap, 1), 2.0)
    breach_reduction = min(coverage_ratio * 0.02, adjusted_breach_prob - 0.02)
    final_breach_prob = adjusted_breach_prob - breach_reduction
    gap_closed = final_breach_prob <= LENDER_COMFORT_THRESHOLD

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "analysis_type": "Credit Enhancement Modeling",
        "bankability_gap_analysis": {
            "gap_amount_usd": gap,
            "commercial_debt_usd": round(commercial_debt),
            "pre_enhancement_breach_probability": f"{adjusted_breach_prob * 100:.1f}%",
            "baseline_breach_probability": f"{PRE_ENHANCEMENT_BREACH_PROB * 100:.1f}%",
            "risk_adjusted": country_risk_profile is not None,
            "lender_comfort_threshold": f"{LENDER_COMFORT_THRESHOLD * 100:.1f}%",
        },
        "instruments_evaluated": evaluated,
        "enhancement_plan": {
            "instruments_selected": [
                {
                    "instrument": s["instrument"],
                    "provider": s["provider"],
                    "coverage_usd": s["coverage_amount_usd"],
                    "annual_premium_usd": s["annual_premium_usd"],
                    "spread_reduction_bps": s["spread_reduction_bps"],
                }
                for s in selected
            ],
            "package_economics": {
                "total_coverage_usd": round(total_coverage),
                "total_annual_premium_usd": round(total_premium),
                "total_annual_saving_usd": round(total_saving),
                "net_annual_benefit_usd": round(net_package_benefit),
            },
            "wacc_impact": {
                "wacc_before": f"{base_wacc * 100:.2f}%",
                "premium_cost_addition": f"+{premium_wacc_add * 100:.2f}%",
                "spread_compression": f"-{saving_wacc_reduce * 100:.2f}%",
                "final_wacc": f"{final_wacc * 100:.2f}%",
                "net_wacc_change": f"{net_wacc_change * 100:.2f}%",
            },
            "risk_closure": {
                "breach_probability_before": f"{adjusted_breach_prob * 100:.1f}%",
                "breach_probability_after": f"{final_breach_prob * 100:.1f}%",
                "gap_fully_closed": gap_closed,
            },
        },
        "country_risk_profile": country_risk_profile if country_risk_profile else "Sovereign risk data unavailable",
        "data_sources": [
            "DFI guarantee pricing database",
            "Corridor AOI",
            "TI CPI / V-Dem Governance" if country_risk_profile else "Sovereign Risk (unavailable)",
        ],
        "message": (
            f"Credit enhancement modeled for ${gap / 1e6:,.0f}M bankability gap. "
            f"{len(evaluated)} instruments evaluated, {len(selected)} selected. "
            f"Total coverage: ${total_coverage / 1e6:,.0f}M. "
            f"Annual premium: ${total_premium / 1e6:,.1f}M vs saving: ${total_saving / 1e6:,.1f}M "
            f"(net benefit: ${net_package_benefit / 1e6:,.1f}M/year). "
            f"WACC: {base_wacc * 100:.2f}% → {final_wacc * 100:.2f}% (net {net_wacc_change * 100:+.2f}%). "
            f"Breach probability: {adjusted_breach_prob * 100:.1f}% → {final_breach_prob * 100:.1f}% "
            f"({'GAP CLOSED' if gap_closed else 'GAP REMAINS'})."
            + (f" Country risk profile based on real CPI (avg: {country_risk_profile['avg_cpi_score']}) and governance indices." if country_risk_profile and country_risk_profile.get("avg_cpi_score") else "")
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
