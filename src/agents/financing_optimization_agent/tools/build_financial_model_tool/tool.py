import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import FinancialModelInput

logger = logging.getLogger("corridor.agent.financing.financial_model")

# Financial model parameters
PROJECTION_YEARS = 25
CONSTRUCTION_YEARS = 4
DEPRECIATION_YEARS = 25
TAX_RATE = 0.25
INFLATION = 0.025
REVENUE_ESCALATION = 0.03
OPEX_ESCALATION = 0.025
OPEX_RATIO = 0.026  # 2.6% of CAPEX annually
DSCR_COVENANT = 1.30

# Revenue benchmarks per MW of connected demand
REVENUE_PER_MW_YEAR1 = 145_000  # USD/MW/year (wheeling + capacity charges)


@tool("build_financial_model", description=TOOL_DESCRIPTION)
def build_financial_model_tool(
    payload: FinancialModelInput, runtime: ToolRuntime
) -> Command:
    """Calculates core financial metrics for the project lifecycle."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    # Extract financing structure
    fin = payload.financing_structure or {}
    capex_data = payload.capex_opex_data or {}
    rev_projections = payload.revenue_projections or []

    # Get real CAPEX from infrastructure or payload
    total_capex = capex_data.get("total_capex_usd", 0)
    if total_capex <= 0:
        try:
            corridor = pipeline_bridge.get_corridor_info()
            total_km = corridor.get("length_km", 1080)
            countries = corridor.get("countries", [])
            total_capex = total_km * 980_000 + len(countries) * 50_000_000
        except Exception as exc:
            logger.warning("Corridor info unavailable: %s", exc)
            total_capex = 900_000_000

    # Get connected demand for revenue estimation
    total_demand_mw = 0
    try:
        infra = pipeline_bridge.get_infrastructure_detections()
        type_mw = {
            "port_facility": 20.0, "airport": 15.0, "industrial_zone": 30.0,
            "mineral_site": 25.0, "rail_network": 5.0, "border_crossing": 2.0,
        }
        for det in infra.get("detections", []):
            dt = det.get("type", "other")
            if dt != "power_plant":
                total_demand_mw += type_mw.get(dt, 5.0)
    except Exception as exc:
        logger.warning("Infrastructure data unavailable: %s", exc)
        total_demand_mw = 500

    # Get IMF indicators for real GDP growth and macro assumptions
    macro_assumptions = None
    rev_escalation = REVENUE_ESCALATION  # local copy; may be overridden by IMF data
    try:
        imf = pipeline_bridge.get_imf_indicators()
        if imf.get("status") == "ok" and imf.get("indicators"):
            imf_indicators = imf["indicators"]
            macro_assumptions = {
                "indicators": imf_indicators,
                "source": imf.get("source", "IMF WEO"),
            }
            # Use real GDP growth forecast for revenue escalation if available
            # Look for an average GDP growth across corridor countries
            gdp_growths = []
            if isinstance(imf_indicators, dict):
                for country_key, country_data in imf_indicators.items():
                    if isinstance(country_data, dict):
                        gdp_g = country_data.get("gdp_growth") or country_data.get("real_gdp_growth")
                        if gdp_g is not None:
                            try:
                                gdp_growths.append(float(gdp_g) / 100 if float(gdp_g) > 1 else float(gdp_g))
                            except (ValueError, TypeError):
                                pass
            if gdp_growths:
                avg_gdp_growth = sum(gdp_growths) / len(gdp_growths)
                # Use GDP growth as a proxy for revenue escalation (capped between 1-6%)
                rev_escalation = max(0.01, min(0.06, avg_gdp_growth))
                macro_assumptions["applied_revenue_escalation"] = round(rev_escalation, 4)
    except Exception as exc:
        logger.warning("IMF indicators unavailable: %s", exc)

    # Get planned energy projects for generation pipeline context
    energy_pipeline_context = None
    try:
        energy = pipeline_bridge.get_planned_energy_projects()
        if energy.get("status") == "ok" and energy.get("projects"):
            energy_pipeline_context = {
                "project_count": len(energy["projects"]),
                "capacity_summary": energy.get("capacity_summary", {}),
                "sample_projects": [
                    {
                        "name": p.get("name") or p.get("title", "Untitled"),
                        "country": p.get("country", "Unknown"),
                        "capacity_mw": p.get("capacity_mw"),
                        "fuel_type": p.get("fuel_type") or p.get("technology", "Unknown"),
                        "status": p.get("status", "Unknown"),
                    }
                    for p in energy["projects"][:5]
                ],
                "source": energy.get("source", "Energy project database"),
            }
    except Exception as exc:
        logger.warning("Planned energy projects unavailable: %s", exc)

    # Build revenue trajectory if not provided
    if not rev_projections or len(rev_projections) < PROJECTION_YEARS:
        base_revenue = total_demand_mw * REVENUE_PER_MW_YEAR1
        # Ramp-up: 40% Y1, 60% Y2, 80% Y3, 95% Y4, 100% Y5+
        ramp = [0.40, 0.60, 0.80, 0.95] + [1.0] * (PROJECTION_YEARS - 4)
        rev_projections = [
            base_revenue * ramp[y] * (1 + rev_escalation) ** y
            for y in range(PROJECTION_YEARS)
        ]

    # OPEX trajectory
    base_opex = total_capex * OPEX_RATIO
    opex_projections = [base_opex * (1 + OPEX_ESCALATION) ** y for y in range(PROJECTION_YEARS)]

    # EBITDA
    ebitda = [rev_projections[y] - opex_projections[y] for y in range(PROJECTION_YEARS)]

    # Depreciation (straight-line)
    annual_depreciation = total_capex / DEPRECIATION_YEARS

    # Extract financing parameters
    wacc = fin.get("wacc_raw", fin.get("wacc", 0.057))
    if isinstance(wacc, str):
        wacc = float(wacc.replace("%", "")) / 100

    grants_usd = fin.get("grants_usd", total_capex * 0.10)
    concessional_usd = fin.get("concessional_usd", total_capex * 0.45)
    commercial_usd = fin.get("commercial_usd", total_capex * 0.30)
    equity_usd = fin.get("equity_usd", total_capex * 0.15)
    total_debt = concessional_usd + commercial_usd

    # Estimate annual debt service (simplified sculpted profile)
    conc_rate = 0.028
    comm_rate = 0.083
    conc_tenor = 25
    comm_tenor = 15
    grace = 5

    # Cash flow waterfall for key years
    waterfall = []
    min_dscr = 999
    min_dscr_year = 0
    cfads_list = []
    cumulative_equity_cf = [-equity_usd]  # initial equity outflow

    for y in range(PROJECTION_YEARS):
        rev = rev_projections[y]
        opex = opex_projections[y]
        ebitda_y = ebitda[y]
        dep = annual_depreciation
        ebit = ebitda_y - dep

        # Interest
        conc_outstanding = max(0, concessional_usd * (1 - max(0, y - grace) / conc_tenor))
        comm_outstanding = max(0, commercial_usd * (1 - max(0, y - grace + 1) / comm_tenor))
        interest = conc_outstanding * conc_rate + comm_outstanding * comm_rate

        # Principal (after grace)
        conc_principal = concessional_usd / conc_tenor if y >= grace else 0
        comm_principal = commercial_usd / comm_tenor if y >= grace - 1 and y < grace - 1 + comm_tenor else 0
        debt_service = interest + conc_principal + comm_principal

        # CFADS
        cfads_y = ebitda_y
        cfads_list.append(cfads_y)

        # DSCR
        dscr_y = cfads_y / debt_service if debt_service > 0 else 99.0
        if dscr_y < min_dscr:
            min_dscr = dscr_y
            min_dscr_year = y + 1

        # Tax
        ebt = ebit - interest
        tax = max(0, ebt * TAX_RATE)
        net_income = ebt - tax

        # Equity distribution
        equity_dist = max(0, cfads_y - debt_service - tax)
        cumulative_equity_cf.append(equity_dist)

        # Record key years
        if y in [0, 2, 4, 9, 14, 24]:
            waterfall.append({
                "year": y + 1,
                "revenue_usd": round(rev),
                "opex_usd": round(opex),
                "ebitda_usd": round(ebitda_y),
                "ebitda_margin": f"{ebitda_y / rev * 100:.1f}%" if rev > 0 else "0%",
                "debt_service_usd": round(debt_service),
                "dscr": round(dscr_y, 2),
                "tax_usd": round(tax),
                "equity_distribution_usd": round(equity_dist),
            })

    # Compute NPV
    npv = sum(ebitda[y] / (1 + wacc) ** (y + 1) for y in range(PROJECTION_YEARS)) - total_capex

    # Estimate equity IRR (simplified)
    equity_irr = _estimate_equity_irr(cumulative_equity_cf)

    # Project IRR
    project_cf = [-total_capex / CONSTRUCTION_YEARS] * CONSTRUCTION_YEARS + list(ebitda)
    project_irr = _estimate_irr(project_cf)

    # Payback period
    cumulative = 0
    payback = PROJECTION_YEARS
    for y, cf in enumerate(ebitda):
        cumulative += cf
        if cumulative >= total_capex:
            payback = y + 1
            break

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "analysis_type": "Financial Model — Project Finance DCF",
        "model_configuration": {
            "projection_period_years": PROJECTION_YEARS,
            "construction_period_years": CONSTRUCTION_YEARS,
            "discount_rate_wacc": f"{wacc * 100:.2f}%",
            "total_capex_usd": total_capex,
            "connected_demand_mw": round(total_demand_mw, 1),
            "tax_rate": f"{TAX_RATE * 100:.0f}%",
        },
        "metrics": {
            "equity_irr": f"{equity_irr * 100:.1f}%",
            "project_irr": f"{project_irr * 100:.1f}%",
            "net_present_value_usd": round(npv),
            "min_dscr": round(min_dscr, 2),
            "min_dscr_year": min_dscr_year,
            "payback_period_years": payback,
            "total_debt_usd": round(total_debt),
            "npv_positive": npv > 0,
            "dscr_covenant_met": min_dscr >= DSCR_COVENANT,
        },
        "revenue_summary": {
            "year_1_usd": round(rev_projections[0]),
            "year_5_usd": round(rev_projections[4]) if len(rev_projections) > 4 else 0,
            "year_10_usd": round(rev_projections[9]) if len(rev_projections) > 9 else 0,
            "year_25_usd": round(rev_projections[-1]),
        },
        "cash_flow_waterfall": waterfall,
        "cfads_profile": [round(c) for c in cfads_list[:10]],
        "macro_assumptions": macro_assumptions if macro_assumptions else "IMF macro data unavailable",
        "energy_pipeline_context": energy_pipeline_context if energy_pipeline_context else "Planned energy project data unavailable",
        "data_sources": [
            "Corridor AOI",
            "OSM + USGS infrastructure",
            "DFI rate benchmarks",
            "IMF WEO" if macro_assumptions else "IMF (unavailable)",
            "Energy project database" if energy_pipeline_context else "Energy projects (unavailable)",
        ],
        "message": (
            f"Financial model complete for ${total_capex / 1e6:,.0f}M CAPEX, "
            f"{total_demand_mw:,.0f} MW connected demand. "
            f"Equity IRR: {equity_irr * 100:.1f}%, Project IRR: {project_irr * 100:.1f}%, "
            f"NPV: ${npv / 1e6:,.0f}M {'(positive)' if npv > 0 else '(negative)'}. "
            f"Min DSCR: {min_dscr:.2f}x in Year {min_dscr_year} "
            f"({'above' if min_dscr >= DSCR_COVENANT else 'BELOW'} {DSCR_COVENANT}x covenant). "
            f"Payback: {payback} years."
            + (f" Revenue escalation calibrated from IMF GDP growth forecasts ({macro_assumptions['applied_revenue_escalation']*100:.1f}%)." if macro_assumptions and macro_assumptions.get("applied_revenue_escalation") else "")
            + (f" {energy_pipeline_context['project_count']} planned energy projects in corridor pipeline." if energy_pipeline_context else "")
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})


def _estimate_equity_irr(cash_flows: list[float]) -> float:
    """Newton-Raphson IRR estimate for equity cash flows."""
    if not cash_flows or all(cf == 0 for cf in cash_flows):
        return 0.0
    rate = 0.12
    for _ in range(100):
        npv = sum(cf / (1 + rate) ** t for t, cf in enumerate(cash_flows))
        dnpv = sum(-t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cash_flows))
        if abs(dnpv) < 1e-10:
            break
        rate -= npv / dnpv
        rate = max(min(rate, 1.0), -0.5)
    return round(rate, 3)


def _estimate_irr(cash_flows: list[float]) -> float:
    """Newton-Raphson IRR estimate."""
    if not cash_flows or all(cf == 0 for cf in cash_flows):
        return 0.0
    rate = 0.10
    for _ in range(100):
        npv = sum(cf / (1 + rate) ** t for t, cf in enumerate(cash_flows))
        dnpv = sum(-t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cash_flows))
        if abs(dnpv) < 1e-10:
            break
        rate -= npv / dnpv
        rate = max(min(rate, 1.0), -0.5)
    return round(rate, 3)
