import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import DebtTermInput


@tool("optimize_debt_terms", description=TOOL_DESCRIPTION)
def optimize_debt_terms_tool(
    payload: DebtTermInput, runtime: ToolRuntime
) -> Command:
    """Aligns debt repayment with infrastructure cash flow patterns."""

    # In a real-world scenario, this tool would:
    # 1. Extract the annual CFADS (Cash Flow Available for Debt Service) profile
    #    from Tool 3 output — this is the cash the project generates each year
    #    after OPEX but before debt service.
    # 2. For each lender tranche separately (concessional vs commercial), test
    #    a matrix of tenor (10–30 years) x grace period (2–7 years) combinations.
    # 3. For each combination, compute the annual debt service schedule and
    #    divide into CFADS to get year-by-year DSCR.
    # 4. Apply DSCR-sculpting: instead of flat equal payments, solve backwards
    #    from a target DSCR (e.g. 1.35x minimum) to derive the maximum allowable
    #    debt service in each year, then set principal repayment accordingly.
    # 5. Identify the combination that: (a) maintains min DSCR above covenant floor,
    #    (b) minimizes total interest cost over project life, (c) fully amortizes
    #    debt within the concession period.
    # 6. Run a comparison table across all tenor/grace combinations showing
    #    min DSCR, total interest paid, and NPV impact for each.
    # 7. Flag any combination where final maturity extends beyond the concession
    #    term — lenders will not accept bullet repayment risk at concession end.

    # --- Mock: Derived from payload for realism ---
    debt_amount = payload.debt_amount                                        # e.g. 675_000_000
    cfads = payload.cash_flow_available_for_debt_service                     # e.g. [53M, 61M, 53M, 78M, 138M, ...]

    response = {

        # ------------------------------------------------------------------ #
        #  OPTIMIZATION CONFIGURATION                                          #
        #  Production: driven dynamically by CFADS shape and debt structure.  #
        #  Mock: pre-set for $675M debt across two tranches.                  #
        # ------------------------------------------------------------------ #
        "optimization_configuration": {
            "total_debt_amount_usd": debt_amount,
            "debt_tranches": 2,
            "tranche_breakdown": {
                "concessional_debt_usd": 405_000_000,     # AfDB + World Bank + AFD
                "commercial_debt_usd": 270_000_000        # IFC A-loan + B-loan
            },
            "cfads_years_modelled": 25,
            "cfads_year_1_usd": 53_000_000,
            "cfads_year_5_usd": 138_500_000,
            "cfads_year_10_usd": 235_200_000,
            "tenor_range_tested_years": "10–30",
            "grace_period_range_tested_years": "2–7",
            "combinations_tested": 54,
            "target_min_dscr": 1.35,
            "covenant_floor_dscr": 1.30,
            "sculpting_method": "DSCR-sculpted amortization (target DSCR lock)",
            "concession_period_years": 30,
            "final_maturity_must_be_within_concession": True
        },

        # ------------------------------------------------------------------ #
        #  TENOR COMPARISON TABLE                                              #
        #  Production: computed across all 54 tenor x grace combinations.     #
        #  Mock: representative cross-section showing key trade-offs.         #
        # ------------------------------------------------------------------ #
        "tenor_comparison": {
            "note": "All combinations use DSCR-sculpted amortization. Ranked by composite score: min DSCR (40%) + total interest cost (35%) + NPV impact (25%).",
            "combinations": [
                {
                    "scenario": "Recommended — S-OPT-3",
                    "concessional_tenor_years": 25,
                    "commercial_tenor_years": 15,
                    "grace_period_years": 5,
                    "amortization_profile": "Sculpted",
                    "min_dscr": 1.44,
                    "avg_dscr": 1.78,
                    "trough_year": "Year 3 (2031)",
                    "total_interest_paid_usd": 312_000_000,
                    "npv_impact_vs_base_usd": "+$18M",
                    "final_maturity_year": 2053,
                    "within_concession": True,
                    "composite_score": 91.2,
                    "recommended": True,
                    "note": "Best balance — min DSCR comfortably above covenant, lowest total interest of viable options."
                },
                {
                    "scenario": "Short Tenor — S-OPT-1",
                    "concessional_tenor_years": 18,
                    "commercial_tenor_years": 12,
                    "grace_period_years": 4,
                    "amortization_profile": "Sculpted",
                    "min_dscr": 1.31,
                    "avg_dscr": 1.52,
                    "trough_year": "Year 3 (2031)",
                    "total_interest_paid_usd": 224_000_000,
                    "npv_impact_vs_base_usd": "-$31M",
                    "final_maturity_year": 2046,
                    "within_concession": True,
                    "composite_score": 72.4,
                    "recommended": False,
                    "note": "Lowest total interest but min DSCR only 1.31x — dangerously close to 1.30x covenant floor. Rejected."
                },
                {
                    "scenario": "Long Tenor — S-OPT-5",
                    "concessional_tenor_years": 30,
                    "commercial_tenor_years": 18,
                    "grace_period_years": 6,
                    "amortization_profile": "Sculpted",
                    "min_dscr": 1.61,
                    "avg_dscr": 2.04,
                    "trough_year": "Year 3 (2031)",
                    "total_interest_paid_usd": 428_000_000,
                    "npv_impact_vs_base_usd": "-$44M",
                    "final_maturity_year": 2059,
                    "within_concession": True,
                    "composite_score": 78.1,
                    "recommended": False,
                    "note": "Excellent DSCR headroom but $116M more interest paid vs recommended. Equity IRR drops to 13.8%. Over-engineered."
                },
                {
                    "scenario": "Flat Amortization (Benchmark) — S-OPT-0",
                    "concessional_tenor_years": 25,
                    "commercial_tenor_years": 15,
                    "grace_period_years": 5,
                    "amortization_profile": "Flat (equal installments)",
                    "min_dscr": 1.29,
                    "avg_dscr": 1.68,
                    "trough_year": "Year 3 (2031)",
                    "total_interest_paid_usd": 318_000_000,
                    "npv_impact_vs_base_usd": "Baseline",
                    "final_maturity_year": 2053,
                    "within_concession": True,
                    "composite_score": 61.3,
                    "recommended": False,
                    "note": "Same tenor as recommended but flat repayment breaches 1.30x covenant in Year 3. Confirms sculpting is essential."
                }
            ]
        },

        # ------------------------------------------------------------------ #
        #  RECOMMENDED OPTIMIZED TERMS (S-OPT-3)                              #
        #  Production: output of optimization algorithm for each tranche.     #
        #  Mock: pre-built for Abidjan-Lagos two-tranche debt structure.      #
        # ------------------------------------------------------------------ #
        "optimized_terms": {

            # --- Concessional Tranche (AfDB + World Bank + AFD) ---
            "concessional_tranche": {
                "lenders": ["AfDB ($230M)", "World Bank IDA/IBRD ($120M)", "AFD ($55M)"],
                "amount_usd": 405_000_000,
                "tenor_years": 25,
                "grace_period_years": 5,
                "interest_rate": "2.8% fixed (blended concessional)",
                "amortization_profile": "Sculpted — DSCR-locked at 1.38x minimum",
                "first_principal_payment_year": 2034,     # Year 5 of operations
                "final_maturity_year": 2058,
                "annual_debt_service_schedule": {
                    "years_1_to_5_interest_only_usd": 11_340_000,
                    "year_6_usd": 19_200_000,
                    "year_10_usd": 28_400_000,
                    "year_15_usd": 38_100_000,
                    "year_20_usd": 31_600_000,
                    "year_25_usd": 22_800_000,
                    "profile_shape": "Bell curve — rises through Year 15 as revenue grows, tapers as principal reduces"
                },
                "total_interest_over_life_usd": 198_000_000,
                "effective_all_in_cost": "3.1% (including arrangement fees)",
                "prepayment_allowed": True,
                "prepayment_penalty": "None after Year 10 (AfDB/WB standard terms)"
            },

            # --- Commercial Tranche (IFC A-Loan + B-Loan) ---
            "commercial_tranche": {
                "lenders": ["IFC A-Loan ($160M)", "Commercial Banks B-Loan ($110M)"],
                "amount_usd": 270_000_000,
                "tenor_years": 15,
                "grace_period_years": 4,
                "interest_rate_base": "SOFR + 2.85% (IFC A-Loan)",
                "interest_rate_blended": "SOFR + 3.05% blended (~8.35% at current SOFR)",
                "interest_rate_swap": "Recommended — fix SOFR component at 5.3% at financial close",
                "fixed_all_in_rate_post_swap": "8.35% fixed",
                "amortization_profile": "Sculpted — DSCR-locked at 1.38x minimum",
                "first_principal_payment_year": 2033,     # Year 4 of operations
                "final_maturity_year": 2047,
                "annual_debt_service_schedule": {
                    "years_1_to_4_interest_only_usd": 22_545_000,
                    "year_5_usd": 31_800_000,
                    "year_8_usd": 42_100_000,
                    "year_12_usd": 38_600_000,
                    "year_15_usd": 29_400_000,
                    "profile_shape": "Front-loaded post grace — aligns with anchor load ramp-up period"
                },
                "total_interest_over_life_usd": 114_000_000,
                "effective_all_in_cost": "8.6% (including arrangement and commitment fees)",
                "prepayment_allowed": True,
                "prepayment_penalty": "1.0% of outstanding balance in Years 1–5, nil thereafter",
                "cash_sweep_mechanism": "50% of excess CFADS above 1.50x DSCR swept to accelerate repayment"
            },

            # --- Combined Debt Service Summary ---
            "combined_debt_service": {
                "total_debt_usd": 675_000_000,
                "total_interest_over_life_usd": 312_000_000,
                "total_repayment_usd": 987_000_000,
                "peak_annual_debt_service_usd": 68_400_000,
                "peak_debt_service_year": 2038,           # Year 9 — both tranches in repayment
                "final_debt_free_year": 2058,
                "weighted_avg_tenor_years": 21.4,
                "blended_all_in_cost": "5.2%"
            }
        },

        # ------------------------------------------------------------------ #
        #  DSCR IMPACT OF OPTIMIZATION                                         #
        #  Production: year-by-year DSCR recomputed post-optimization.        #
        #  Mock: key years showing improvement over flat amortization.         #
        # ------------------------------------------------------------------ #
        "dscr_impact": {
            "note": "Comparison between flat amortization (rejected) and sculpted (recommended).",
            "improvement_summary": {
                "trough_dscr_flat": "1.29x — breaches 1.30x covenant",
                "trough_dscr_sculpted": "1.44x — 14bps above covenant floor",
                "trough_year_improvement": "+0.15x DSCR in critical Year 3",
                "covenant_breach_eliminated": True,
                "years_above_1_50x": "18 of 25 operating years"
            },
            "annual_dscr_post_optimization": [
                {"year": 2029, "cfads_usd": 53_000_000, "debt_service_usd": 33_840_000, "dscr": 1.57, "status": "Healthy — interest only period"},
                {"year": 2030, "cfads_usd": 61_000_000, "debt_service_usd": 33_840_000, "dscr": 1.80, "status": "Improving"},
                {"year": 2031, "cfads_usd": 53_000_000, "debt_service_usd": 36_810_000, "dscr": 1.44, "status": "Trough — ramp-up dip, above covenant"},
                {"year": 2032, "cfads_usd": 78_000_000, "debt_service_usd": 43_200_000, "dscr": 1.81, "status": "Recovery"},
                {"year": 2033, "cfads_usd": 138_500_000, "debt_service_usd": 68_400_000, "dscr": 2.03, "status": "Strong — both tranches in repayment"},
                {"year": 2038, "cfads_usd": 235_200_000, "debt_service_usd": 68_400_000, "dscr": 3.44, "status": "Peak cash generation"},
                {"year": 2047, "cfads_usd": 318_000_000, "debt_service_usd": 22_800_000, "dscr": 13.9, "status": "Commercial tranche fully repaid — minimal debt service"}
            ]
        },

        # ------------------------------------------------------------------ #
        #  RESERVE ACCOUNTS RECOMMENDED                                        #
        #  Production: sized dynamically from debt service schedule.          #
        #  Mock: standard project finance reserve account structure.          #
        # ------------------------------------------------------------------ #
        "reserve_accounts": {
            "debt_service_reserve_account": {
                "size": "6 months forward debt service",
                "amount_at_close_usd": 38_000_000,
                "funded_by": "Equity contribution at financial close",
                "purpose": "Covers debt service if CFADS falls short in any 6-month period",
                "dscr_breach_probability_impact": "Reduces covenant breach probability from 15.3% → 6.8%"
            },
            "maintenance_reserve_account": {
                "size": "12 months forward major maintenance capex",
                "amount_at_close_usd": 12_000_000,
                "funded_by": "Operating cash flow sweep (annual top-up)",
                "purpose": "Ensures major O&M does not disrupt debt service in any year"
            },
            "cash_sweep_waterfall": {
                "priority_1": "Operating costs (OPEX)",
                "priority_2": "Scheduled debt service",
                "priority_3": "DSRA top-up to 6-month target",
                "priority_4": "Maintenance reserve top-up",
                "priority_5": "Excess cash sweep — 50% to accelerate commercial debt repayment",
                "priority_6": "Remaining — distributable to equity"
            }
        },

        # ------------------------------------------------------------------ #
        #  EQUITY IRR IMPACT OF OPTIMIZED TERMS                               #
        # ------------------------------------------------------------------ #
        "equity_irr_impact": {
            "base_case_irr_before_optimization": "15.1%",
            "irr_after_sculpting": "15.4%",
            "irr_improvement": "+0.3%",
            "explanation": (
                "Sculpted amortization shifts debt service from early low-cash years to "
                "later high-cash years, preserving more free cash flow for equity distributions "
                "in Years 1–5 and slightly improving equity IRR."
            ),
            "payback_period_before": "11.5 years",
            "payback_period_after": "11.1 years"
        },

        "message": (
            f"Debt term optimization complete across 54 tenor/grace period combinations for "
            f"${debt_amount:,.0f} total debt across 2 tranches. "
            "Recommended structure: Concessional tranche — 25-year tenor, 5-year grace, 2.8% fixed, DSCR-sculpted. "
            "Commercial tranche — 15-year tenor, 4-year grace, 8.35% fixed (post-swap), DSCR-sculpted. "
            "Key outcome: Trough DSCR improved from 1.29x (flat — covenant breach) to 1.44x (sculpted — covenant met). "
            "Total interest over project life: $312M. Blended all-in debt cost: 5.2%. "
            "Equity IRR improves marginally from 15.1% → 15.4% due to early-year cash flow preservation. "
            "DSCR covenant breach probability reduced from 15.3% → 6.8% with 6-month DSRA in place. "
            "Remaining breach probability of 6.8% still above 5% lender comfort threshold — "
            "proceed to `model_credit_enhancement` for residual bankability gap closure."
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