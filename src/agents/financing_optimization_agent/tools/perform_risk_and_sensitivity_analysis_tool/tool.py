import copy
import json
import logging
import random

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import RiskAnalysisInput

logger = logging.getLogger("corridor.agent.financing.risk_analysis")

# Sensitivity variables with default ranges
DEFAULT_VARIABLES = [
    {
        "variable": "Anchor Load Revenue Realization",
        "base": 0.85, "low": 0.60, "high": 1.00,
        "irr_sensitivity": 0.033,  # IRR change per 10% variable change
        "dscr_sensitivity": 0.012,
        "label": "CRITICAL",
    },
    {
        "variable": "Construction CAPEX Overrun",
        "base": 0.0, "low": 0.25, "high": -0.05,
        "irr_sensitivity": -0.018,
        "dscr_sensitivity": -0.007,
        "label": "HIGH",
    },
    {
        "variable": "Currency Devaluation (Local vs USD)",
        "base": 0.025, "low": 0.08, "high": 0.0,
        "irr_sensitivity": -0.020,
        "dscr_sensitivity": -0.005,
        "label": "HIGH",
    },
    {
        "variable": "Construction Timeline Delay (months)",
        "base": 0, "low": 18, "high": -3,
        "irr_sensitivity": -0.015,
        "dscr_sensitivity": -0.005,
        "label": "HIGH",
    },
    {
        "variable": "Commercial Interest Rate (SOFR)",
        "base": 0.053, "low": 0.073, "high": 0.038,
        "irr_sensitivity": -0.010,
        "dscr_sensitivity": -0.003,
        "label": "MEDIUM",
    },
    {
        "variable": "Transmission Tariff Level",
        "base": 0.021, "low": 0.015, "high": 0.026,
        "irr_sensitivity": 0.019,
        "dscr_sensitivity": 0.005,
        "label": "MEDIUM",
    },
    {
        "variable": "OPEX Escalation Rate",
        "base": 0.025, "low": 0.05, "high": 0.015,
        "irr_sensitivity": -0.006,
        "dscr_sensitivity": -0.002,
        "label": "LOW",
    },
]

# Correlation pairs
CORRELATION_PAIRS = [
    ("Currency Devaluation (Local vs USD)", "Anchor Load Revenue Realization", 0.68,
     "Currency crises reduce industrial output and power demand simultaneously"),
    ("Construction Timeline Delay (months)", "Construction CAPEX Overrun", 0.72,
     "Delays almost always accompany cost overruns — same root causes"),
    ("Commercial Interest Rate (SOFR)", "Currency Devaluation (Local vs USD)", 0.55,
     "USD strengthening periods coincide with local currency weakness"),
]


