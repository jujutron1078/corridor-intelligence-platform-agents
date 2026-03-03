import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import ScenarioGenerationInput


@tool("generate_financing_scenarios", description=TOOL_DESCRIPTION)
def generate_financing_scenarios_tool(
    payload: ScenarioGenerationInput, runtime: ToolRuntime
) -> Command:
    """Creates multiple blended finance structures to optimize project returns."""

    # In a real-world scenario, this tool would:
    # 1. Pull eligible DFI instruments and their terms from the match_dfi_institutions output.
    # 2. Run a combinatorial optimization engine testing 20–30 funding stacks by varying:
    #    - Grant ratio (0–20% of CAPEX)
    #    - Concessional debt ratio (20–55% of CAPEX)
    #    - Commercial debt ratio (up to max_commercial_debt_ratio ceiling)
    #    - Equity ratio (remaining balance, floored at 15%)
    # 3. For each combination, compute WACC using a weighted average of instrument costs.
    # 4. Run a quick DCF pass to estimate equity IRR and project IRR per scenario.
    # 5. Filter out scenarios where DSCR < 1.3x or equity IRR < target_equity_irr.
    # 6. Rank survivors by a composite score: WACC (40%) + equity IRR (35%) + DSCR (25%).
    # 7. Return the top-ranked scenario as "recommended" plus a comparison table of all survivors.

    # --- Mock: Derived from payload for realism ---
    total_capex = payload.total_capex                          # e.g. 900_000_000
    target_equity_irr = payload.target_equity_irr or 0.14     # e.g. 0.14 = 14%
    max_commercial_debt = payload.max_commercial_debt_ratio or 0.40

    response = {

        # ------------------------------------------------------------------ #
        #  SCENARIO GENERATION METADATA                                        #
        #  Production: reflects actual combinatorial run stats.                #
        #  Mock: pre-set to reflect a realistic corridor-scale analysis.       #
        # ------------------------------------------------------------------ #
        "generation_metadata": {
            "total_combinations_tested": 312,
            "scenarios_passing_dscr_floor": 41,          # DSCR >= 1.3x
            "scenarios_passing_irr_floor": 28,           # Equity IRR >= target
            "scenarios_generated": 25,                   # Final shortlist after composite scoring
            "capex_input_usd": total_capex,
            "target_equity_irr": f"{target_equity_irr * 100:.1f}%",
            "max_commercial_debt_ratio": f"{max_commercial_debt * 100:.0f}%",
            "wacc_target_range": "5.0%–7.5%",
            "optimization_objective": "Minimize WACC subject to: Equity IRR >= target, DSCR >= 1.35x, Grant ratio <= 20%"
        },

        # ------------------------------------------------------------------ #
        #  RECOMMENDED SCENARIO (Scenario 14 — Best Composite Score)          #
        #  Production: top-ranked by composite scoring model.                  #
        #  Mock: pre-built for Abidjan-Lagos $900M corridor infrastructure.   #
        # ------------------------------------------------------------------ #
        "recommended_scenario": {
            "scenario_id": "S-14",
            "label": "Blended Anchor + IFC Commercial Tranche",
            "composite_score": 87.4,          # Out of 100
            "ranking": "1 of 25",

            # --- Capital Stack Breakdown ---
            "capital_stack": {
                "grants": {
                    "amount_usd": 90_000_000,
                    "percentage_of_capex": "10.0%",
                    "sources": [
                        {"institution": "EU Global Gateway", "amount_usd": 60_000_000, "instrument": "Climate Grant"},
                        {"institution": "AFD", "amount_usd": 30_000_000, "instrument": "Technical Assistance Grant"}
                    ],
                    "cost": "0.0%",
                    "rationale": "Grant tranche reduces WACC floor and improves equity returns without dilution."
                },
                "concessional_loans": {
                    "amount_usd": 405_000_000,
                    "percentage_of_capex": "45.0%",
                    "sources": [
                        {"institution": "AfDB", "amount_usd": 230_000_000, "instrument": "ADB/ADF Blended Loan", "rate": "3.2%", "tenor_years": 25, "grace_period_years": 5},
                        {"institution": "World Bank IDA/IBRD", "amount_usd": 120_000_000, "instrument": "IDA Credit + IBRD Loan", "rate": "2.1%", "tenor_years": 30, "grace_period_years": 5},
                        {"institution": "AFD", "amount_usd": 55_000_000, "instrument": "Concessional Loan", "rate": "2.8%", "tenor_years": 22, "grace_period_years": 4}
                    ],
                    "blended_concessional_rate": "2.8%",
                    "rationale": "AfDB anchors the concessional stack. World Bank IDA unlocks Togo/Benin eligibility. Combined 45% concessional share pulls WACC below 6%."
                },
                "commercial_debt": {
                    "amount_usd": 270_000_000,
                    "percentage_of_capex": "30.0%",
                    "sources": [
                        {"institution": "IFC", "amount_usd": 160_000_000, "instrument": "IFC A-Loan", "rate": "SOFR + 2.85%", "tenor_years": 15, "grace_period_years": 3},
                        {"institution": "Commercial Banks (IFC B-Loan)", "amount_usd": 110_000_000, "instrument": "Parallel B-Loan", "rate": "SOFR + 3.20%", "tenor_years": 12, "grace_period_years": 2}
                    ],
                    "blended_commercial_rate": "SOFR + 3.0% (~8.3% at current rates)",
                    "credit_enhancement": "World Bank PRG covers $120M of commercial exposure — reduces lender risk premium by ~80bps",
                    "rationale": "IFC A/B loan structure mobilizes commercial banks at scale. PRG from World Bank de-risks the tranche and improves terms."
                },
                "equity": {
                    "amount_usd": 135_000_000,
                    "percentage_of_capex": "15.0%",
                    "sources": [
                        {"investor_type": "Infrastructure Private Equity Fund", "amount_usd": 80_000_000, "expected_irr": "16.2%"},
                        {"investor_type": "DFI Equity (IFC)", "amount_usd": 35_000_000, "expected_irr": "13.5%"},
                        {"investor_type": "Government Co-investment (Ghana + Nigeria)", "amount_usd": 20_000_000, "expected_irr": "10.0%"}
                    ],
                    "blended_equity_cost": "14.8%",
                    "rationale": "Minimum equity floor of 15% preserves gearing headroom. DFI equity alongside private equity signals confidence and lowers perceived risk."
                }
            },

            # --- WACC Computation ---
            "wacc_computation": {
                "grants_contribution": "0.0% × 10.0% = 0.00%",
                "concessional_contribution": "2.8% × 45.0% = 1.26%",
                "commercial_contribution": "8.3% × 30.0% = 2.49%",
                "equity_contribution": "14.8% × 15.0% = 2.22%",
                "gross_wacc": "5.97%",
                "tax_shield_adjustment": "-0.31%",
                "final_wacc": "5.66%"
            },

            # --- Financial Performance Estimates ---
            "financial_performance": {
                "equity_irr": "15.1%",
                "project_irr": "10.3%",
                "estimated_npv_usd": "218_000_000",
                "min_dscr": "1.42x",
                "avg_dscr": "1.71x",
                "payback_period_years": 11.5,
                "break_even_year": 8,
                "target_equity_irr_met": True,
                "dscr_covenant_met": True         # Covenant floor typically 1.30x
            },

            # --- Debt Repayment Profile ---
            "debt_repayment_profile": {
                "construction_period_years": 4,
                "grace_period_years": 5,
                "first_principal_repayment_year": 6,
                "peak_debt_service_year": 10,
                "peak_debt_service_usd": 68_500_000,
                "final_maturity_year": 30,
                "amortization_profile": "Sculpted to match cash flow ramp-up (lower in early years, higher post-Year 8)"
            }
        },

        # ------------------------------------------------------------------ #
        #  SCENARIO COMPARISON TABLE (Top 5 Scenarios)                         #
        #  Production: full 25-scenario table with all metrics.                #
        #  Mock: top 5 for illustration — shows trade-offs clearly.            #
        # ------------------------------------------------------------------ #
        "scenario_comparison": [
            {
                "scenario_id": "S-14",
                "label": "Blended Anchor + IFC Commercial Tranche",
                "grants_pct": "10%",
                "concessional_pct": "45%",
                "commercial_pct": "30%",
                "equity_pct": "15%",
                "wacc": "5.66%",
                "equity_irr": "15.1%",
                "project_irr": "10.3%",
                "min_dscr": "1.42x",
                "composite_score": 87.4,
                "recommended": True,
                "trade_off": "Best overall balance — strong DSCR, WACC below 6%, IRR above target."
            },
            {
                "scenario_id": "S-09",
                "label": "High Grant / Low Commercial",
                "grants_pct": "18%",
                "concessional_pct": "50%",
                "commercial_pct": "17%",
                "equity_pct": "15%",
                "wacc": "4.91%",
                "equity_irr": "17.4%",
                "project_irr": "11.1%",
                "min_dscr": "1.61x",
                "composite_score": 83.1,
                "recommended": False,
                "trade_off": "Excellent WACC and IRR but requires $162M in grants — unlikely to be fully available. Execution risk is high."
            },
            {
                "scenario_id": "S-21",
                "label": "Commercial-Heavy / Minimal Grants",
                "grants_pct": "5%",
                "concessional_pct": "35%",
                "commercial_pct": "40%",
                "equity_pct": "20%",
                "wacc": "7.12%",
                "equity_irr": "13.2%",
                "project_irr": "9.1%",
                "min_dscr": "1.31x",
                "composite_score": 71.8,
                "recommended": False,
                "trade_off": "Feasible without DFI grants but WACC is high and equity IRR barely meets target. Sensitive to cost overruns."
            },
            {
                "scenario_id": "S-06",
                "label": "DFI-Only / No Commercial Debt",
                "grants_pct": "12%",
                "concessional_pct": "68%",
                "commercial_pct": "0%",
                "equity_pct": "20%",
                "wacc": "4.44%",
                "equity_irr": "16.8%",
                "project_irr": "11.8%",
                "min_dscr": "1.85x",
                "composite_score": 78.3,
                "recommended": False,
                "trade_off": "Lowest WACC but fully dependent on DFI appetite. $612M concessional ask exceeds realistic single-corridor allocation. Not bankable at scale."
            },
            {
                "scenario_id": "S-18",
                "label": "Equity-Heavy / Reduced Debt",
                "grants_pct": "8%",
                "concessional_pct": "38%",
                "commercial_pct": "24%",
                "equity_pct": "30%",
                "wacc": "8.34%",
                "equity_irr": "14.1%",
                "project_irr": "9.6%",
                "min_dscr": "1.55x",
                "composite_score": 65.2,
                "recommended": False,
                "trade_off": "Stronger DSCR but WACC is too high. Equity IRR barely meets target given higher equity cost. Only suitable if debt markets are closed."
            }
        ],

        # ------------------------------------------------------------------ #
        #  SENSITIVITY FLAGS                                                   #
        #  Production: computed from quick Monte Carlo pass on each scenario.  #
        #  Mock: pre-assessed for recommended scenario S-14.                  #
        # ------------------------------------------------------------------ #
        "sensitivity_flags": {
            "scenario": "S-14",
            "capex_overrun_10pct_impact": "Equity IRR drops from 15.1% → 13.4% (still above target)",
            "revenue_shortfall_15pct_impact": "Min DSCR drops from 1.42x → 1.24x (breaches 1.30x covenant — FLAG)",
            "sofr_rate_increase_100bps_impact": "WACC increases from 5.66% → 6.14%, Equity IRR drops to 14.3%",
            "grant_shortfall_50pct_impact": "WACC increases from 5.66% → 6.31%, equity must absorb $45M gap",
            "critical_assumption": "Revenue realization is the most sensitive variable. Anchor load contracts covering 70%+ of projected Year 1 revenue should be secured before financial close."
        },

        # ------------------------------------------------------------------ #
        #  NEXT STEPS                                                          #
        # ------------------------------------------------------------------ #
        "next_steps": [
            "Pass recommended scenario (S-14) capital stack to `build_financial_model` for full 25-year DCF.",
            "Initiate AfDB pre-appraisal discussions to confirm $230M concessional anchor availability.",
            "Confirm EU Global Gateway grant eligibility — submit Expression of Interest within 60 days.",
            "Engage IFC Infrastructure team to structure A/B loan and assess MIGA PRI appetite.",
            "Secure anchor load off-take LOIs (Dangote, Lekki FTZ, Obuasi Mine) to reduce revenue sensitivity."
        ],

        "message": (
            f"25 financing scenarios generated from 312 combinations tested against ${total_capex:,.0f} CAPEX. "
            f"Scenario S-14 ('Blended Anchor + IFC Commercial Tranche') ranked #1 with composite score 87.4/100. "
            f"Recommended capital stack: 10% grants ($90M) + 45% concessional debt ($405M) + 30% commercial debt ($270M) + 15% equity ($135M). "
            f"Final WACC: 5.66% — within 5.0%–7.5% target range. "
            f"Projected equity IRR: 15.1% — exceeds {target_equity_irr * 100:.1f}% target. "
            f"Minimum DSCR: 1.42x — above 1.30x covenant floor. "
            f"CRITICAL FLAG: Revenue shortfall scenario breaches DSCR covenant — anchor load off-take contracts must be prioritized before financial close. "
            f"Proceed to `build_financial_model` with Scenario S-14 structure."
        )
    }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response),
                    tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )