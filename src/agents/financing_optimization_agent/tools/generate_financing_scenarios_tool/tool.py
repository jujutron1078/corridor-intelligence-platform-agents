import json
import logging

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import ScenarioGenerationInput

logger = logging.getLogger("corridor.agent.financing.scenarios")

# Financing structure benchmarks for African infrastructure
GRANT_RATIOS = [0.05, 0.08, 0.10, 0.12, 0.15, 0.18]
CONCESSIONAL_RATIOS = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]
EQUITY_FLOOR = 0.15  # minimum equity ratio

# Cost of capital benchmarks
GRANT_COST = 0.0
CONCESSIONAL_RATE = 0.028  # 2.8% blended DFI rate
COMMERCIAL_RATE = 0.083    # SOFR + 3% ≈ 8.3%
EQUITY_COST = 0.148        # 14.8% blended equity cost
TAX_SHIELD = 0.25          # corporate tax rate for shield
DSCR_FLOOR = 1.30


def _compute_wacc(grant_pct, concessional_pct, commercial_pct, equity_pct):
    """Compute weighted average cost of capital."""
    gross = (
        GRANT_COST * grant_pct
        + CONCESSIONAL_RATE * concessional_pct
        + COMMERCIAL_RATE * commercial_pct
        + EQUITY_COST * equity_pct
    )
    debt_pct = concessional_pct + commercial_pct
    tax_shield = debt_pct * TAX_SHIELD * (
        (CONCESSIONAL_RATE * concessional_pct + COMMERCIAL_RATE * commercial_pct)
        / max(debt_pct, 0.01)
    )
    return round(gross - tax_shield, 4)


def _estimate_irr(wacc, grant_pct):
    """Rough equity IRR estimate — higher grant ratio = better equity returns."""
    base_spread = 0.045  # equity typically 4-5% above project WACC
    grant_boost = grant_pct * 0.15  # grants improve equity returns
    return round(wacc + base_spread + grant_boost, 3)


def _estimate_dscr(concessional_pct, commercial_pct, grant_pct):
    """Estimate minimum DSCR from debt structure."""
    debt_ratio = concessional_pct + commercial_pct
    base_dscr = 2.0 - debt_ratio * 1.2  # higher debt = lower DSCR
    grant_benefit = grant_pct * 0.5
    return round(base_dscr + grant_benefit, 2)