@tool("perform_risk_and_sensitivity_analysis", description=TOOL_DESCRIPTION)
def perform_risk_and_sensitivity_analysis_tool(
    payload: RiskAnalysisInput, runtime: ToolRuntime
) -> Command:
    """Runs sensitivity and scenario analysis to determine risk profile."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    model_data = payload.financial_model_data or {}
    variances = payload.variable_variances or {}

    # Work on a copy to avoid mutating the module-level defaults
    sensitivity_variables = copy.deepcopy(DEFAULT_VARIABLES)

    # Extract base case from model data or use defaults
    base_irr = model_data.get("equity_irr", 0.151)
    if isinstance(base_irr, str):
        base_irr = float(base_irr.replace("%", "")) / 100
    base_dscr = model_data.get("min_dscr", 1.42)
    base_npv = model_data.get("npv_usd", 218_000_000)
    target_irr = 0.14
    dscr_covenant = 1.30

    # Get conflict data for political risk context
    conflict_context = None
    try:
        conflict = pipeline_bridge.get_conflict_data()
        conflict_context = {
            "total_events": conflict.get("total_events", 0),
            "risk_level": conflict.get("risk_level", "unknown"),
        }
    except Exception as exc:
        logger.warning("Conflict data unavailable: %s", exc)

    # Get WB indicators for macro risk context
    macro_context = None
    try:
        wb = pipeline_bridge.get_worldbank_indicators()
        macro_context = wb.get("indicators")
    except Exception as exc:
        logger.warning("World Bank data unavailable: %s", exc)

    # Get sovereign risk data — real CPI and governance scores
    sovereign_risk_context = None
    try:
        sov = pipeline_bridge.get_sovereign_risk()
        if sov.get("status") == "ok":
            cpi_scores = sov.get("cpi_scores", [])
            governance = sov.get("governance", {})
            sovereign_risk_context = {
                "cpi_scores": cpi_scores,
                "governance_indices": governance,
                "source": sov.get("source", "TI/V-Dem"),
            }
            # Adjust political risk sensitivity based on actual CPI scores
            # CPI range 0-100 (higher = cleaner); low CPI → higher political risk
            if cpi_scores:
                avg_cpi = sum(
                    s.get("score", 50) for s in cpi_scores
                ) / len(cpi_scores)
                # Scale: CPI < 30 = high risk, 30-50 = medium, > 50 = lower
                political_risk_factor = max(0.5, min(2.0, (60 - avg_cpi) / 30))
                # Adjust currency devaluation sensitivity by political risk
                for var in sensitivity_variables:
                    if "Currency Devaluation" in var["variable"]:
                        var["irr_sensitivity"] = round(var["irr_sensitivity"] * political_risk_factor, 4)
                        var["dscr_sensitivity"] = round(var["dscr_sensitivity"] * political_risk_factor, 4)
    except Exception as exc:
        logger.warning("Sovereign risk data unavailable: %s", exc)

    # Get IMF indicators for macro risk context (GDP growth, inflation, debt)
    imf_macro_context = None
    try:
        imf = pipeline_bridge.get_imf_indicators()
        if imf.get("status") == "ok":
            imf_macro_context = {
                "indicators": imf.get("indicators", {}),
                "source": imf.get("source", "IMF WEO"),
            }
    except Exception as exc:
        logger.warning("IMF indicators unavailable: %s", exc)

    # Tornado diagram — one-at-a-time sensitivity
    tornado = []
    for var in sensitivity_variables:
        # Apply variance overrides if provided
        var_key = var["variable"].lower().replace(" ", "_")[:10]
        variance = variances.get(var_key, abs(var["high"] - var["low"]) / 2)

        irr_swing = abs(var["irr_sensitivity"]) * 20  # full range swing
        irr_low = round(base_irr + var["irr_sensitivity"] * -10, 3)
        irr_high = round(base_irr + var["irr_sensitivity"] * 10, 3)

        dscr_low = round(base_dscr + var["dscr_sensitivity"] * -10, 2)

        tornado.append({
            "rank": len(tornado) + 1,
            "variable": var["variable"],
            "base_case": var["base"],
            "low_case": var["low"],
            "high_case": var["high"],
            "irr_low_case": f"{irr_low * 100:.1f}%",
            "irr_high_case": f"{irr_high * 100:.1f}%",
            "irr_swing": f"{abs(irr_high - irr_low) * 100:.1f}%",
            "dscr_impact_low": f"{dscr_low:.2f}x",
            "sensitivity_label": var["label"],
        })

    # Sort by IRR swing
    tornado.sort(key=lambda x: float(x["irr_swing"].replace("%", "")), reverse=True)
    for i, t in enumerate(tornado):
        t["rank"] = i + 1

    # Monte Carlo simulation (simplified — 1000 iterations with random sampling)
    n_iterations = 1000
    random.seed(42)  # reproducible
    irr_results = []
    dscr_results = []
    npv_results = []

    for _ in range(n_iterations):
        irr_shift = 0
        dscr_shift = 0
        for var in sensitivity_variables:
            shock = random.gauss(0, abs(var["irr_sensitivity"]) * 3)
            irr_shift += shock
            dscr_shift += random.gauss(0, abs(var["dscr_sensitivity"]) * 3)

        sim_irr = base_irr + irr_shift
        sim_dscr = base_dscr + dscr_shift
        sim_npv = base_npv * (1 + irr_shift * 5)

        irr_results.append(sim_irr)
        dscr_results.append(sim_dscr)
        npv_results.append(sim_npv)

    irr_results.sort()
    dscr_results.sort()
    npv_results.sort()

    p10_idx = int(n_iterations * 0.10)
    p50_idx = int(n_iterations * 0.50)
    p90_idx = int(n_iterations * 0.90)

    prob_above_target = sum(1 for r in irr_results if r >= target_irr) / n_iterations
    prob_dscr_breach = sum(1 for r in dscr_results if r < dscr_covenant) / n_iterations
    prob_npv_positive = sum(1 for r in npv_results if r > 0) / n_iterations

    # Break-even analysis
    break_evens = []
    for var in sensitivity_variables[:4]:  # top 4 critical variables
        headroom = abs(base_irr - target_irr) / max(abs(var["irr_sensitivity"]), 0.001)
        break_evens.append({
            "variable": var["variable"],
            "headroom_from_base": f"{headroom:.0f}% movement tolerated",
        })

    # Correlation risks
    corr_risks = []
    for var_a, var_b, corr, explanation in CORRELATION_PAIRS:
        sens_a = next((v for v in sensitivity_variables if v["variable"] == var_a), None)
        sens_b = next((v for v in sensitivity_variables if v["variable"] == var_b), None)
        combined_irr = base_irr
        if sens_a and sens_b:
            combined_irr = base_irr + (sens_a["irr_sensitivity"] + sens_b["irr_sensitivity"]) * -5
        corr_risks.append({
            "variable_a": var_a,
            "variable_b": var_b,
            "correlation": corr,
            "explanation": explanation,
            "combined_downside_irr": f"{combined_irr * 100:.1f}%",
            "risk_level": "HIGH" if corr >= 0.6 else "MEDIUM",
        })

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "analysis_type": "Risk & Sensitivity Analysis",
        "simulation_configuration": {
            "iterations": n_iterations,
            "variables_modelled": len(sensitivity_variables),
            "base_case_equity_irr": f"{base_irr * 100:.1f}%",
            "base_case_min_dscr": base_dscr,
            "base_case_npv_usd": base_npv,
            "target_equity_irr": f"{target_irr * 100:.1f}%",
            "covenant_floor_dscr": dscr_covenant,
        },
        "monte_carlo_results": {
            "equity_irr_distribution": {
                "prob_above_target": f"{prob_above_target * 100:.1f}%",
                "p10_irr": f"{irr_results[p90_idx] * 100:.1f}%",
                "p50_irr": f"{irr_results[p50_idx] * 100:.1f}%",
                "p90_irr": f"{irr_results[p10_idx] * 100:.1f}%",
                "mean_irr": f"{sum(irr_results) / n_iterations * 100:.1f}%",
            },
            "dscr_distribution": {
                "prob_covenant_breach": f"{prob_dscr_breach * 100:.1f}%",
                "p50_min_dscr": f"{dscr_results[p50_idx]:.2f}x",
                "p90_min_dscr": f"{dscr_results[p10_idx]:.2f}x",
            },
            "npv_distribution": {
                "prob_npv_positive": f"{prob_npv_positive * 100:.1f}%",
                "p50_npv_usd": round(npv_results[p50_idx]),
                "mean_npv_usd": round(sum(npv_results) / n_iterations),
            },
        },
        "tornado_diagram": {
            "metric_analysed": "Equity IRR",
            "base_case": f"{base_irr * 100:.1f}%",
            "variables": tornado,
        },
        "break_even_analysis": break_evens,
        "correlation_risks": corr_risks,
        "conflict_context": conflict_context if conflict_context else "Conflict data unavailable",
        "macro_context": macro_context if macro_context else "World Bank data unavailable",
        "sovereign_risk_context": sovereign_risk_context if sovereign_risk_context else "Sovereign risk data unavailable",
        "imf_macro_context": imf_macro_context if imf_macro_context else "IMF indicators unavailable",
        "data_sources": [
            "Financial model outputs",
            "ACLED" if conflict_context else "ACLED (unavailable)",
            "World Bank" if macro_context else "World Bank (unavailable)",
            "TI CPI / V-Dem Governance" if sovereign_risk_context else "Sovereign Risk (unavailable)",
            "IMF WEO" if imf_macro_context else "IMF (unavailable)",
        ],
        "message": (
            f"Risk analysis complete: {n_iterations} Monte Carlo iterations across {len(sensitivity_variables)} variables. "
            f"Probability of exceeding {target_irr * 100:.0f}% target IRR: {prob_above_target * 100:.1f}%. "
            f"P90 IRR: {irr_results[p10_idx] * 100:.1f}%. "
            f"DSCR covenant breach probability: {prob_dscr_breach * 100:.1f}%. "
            f"Top risk: {tornado[0]['variable']} (IRR swing: {tornado[0]['irr_swing']}). "
            f"{'Conflict risk context available. ' if conflict_context else ''}"
            f"{'Sovereign risk (CPI/governance) data injected into risk model. ' if sovereign_risk_context else ''}"
            f"{'IMF macro forecasts available.' if imf_macro_context else ''}"
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
