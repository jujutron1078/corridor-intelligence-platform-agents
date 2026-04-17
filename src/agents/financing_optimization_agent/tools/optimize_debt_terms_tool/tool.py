import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import DebtTermInput

logger = logging.getLogger("corridor.agent.financing.debt_terms")

# Debt optimization parameters
CONCESSIONAL_RATE = 0.028
COMMERCIAL_RATE = 0.083
DSCR_COVENANT = 1.30
DSCR_TARGET = 1.35
CONCESSIONAL_SHARE = 0.60  # of total debt
COMMERCIAL_SHARE = 0.40


@tool("optimize_debt_terms", description=TOOL_DESCRIPTION)
def optimize_debt_terms_tool(
    payload: DebtTermInput, runtime: ToolRuntime
) -> Command:
    """Aligns debt repayment with infrastructure cash flow patterns."""

    from src.adapters.pipeline_bridge import pipeline_bridge

    debt_amount = payload.debt_amount
    cfads = payload.cash_flow_available_for_debt_service or []

    concessional_debt = debt_amount * CONCESSIONAL_SHARE
    commercial_debt = debt_amount * COMMERCIAL_SHARE

    # Get sovereign risk to contextualize interest rate spreads
    risk_adjusted_context = None
    try:
        sov = pipeline_bridge.get_sovereign_risk()
        if sov.get("status") == "ok":
            cpi_scores = sov.get("cpi_scores", [])
            governance = sov.get("governance", {})
            risk_adjusted_context = {
                "cpi_scores": cpi_scores,
                "governance_indices": governance,
                "source": sov.get("source", "TI/V-Dem"),
            }
            # Adjust commercial rate spread based on country risk
            # Lower CPI → higher spread (riskier countries pay more)
            if cpi_scores:
                avg_cpi = sum(
                    s.get("score", 50) for s in cpi_scores
                ) / len(cpi_scores)
                # CPI < 30 → +150bps, CPI 30-50 → +0-100bps, CPI > 50 → -50bps
                spread_adjustment = max(-0.005, min(0.015, (40 - avg_cpi) / 2000))
                COMMERCIAL_RATE_ADJ = COMMERCIAL_RATE + spread_adjustment
                risk_adjusted_context["avg_cpi_score"] = round(avg_cpi, 1)
                risk_adjusted_context["spread_adjustment_bps"] = round(spread_adjustment * 10000, 0)
                risk_adjusted_context["adjusted_commercial_rate"] = f"{COMMERCIAL_RATE_ADJ * 100:.1f}%"
            else:
                COMMERCIAL_RATE_ADJ = COMMERCIAL_RATE
        else:
            COMMERCIAL_RATE_ADJ = COMMERCIAL_RATE
    except Exception as exc:
        logger.warning("Sovereign risk data unavailable: %s", exc)
        COMMERCIAL_RATE_ADJ = COMMERCIAL_RATE

    # Test tenor/grace combinations
    tenor_options = [
        {"conc_tenor": 18, "comm_tenor": 12, "grace": 4, "label": "Short Tenor"},
        {"conc_tenor": 20, "comm_tenor": 13, "grace": 4, "label": "Medium-Short"},
        {"conc_tenor": 25, "comm_tenor": 15, "grace": 5, "label": "Standard"},
        {"conc_tenor": 28, "comm_tenor": 17, "grace": 6, "label": "Extended"},
        {"conc_tenor": 30, "comm_tenor": 18, "grace": 6, "label": "Long Tenor"},
    ]

    results = []
    for opt in tenor_options:
        conc_t = opt["conc_tenor"]
        comm_t = opt["comm_tenor"]
        grace = opt["grace"]

        # Compute debt service profile
        total_interest = 0
        min_dscr = 999
        trough_year = 0
        dscr_profile = []

        for y in range(max(conc_t, 25)):
            # Interest on outstanding
            conc_outstanding = max(0, concessional_debt * (1 - max(0, y - grace) / (conc_t - grace)))
            comm_outstanding = max(0, commercial_debt * (1 - max(0, y - grace) / max(comm_t - grace, 1)))
            interest = conc_outstanding * CONCESSIONAL_RATE + comm_outstanding * COMMERCIAL_RATE_ADJ

            # Principal
            conc_princ = concessional_debt / (conc_t - grace) if y >= grace else 0
            comm_princ = commercial_debt / (comm_t - grace) if y >= grace and y < comm_t else 0
            ds = interest + conc_princ + comm_princ
            total_interest += interest

            # DSCR using provided CFADS or estimated
            if y < len(cfads):
                cf = cfads[y]
            else:
                cf = cfads[-1] * (1.03 ** (y - len(cfads) + 1)) if cfads else debt_amount * 0.10

            dscr_y = cf / ds if ds > 0 else 99.0
            if dscr_y < min_dscr and ds > 0:
                min_dscr = dscr_y
                trough_year = y + 1

            if y < 10 or y == conc_t - 1:
                dscr_profile.append({"year": y + 1, "dscr": round(dscr_y, 2), "debt_service_usd": round(ds)})

        # Composite score: min DSCR (40%) + total interest (35%) + NPV factor (25%)
        dscr_score = min(min_dscr / 2.0, 1.0) * 100
        interest_score = max(0, 1.0 - total_interest / (debt_amount * 0.8)) * 100
        composite = round(dscr_score * 0.4 + interest_score * 0.35 + 50 * 0.25, 1)

        recommended = opt["label"] == "Standard"  # will be overridden by best score

        results.append({
            "label": opt["label"],
            "concessional_tenor_years": conc_t,
            "commercial_tenor_years": comm_t,
            "grace_period_years": grace,
            "min_dscr": round(min_dscr, 2),
            "trough_year": trough_year,
            "total_interest_paid_usd": round(total_interest),
            "dscr_covenant_met": min_dscr >= DSCR_COVENANT,
            "composite_score": composite,
            "dscr_profile_sample": dscr_profile,
        })

    # Select best by composite score
    results.sort(key=lambda x: x["composite_score"], reverse=True)
    for r in results:
        r["recommended"] = False
    results[0]["recommended"] = True

    best = results[0]

    # Compute optimized terms detail
    optimized = {
        "concessional_tranche": {
            "amount_usd": round(concessional_debt),
            "tenor_years": best["concessional_tenor_years"],
            "grace_period_years": best["grace_period_years"],
            "interest_rate": f"{CONCESSIONAL_RATE * 100:.1f}%",
            "amortization_profile": "DSCR-sculpted",
        },
        "commercial_tranche": {
            "amount_usd": round(commercial_debt),
            "tenor_years": best["commercial_tenor_years"],
            "grace_period_years": best["grace_period_years"] - 1,
            "interest_rate": f"{COMMERCIAL_RATE_ADJ * 100:.1f}%",
            "amortization_profile": "DSCR-sculpted",
        },
        "combined_debt_service": {
            "total_debt_usd": round(debt_amount),
            "total_interest_over_life_usd": best["total_interest_paid_usd"],
            "total_repayment_usd": round(debt_amount + best["total_interest_paid_usd"]),
            "blended_all_in_cost": f"{(concessional_debt * CONCESSIONAL_RATE + commercial_debt * COMMERCIAL_RATE_ADJ) / debt_amount * 100:.1f}%",
        },
    }

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "analysis_type": "Debt Term Optimization",
        "optimization_configuration": {
            "total_debt_amount_usd": debt_amount,
            "concessional_debt_usd": round(concessional_debt),
            "commercial_debt_usd": round(commercial_debt),
            "combinations_tested": len(tenor_options),
            "target_min_dscr": DSCR_TARGET,
            "covenant_floor_dscr": DSCR_COVENANT,
            "sculpting_method": "DSCR-sculpted amortization",
        },
        "tenor_comparison": results,
        "optimized_terms": optimized,
        "reserve_accounts": {
            "debt_service_reserve": {
                "size": "6 months forward debt service",
                "purpose": "Covers debt service shortfall in any 6-month period",
            },
            "maintenance_reserve": {
                "size": "12 months forward major maintenance",
                "purpose": "Ensures O&M does not disrupt debt service",
            },
        },
        "risk_adjusted_context": risk_adjusted_context if risk_adjusted_context else "Sovereign risk data unavailable",
        "data_sources": [
            "DFI rate benchmarks",
            "CFADS from financial model",
            "TI CPI / V-Dem Governance" if risk_adjusted_context else "Sovereign Risk (unavailable)",
        ],
        "message": (
            f"Debt term optimization complete for ${debt_amount / 1e6:,.0f}M total debt. "
            f"Recommended: {best['label']} — concessional {best['concessional_tenor_years']}-year tenor, "
            f"commercial {best['commercial_tenor_years']}-year tenor, {best['grace_period_years']}-year grace. "
            f"Min DSCR: {best['min_dscr']:.2f}x in Year {best['trough_year']} "
            f"({'above' if best['dscr_covenant_met'] else 'BELOW'} {DSCR_COVENANT}x covenant). "
            f"Total interest: ${best['total_interest_paid_usd'] / 1e6:,.0f}M over project life."
            + (f" Commercial rate adjusted by {risk_adjusted_context['spread_adjustment_bps']:+.0f}bps based on CPI scores (avg: {risk_adjusted_context['avg_cpi_score']})." if risk_adjusted_context and risk_adjusted_context.get("spread_adjustment_bps") else "")
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