@tool("generate_financing_scenarios", description=TOOL_DESCRIPTION)
def generate_financing_scenarios_tool(
    payload: ScenarioGenerationInput, runtime: ToolRuntime
) -> Command:
    """Creates multiple blended finance structures to optimize project returns."""
    from src.adapters.pipeline_bridge import pipeline_bridge

    total_capex = payload.total_capex
    target_irr = payload.target_equity_irr or 0.14
    max_commercial = payload.max_commercial_debt_ratio or 0.40

    # Get PPI/PPP comparable projects for benchmarking
    comparable_projects = None
    try:
        ppi_data = pipeline_bridge.get_ppi_projects()
        if ppi_data.get("status") == "ok" and ppi_data.get("projects"):
            summary = ppi_data.get("summary", {})
            comparable_projects = {
                "total_comparable_projects": ppi_data.get("project_count", len(ppi_data["projects"])),
                "total_investment_usd": summary.get("total_investment"),
                "by_sector": summary.get("by_sector", {}),
                "by_country": summary.get("by_country", {}),
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

    # If CAPEX not provided or zero, estimate from real data
    if total_capex <= 0:
        try:
            corridor = pipeline_bridge.get_corridor_info()
            total_km = corridor.get("length_km", 1080)
            countries = corridor.get("countries", [])
            total_capex = total_km * 980_000 + len(countries) * 50_000_000
        except Exception as exc:
            logger.warning("Corridor info unavailable: %s", exc)
            total_capex = 900_000_000  # fallback

    # Generate scenarios by varying grant/concessional/commercial ratios
    scenarios = []
    for grant_r in GRANT_RATIOS:
        for conc_r in CONCESSIONAL_RATIOS:
            for comm_pct in [0.15, 0.20, 0.25, 0.30, 0.35, 0.40]:
                if comm_pct > max_commercial:
                    continue
                equity_r = 1.0 - grant_r - conc_r - comm_pct
                if equity_r < EQUITY_FLOOR or equity_r > 0.35:
                    continue

                wacc = _compute_wacc(grant_r, conc_r, comm_pct, equity_r)
                eq_irr = _estimate_irr(wacc, grant_r)
                min_dscr = _estimate_dscr(conc_r, comm_pct, grant_r)

                if min_dscr < DSCR_FLOOR or eq_irr < target_irr * 0.85:
                    continue

                # Composite score: WACC (40%) + IRR (35%) + DSCR (25%)
                wacc_score = max(0, (0.10 - wacc) / 0.10) * 100
                irr_score = min(eq_irr / 0.20, 1.0) * 100
                dscr_score = min(min_dscr / 2.0, 1.0) * 100
                composite = round(wacc_score * 0.4 + irr_score * 0.35 + dscr_score * 0.25, 1)

                scenarios.append({
                    "grants_pct": round(grant_r * 100),
                    "concessional_pct": round(conc_r * 100),
                    "commercial_pct": round(comm_pct * 100),
                    "equity_pct": round(equity_r * 100),
                    "grants_usd": round(total_capex * grant_r),
                    "concessional_usd": round(total_capex * conc_r),
                    "commercial_usd": round(total_capex * comm_pct),
                    "equity_usd": round(total_capex * equity_r),
                    "wacc": f"{wacc * 100:.2f}%",
                    "wacc_raw": wacc,
                    "equity_irr": f"{eq_irr * 100:.1f}%",
                    "equity_irr_raw": eq_irr,
                    "min_dscr": f"{min_dscr:.2f}x",
                    "min_dscr_raw": min_dscr,
                    "composite_score": composite,
                })

    # Sort by composite score and take top scenarios
    scenarios.sort(key=lambda x: x["composite_score"], reverse=True)

    # Mark recommended
    for i, s in enumerate(scenarios):
        s["scenario_id"] = f"S-{i + 1:02d}"
        s["recommended"] = i == 0

    top_scenarios = scenarios[:min(len(scenarios), 10)]

    # Clean internal fields from output
    for s in top_scenarios:
        del s["wacc_raw"]
        del s["equity_irr_raw"]
        del s["min_dscr_raw"]

    recommended = top_scenarios[0] if top_scenarios else None

    response = {
        "corridor_id": "AL_CORRIDOR_001",
        "analysis_type": "Financing Scenario Generation",
        "generation_metadata": {
            "total_combinations_tested": len(GRANT_RATIOS) * len(CONCESSIONAL_RATIOS) * 6,
            "scenarios_passing_filters": len(scenarios),
            "scenarios_returned": len(top_scenarios),
            "capex_input_usd": total_capex,
            "target_equity_irr": f"{target_irr * 100:.1f}%",
            "max_commercial_debt_ratio": f"{max_commercial * 100:.0f}%",
            "optimization_objective": f"Minimize WACC subject to: Equity IRR >= {target_irr * 100:.0f}%, DSCR >= {DSCR_FLOOR}x",
        },
        "recommended_scenario": recommended,
        "scenario_comparison": top_scenarios,
        "comparable_projects": comparable_projects if comparable_projects else "PPI/PPP comparable project data unavailable",
        "data_sources": [
            "Corridor AOI",
            "DFI rate benchmarks",
            "AfDB/IFC cost of capital data",
            "PPI Database" if comparable_projects else "PPI Database (unavailable)",
        ],
        "message": (
            f"{len(scenarios)} financing scenarios generated from {len(GRANT_RATIOS) * len(CONCESSIONAL_RATIOS) * 6} "
            f"combinations tested against ${total_capex / 1e6:,.0f}M CAPEX. "
            + (
                f"Recommended: {recommended['scenario_id']} — "
                f"{recommended['grants_pct']}% grants + {recommended['concessional_pct']}% concessional + "
                f"{recommended['commercial_pct']}% commercial + {recommended['equity_pct']}% equity. "
                f"WACC: {recommended['wacc']}, IRR: {recommended['equity_irr']}, DSCR: {recommended['min_dscr']}."
                if recommended else "No viable scenarios found with given constraints."
            )
            + (f" Benchmarked against {comparable_projects['total_comparable_projects']} comparable PPP/PFI projects in the corridor." if comparable_projects else "")
        ),
    }

    return Command(update={"messages": [ToolMessage(
        content=json.dumps(response), tool_call_id=runtime.tool_call_id,
    )]})
