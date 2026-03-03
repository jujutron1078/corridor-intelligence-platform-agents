import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import CreditEnhancementInput


@tool("model_credit_enhancement", description=TOOL_DESCRIPTION)
def model_credit_enhancement_tool(
    payload: CreditEnhancementInput, runtime: ToolRuntime
) -> Command:
    """Models the impact of risk mitigation instruments on the final WACC."""

    # In a real-world scenario, this tool would:
    # 1. Receive the residual bankability gap from Tool 5 — the specific risk amount
    #    that commercial lenders will not absorb after debt sculpting and DSRA sizing.
    # 2. Decompose the gap into its root causes: political risk, revenue risk,
    #    currency risk, construction risk — each requiring a different instrument.
    # 3. For each instrument type (PRG, PRI, PCG, first-loss tranche), query a
    #    database of provider mandates (MIGA, GuarantCo, USAID DCA, AfDB PSF)
    #    to identify eligible providers and their standard pricing (bps).
    # 4. Model each instrument's coverage amount, annual premium cost, and
    #    the resulting reduction in commercial lender risk premium (spread compression).
    # 5. Run a cost-benefit analysis: compare annual premium paid vs annual
    #    interest saving from spread compression to confirm net WACC improvement.
    # 6. Compute the post-enhancement covenant breach probability by re-running
    #    the Monte Carlo from Tool 4 with the guarantee coverage applied.
    # 7. Check if the combined enhancement package fully closes the bankability gap
    #    (breach probability < 5%) or if residual risk remains.
    # 8. Model the full WACC impact: enhancement costs increase WACC slightly
    #    (premium payment) but spread compression reduces it more — net effect
    #    should always be negative (WACC improvement).

    # --- Mock: Derived from payload for realism ---
    gap_in_bankability = payload.gap_in_bankability     # e.g. 120_000_000

    response = {

        # ------------------------------------------------------------------ #
        #  BANKABILITY GAP ANALYSIS                                            #
        #  Production: derived from Tool 4 risk output and Tool 5 DSCR data. #
        #  Mock: pre-assessed from 6.8% residual covenant breach probability. #
        # ------------------------------------------------------------------ #
        "bankability_gap_analysis": {
            "residual_covenant_breach_probability": "6.8%",
            "lender_comfort_threshold": "5.0%",
            "gap_to_close": "1.8 percentage points of breach probability",
            "gap_amount_usd": gap_in_bankability,
            "gap_decomposition": {
                "political_risk_contribution": "38%",
                "revenue_shortfall_risk_contribution": "31%",
                "currency_transfer_risk_contribution": "19%",
                "construction_completion_risk_contribution": "12%"
            },
            "commercial_lender_feedback": [
                "IFC B-loan syndicate requires breach probability < 5% for credit approval",
                "Nigerian commercial banks require PRI coverage for cross-border segments",
                "European institutional investors require investment-grade equivalent rating — currently sub-IG without enhancement"
            ]
        },

        # ------------------------------------------------------------------ #
        #  ENHANCEMENT INSTRUMENTS EVALUATED                                  #
        #  Production: scored against provider mandates and pricing database. #
        #  Mock: pre-evaluated for Abidjan-Lagos 5-country corridor.         #
        # ------------------------------------------------------------------ #
        "instruments_evaluated": [
            {
                "instrument": "MIGA Political Risk Insurance (PRI)",
                "provider": "MIGA (World Bank Group)",
                "coverage_type": "Political risk — expropriation, currency transfer, breach of contract, war/civil disturbance",
                "coverage_amount_usd": 270_000_000,
                "coverage_pct_of_commercial_debt": "100%",
                "annual_premium_bps": 75,
                "annual_premium_usd": 2_025_000,
                "commercial_debt_spread_reduction_bps": 145,
                "annual_interest_saving_usd": 3_915_000,
                "net_annual_benefit_usd": 1_890_000,
                "cost_benefit_ratio": "1.93x (saves $1.93 for every $1 of premium)",
                "addresses_gap_component": "Political risk (38% of gap) + currency transfer (19% of gap)",
                "eligible": True,
                "eligibility_notes": "All 5 corridor countries are MIGA member states. Cross-border transmission qualifies under MIGA's infrastructure mandate.",
                "procurement_timeline_months": 6,
                "recommended": True
            },
            {
                "instrument": "World Bank Partial Risk Guarantee (PRG)",
                "provider": "World Bank IBRD/IDA",
                "coverage_type": "Government obligation risk — covers lenders if a government fails to meet contractual obligations (tariff payments, concession terms)",
                "coverage_amount_usd": 150_000_000,
                "coverage_pct_of_commercial_debt": "56%",
                "annual_premium_bps": 50,
                "annual_premium_usd": 750_000,
                "commercial_debt_spread_reduction_bps": 110,
                "annual_interest_saving_usd": 2_970_000,
                "net_annual_benefit_usd": 2_220_000,
                "cost_benefit_ratio": "3.96x",
                "addresses_gap_component": "Revenue shortfall risk from government non-payment (portion of 31% revenue risk gap)",
                "eligible": True,
                "eligibility_notes": "Requires counter-indemnity from each of the 5 governments. World Bank already engaged on IDA credit — PRG can be packaged alongside.",
                "procurement_timeline_months": 9,
                "recommended": True
            },
            {
                "instrument": "GuarantCo Partial Credit Guarantee (PCG)",
                "provider": "GuarantCo (PIDG)",
                "coverage_type": "Credit risk — covers a defined first-loss portion of commercial debt regardless of default cause",
                "coverage_amount_usd": 80_000_000,
                "coverage_pct_of_commercial_debt": "30%",
                "annual_premium_bps": 95,
                "annual_premium_usd": 760_000,
                "commercial_debt_spread_reduction_bps": 80,
                "annual_interest_saving_usd": 2_160_000,
                "net_annual_benefit_usd": 1_400_000,
                "cost_benefit_ratio": "2.84x",
                "addresses_gap_component": "Residual construction completion risk (12% of gap) and general credit risk",
                "eligible": True,
                "eligibility_notes": "GuarantCo mandated for IDA-eligible countries — Togo, Benin, Côte d'Ivoire qualify. Can be structured as first-loss to attract local currency investors.",
                "procurement_timeline_months": 5,
                "recommended": True
            },
            {
                "instrument": "USAID Development Credit Authority (DCA) Guarantee",
                "provider": "USAID DCA",
                "coverage_type": "Partial credit guarantee for U.S.-linked commercial lenders",
                "coverage_amount_usd": 50_000_000,
                "coverage_pct_of_commercial_debt": "19%",
                "annual_premium_bps": 40,
                "annual_premium_usd": 200_000,
                "commercial_debt_spread_reduction_bps": 60,
                "annual_interest_saving_usd": 1_080_000,
                "net_annual_benefit_usd": 880_000,
                "cost_benefit_ratio": "5.40x",
                "addresses_gap_component": "Supports DFC loan mobilization for digital infrastructure component",
                "eligible": True,
                "eligibility_notes": "Eligible if DFC is participating in financing. Covers U.S. private lenders only — limited applicability for West African commercial banks.",
                "procurement_timeline_months": 4,
                "recommended": False,
                "rejection_reason": "Coverage scope too narrow (U.S. lenders only). MIGA + PRG + PCG package already closes the gap without this instrument."
            },
            {
                "instrument": "AfDB Partial Risk Guarantee (PRG)",
                "provider": "African Development Bank",
                "coverage_type": "Government obligation risk for AfDB non-sovereign operations",
                "coverage_amount_usd": 100_000_000,
                "coverage_pct_of_commercial_debt": "37%",
                "annual_premium_bps": 65,
                "annual_premium_usd": 650_000,
                "commercial_debt_spread_reduction_bps": 90,
                "annual_interest_saving_usd": 2_430_000,
                "net_annual_benefit_usd": 1_780_000,
                "cost_benefit_ratio": "3.74x",
                "addresses_gap_component": "Complements World Bank PRG for Francophone corridor countries",
                "eligible": True,
                "eligibility_notes": "Can be structured alongside AfDB concessional loan — same credit committee approval process reduces procurement time.",
                "procurement_timeline_months": 7,
                "recommended": False,
                "rejection_reason": "Overlaps with World Bank PRG coverage. Adding both creates over-enhancement — unnecessary cost. Held as contingency if World Bank PRG is delayed."
            }
        ],

        # ------------------------------------------------------------------ #
        #  RECOMMENDED ENHANCEMENT PACKAGE                                    #
        #  Production: optimized combination closing gap at minimum cost.     #
        #  Mock: 3-instrument package for Abidjan-Lagos corridor.            #
        # ------------------------------------------------------------------ #
        "enhancement_plan": {
            "package_label": "3-Instrument Blended Enhancement Package",
            "instruments_selected": [
                {
                    "instrument": "MIGA Political Risk Insurance",
                    "provider": "MIGA",
                    "coverage_usd": 270_000_000,
                    "annual_premium_usd": 2_025_000,
                    "premium_bps": 75,
                    "spread_reduction_bps": 145,
                    "risk_addressed": "Political risk + currency transfer (57% of gap)"
                },
                {
                    "instrument": "World Bank Partial Risk Guarantee",
                    "provider": "World Bank",
                    "coverage_usd": 150_000_000,
                    "annual_premium_usd": 750_000,
                    "premium_bps": 50,
                    "spread_reduction_bps": 110,
                    "risk_addressed": "Government obligation / tariff payment risk (24% of gap)"
                },
                {
                    "instrument": "GuarantCo Partial Credit Guarantee",
                    "provider": "GuarantCo (PIDG)",
                    "coverage_usd": 80_000_000,
                    "annual_premium_usd": 760_000,
                    "premium_bps": 95,
                    "spread_reduction_bps": 80,
                    "risk_addressed": "Construction completion + residual credit risk (19% of gap)"
                }
            ],

            # --- Package Economics ---
            "package_economics": {
                "total_coverage_usd": 500_000_000,
                "coverage_as_pct_of_commercial_debt": "185% — overlapping coverage layers provide redundancy",
                "total_annual_premium_usd": 3_535_000,
                "total_premium_bps": 131,
                "total_spread_reduction_bps": 245,
                "total_annual_interest_saving_usd": 6_615_000,
                "net_annual_benefit_usd": 3_080_000,
                "package_cost_benefit_ratio": "1.87x — saves $1.87 for every $1 of premium paid",
                "npv_of_net_benefit_over_15_years_usd": 32_000_000
            },

            # --- WACC Impact ---
            "wacc_impact": {
                "wacc_before_enhancement": "5.66%",
                "premium_cost_addition_to_wacc": "+0.18%",
                "spread_compression_reduction_to_wacc": "-0.63%",
                "net_wacc_change": "-0.45%",
                "final_wacc_post_enhancement": "5.21%",
                "wacc_impact_breakdown": {
                    "miga_pri_net_impact": "-0.21%",
                    "world_bank_prg_net_impact": "-0.17%",
                    "guarantco_pcg_net_impact": "-0.07%"
                }
            },

            # --- Risk Closure ---
            "risk_closure": {
                "covenant_breach_probability_before": "6.8%",
                "covenant_breach_probability_after": "3.9%",
                "lender_comfort_threshold": "5.0%",
                "gap_fully_closed": True,
                "residual_breach_probability": "3.9% — below 5% lender comfort threshold",
                "credit_rating_impact": "Project moves from BB- (sub-investment grade) to BBB- (investment grade equivalent) with enhancement package — unlocks institutional investor participation"
            }
        },

        # ------------------------------------------------------------------ #
        #  FINAL WACC IMPACT                                                  #
        # ------------------------------------------------------------------ #
        "final_wacc_impact": "-0.45%",

        # ------------------------------------------------------------------ #
        #  COMPLETE FINANCING STRUCTURE SUMMARY                               #
        #  Production: consolidated view across all 6 tools in the workflow. #
        #  Mock: final investor-ready summary for Abidjan-Lagos corridor.    #
        # ------------------------------------------------------------------ #
        "final_financing_structure": {
            "label": "Abidjan-Lagos Corridor — Final Investment-Grade Financing Package",
            "total_project_cost_usd": 900_000_000,
            "capital_stack": {
                "grants_usd": 90_000_000,
                "concessional_loans_usd": 405_000_000,
                "commercial_debt_usd": 270_000_000,
                "equity_usd": 135_000_000
            },
            "debt_terms": {
                "concessional": "25-year tenor, 5-year grace, 2.8% fixed, DSCR-sculpted",
                "commercial": "15-year tenor, 4-year grace, 8.35% fixed (post-swap), DSCR-sculpted"
            },
            "credit_enhancement": "MIGA PRI + World Bank PRG + GuarantCo PCG",
            "reserve_accounts": "6-month DSRA ($38M) + Maintenance Reserve ($12M)",
            "key_metrics": {
                "final_wacc": "5.21%",
                "equity_irr": "15.4%",
                "project_irr": "10.3%",
                "min_dscr": "1.44x",
                "npv_usd": 218_000_000,
                "payback_years": 11.1,
                "covenant_breach_probability": "3.9%"
            },
            "investment_grade_achieved": True,
            "ready_for_dfi_board_submission": True,
            "ready_for_investor_roadshow": True
        },

        # ------------------------------------------------------------------ #
        #  PROCUREMENT ROADMAP FOR ENHANCEMENT INSTRUMENTS                    #
        # ------------------------------------------------------------------ #
        "procurement_roadmap": [
            {
                "step": 1,
                "action": "Submit MIGA PRI application",
                "institution": "MIGA",
                "timeline": "Month 1–6",
                "parallel_with": "AfDB pre-appraisal discussions",
                "key_requirement": "Project information memorandum + environmental assessment"
            },
            {
                "step": 2,
                "action": "Initiate World Bank PRG structuring",
                "institution": "World Bank",
                "timeline": "Month 3–9",
                "parallel_with": "IDA credit negotiation",
                "key_requirement": "Counter-indemnity agreements from all 5 governments — ECOWAS facilitation recommended"
            },
            {
                "step": 3,
                "action": "Submit GuarantCo PCG application",
                "institution": "GuarantCo / PIDG",
                "timeline": "Month 2–5",
                "parallel_with": "IFC A/B loan structuring",
                "key_requirement": "Audited financial statements of project SPV + EPC contract term sheet"
            },
            {
                "step": 4,
                "action": "Package all enhancement instruments for commercial lender credit approval",
                "institution": "IFC + Commercial Bank Syndicate",
                "timeline": "Month 10–12",
                "parallel_with": "Financial close preparation",
                "key_requirement": "All 3 enhancement instruments confirmed — letters of commitment required"
            }
        ],

        "message": (
            f"Credit enhancement modelling complete for ${gap_in_bankability:,.0f} bankability gap. "
            "5 instruments evaluated. Recommended 3-instrument package: "
            "MIGA PRI ($270M coverage, 75bps) + World Bank PRG ($150M coverage, 50bps) + GuarantCo PCG ($80M coverage, 95bps). "
            "Package economics: $3.54M annual premium cost vs $6.62M annual interest saving — net benefit $3.08M/year (1.87x cost-benefit ratio). "
            "WACC reduced from 5.66% → 5.21% (net -0.45% after premium costs). "
            "Covenant breach probability reduced from 6.8% → 3.9% — below 5.0% lender comfort threshold. GAP FULLY CLOSED. "
            "Credit rating equivalent improves from BB- → BBB- — unlocking institutional investor participation. "
            "Full financing package is investment-grade and ready for DFI board submission and investor roadshow. "
            "Financing Optimization Agent workflow complete across all 6 tools."
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