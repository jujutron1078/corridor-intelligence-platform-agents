import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import FinancialModelInput


@tool("build_financial_model", description=TOOL_DESCRIPTION)
def build_financial_model_tool(
    payload: FinancialModelInput, runtime: ToolRuntime
) -> Command:
    """Calculates core financial metrics for the project lifecycle."""

    # In a real-world scenario, this tool would:
    # 1. Build a full 3-statement model (P&L, Balance Sheet, Cash Flow Statement)
    #    over a 25–30 year lifecycle, driven by revenue_projections and capex_opex_data.
    # 2. Compute annual DSCR by dividing Cash Flow Available for Debt Service (CFADS)
    #    by scheduled debt service (principal + interest) for each lender tranche.
    # 3. Run a DCF using the WACC from the financing_structure to compute NPV.
    # 4. Calculate equity IRR by modeling levered free cash flows to equity holders
    #    after debt service, using the equity injection timing from the financing plan.
    # 5. Calculate project IRR on unlevered free cash flows (pre-financing).
    # 6. Identify the minimum DSCR year and flag if it breaches the 1.30x covenant floor.
    # 7. Generate annual cash flow waterfall: Revenue → OPEX → EBITDA → Debt Service
    #    → Tax → Equity distributions.
    # 8. Produce a year-by-year summary table for lender reporting and investor decks.

    response = {

        # ------------------------------------------------------------------ #
        #  MODEL CONFIGURATION                                                 #
        #  Production: derived dynamically from payload inputs.               #
        #  Mock: pre-set for Abidjan-Lagos $900M corridor infrastructure.     #
        # ------------------------------------------------------------------ #
        "model_configuration": {
            "model_type": "Project Finance DCF — 3-Statement",
            "projection_period_years": 25,
            "construction_period_years": 4,
            "operations_start_year": 2029,
            "base_currency": "USD",
            "discount_rate_wacc": "5.66%",
            "inflation_assumption": "2.5% per annum",
            "revenue_escalation": "3.0% per annum (CPI-linked tariffs)",
            "opex_escalation": "2.5% per annum",
            "tax_rate": "25% (blended across 5 corridor countries)",
            "depreciation_method": "Straight-line over 25 years",
            "terminal_value_included": False,
            "debt_sculpting": "DSCR-sculpted amortization aligned to cash flow ramp-up"
        },

        # ------------------------------------------------------------------ #
        #  CORE FINANCIAL METRICS                                              #
        #  Production: computed from full DCF and levered/unlevered models.   #
        #  Mock: pre-calculated for Scenario S-14 financing structure.        #
        # ------------------------------------------------------------------ #
        "metrics": {
            "equity_irr": "15.1%",
            "project_irr": "10.3%",
            "net_present_value_usd": 218_000_000,
            "min_dscr": 1.42,
            "avg_dscr": 1.71,
            "max_dscr": 2.18,
            "min_dscr_year": 2031,              # Year 3 of operations — ramp-up period
            "payback_period_years": 11.5,
            "break_even_year": 2037,            # Year 8 of operations
            "equity_multiple": "2.8x",          # Total equity returned / equity invested
            "target_equity_irr_met": True,
            "dscr_covenant_met": True,          # Min DSCR 1.42x > 1.30x covenant floor
            "npv_positive": True
        },

        # ------------------------------------------------------------------ #
        #  REVENUE MODEL                                                       #
        #  Production: built from anchor load contracts + tariff schedules.   #
        #  Mock: aggregated from 45–57 anchor loads identified in corridor.   #
        # ------------------------------------------------------------------ #
        "revenue_model": {
            "revenue_streams": [
                {
                    "stream": "Transmission Wheeling Charges",
                    "description": "Tariff charged per kWh transmitted across corridor grid",
                    "year_1_revenue_usd": 38_000_000,
                    "year_5_revenue_usd": 89_000_000,
                    "year_10_revenue_usd": 148_000_000,
                    "tariff_rate": "$0.018–0.024/kWh",
                    "volume_year_1_gwh": 2_100,
                    "volume_year_10_gwh": 7_400,
                    "contract_type": "Use-of-system agreements with 5 national utilities",
                    "off_take_certainty": "HIGH — regulated tariff, government-backed"
                },
                {
                    "stream": "Capacity Reservation Charges",
                    "description": "Fixed monthly charge for reserved transmission capacity by anchor loads",
                    "year_1_revenue_usd": 22_000_000,
                    "year_5_revenue_usd": 41_000_000,
                    "year_10_revenue_usd": 63_000_000,
                    "tariff_rate": "$8,500/MW/month reserved",
                    "contracted_capacity_mw_year_1": 215,
                    "contracted_capacity_mw_year_10": 620,
                    "contract_type": "15-year capacity reservations (Dangote, Obuasi, Lekki FTZ)",
                    "off_take_certainty": "HIGH — take-or-pay contracts with investment-grade counterparties"
                },
                {
                    "stream": "Fiber Optic Leasing (Co-deployed)",
                    "description": "Dark fiber and lit services leased to telecoms along corridor right-of-way",
                    "year_1_revenue_usd": 8_000_000,
                    "year_5_revenue_usd": 19_000_000,
                    "year_10_revenue_usd": 31_000_000,
                    "tariff_rate": "$4,200/km/year (dark fiber IRU)",
                    "contract_type": "15–20 year Indefeasible Right of Use (IRU) agreements",
                    "off_take_certainty": "MEDIUM — 3 LOIs signed, full contracts pending"
                },
                {
                    "stream": "Ancillary Services (Frequency & Voltage)",
                    "description": "Revenue from providing grid balancing services to WAPP and national utilities",
                    "year_1_revenue_usd": 4_500_000,
                    "year_5_revenue_usd": 11_000_000,
                    "year_10_revenue_usd": 18_000_000,
                    "contract_type": "Ancillary service agreements with WAPP",
                    "off_take_certainty": "MEDIUM — subject to WAPP market development"
                }
            ],
            "total_revenue_summary": {
                "year_1_usd": 72_500_000,
                "year_3_usd": 98_000_000,
                "year_5_usd": 160_000_000,
                "year_10_usd": 260_000_000,
                "year_25_usd": 398_000_000,
                "revenue_concentration_risk": "Top 3 anchor loads (Dangote, Lekki FTZ, Obuasi) represent 38% of Year 1 revenue — moderate concentration"
            }
        },

        # ------------------------------------------------------------------ #
        #  COST MODEL                                                          #
        #  Production: built from Infrastructure agent CAPEX/OPEX outputs.   #
        #  Mock: detailed for $900M Abidjan-Lagos transmission corridor.      #
        # ------------------------------------------------------------------ #
        "cost_model": {
            "capex": {
                "total_capex_usd": 900_000_000,
                "co_location_savings_usd": 162_000_000,
                "gross_capex_usd": 1_062_000_000,
                "breakdown": {
                    "transmission_lines_and_towers_usd": 490_000_000,
                    "substations_usd": 210_000_000,
                    "fiber_optic_co_deployment_usd": 42_000_000,
                    "scada_and_control_systems_usd": 55_000_000,
                    "environmental_and_social_usd": 62_000_000,
                    "project_development_costs_usd": 18_000_000,
                    "contingency_15pct_usd": 23_000_000
                },
                "capex_phasing": {
                    "year_1_construction_usd": 180_000_000,
                    "year_2_construction_usd": 270_000_000,
                    "year_3_construction_usd": 315_000_000,
                    "year_4_construction_usd": 135_000_000
                }
            },
            "opex": {
                "year_1_opex_usd": 19_500_000,
                "year_5_opex_usd": 21_500_000,
                "year_10_opex_usd": 24_800_000,
                "breakdown": {
                    "operations_and_maintenance_usd": 12_000_000,
                    "insurance_usd": 3_200_000,
                    "scada_and_it_systems_usd": 1_800_000,
                    "management_and_admin_usd": 1_500_000,
                    "environmental_monitoring_usd": 600_000,
                    "regulatory_fees_usd": 400_000
                },
                "opex_as_pct_of_revenue_year_5": "13.4%"
            }
        },

        # ------------------------------------------------------------------ #
        #  ANNUAL CASH FLOW WATERFALL (Key Years)                              #
        #  Production: full 25-year year-by-year table.                       #
        #  Mock: representative years showing construction, ramp-up, steady.  #
        # ------------------------------------------------------------------ #
        "cash_flow_waterfall": {
            "currency": "USD Millions",
            "note": "Production model returns full 25-year annual table. Mock shows representative years.",
            "years": [
                {
                    "year": 2029,
                    "period": "Year 1 — Operations Ramp-up",
                    "revenue": 72.5,
                    "opex": -19.5,
                    "ebitda": 53.0,
                    "ebitda_margin": "73.1%",
                    "depreciation": -36.0,
                    "ebit": 17.0,
                    "interest_expense": -38.2,
                    "ebt": -21.2,
                    "tax": 0.0,
                    "net_income": -21.2,
                    "add_back_depreciation": 36.0,
                    "cfads": 53.0,
                    "debt_service": -37.3,
                    "dscr": 1.42,
                    "equity_distribution": 0.0,
                    "closing_cash_balance": 15.7
                },
                {
                    "year": 2033,
                    "period": "Year 5 — Stabilised Operations",
                    "revenue": 160.0,
                    "opex": -21.5,
                    "ebitda": 138.5,
                    "ebitda_margin": "86.6%",
                    "depreciation": -36.0,
                    "ebit": 102.5,
                    "interest_expense": -29.4,
                    "ebt": 73.1,
                    "tax": -18.3,
                    "net_income": 54.8,
                    "add_back_depreciation": 36.0,
                    "cfads": 138.5,
                    "debt_service": -58.1,
                    "dscr": 2.38,
                    "equity_distribution": 48.0,
                    "closing_cash_balance": 32.4
                },
                {
                    "year": 2038,
                    "period": "Year 10 — Full Capacity",
                    "revenue": 260.0,
                    "opex": -24.8,
                    "ebitda": 235.2,
                    "ebitda_margin": "90.5%",
                    "depreciation": -36.0,
                    "ebit": 199.2,
                    "interest_expense": -18.6,
                    "ebt": 180.6,
                    "tax": -45.1,
                    "net_income": 135.5,
                    "add_back_depreciation": 36.0,
                    "cfads": 235.2,
                    "debt_service": -61.4,
                    "dscr": 3.83,
                    "equity_distribution": 120.0,
                    "closing_cash_balance": 53.8
                }
            ]
        },

        # ------------------------------------------------------------------ #
        #  DSCR PROFILE (Annual — Key Years)                                  #
        #  Production: full annual DSCR table with per-tranche breakdown.     #
        #  Mock: summary profile showing ramp-up, trough, and recovery.       #
        # ------------------------------------------------------------------ #
        "dscr_profile": {
            "covenant_floor": 1.30,
            "target_minimum": 1.40,
            "years_below_covenant": 0,
            "trough_year": 2031,
            "trough_dscr": 1.42,
            "trough_comment": "Year 3 of operations — ramp-up period before full anchor load realization",
            "annual_summary": [
                {"year": 2029, "dscr": 1.42, "status": "Above covenant"},
                {"year": 2030, "dscr": 1.48, "status": "Above covenant"},
                {"year": 2031, "dscr": 1.42, "status": "Above covenant — trough year"},
                {"year": 2032, "dscr": 1.61, "status": "Recovering"},
                {"year": 2033, "dscr": 2.38, "status": "Healthy"},
                {"year": 2035, "dscr": 2.94, "status": "Strong"},
                {"year": 2038, "dscr": 3.83, "status": "Post-refi optionality available"}
            ]
        },

        # ------------------------------------------------------------------ #
        #  MODEL STATUS AND READINESS                                          #
        # ------------------------------------------------------------------ #
        "status": {
            "model_readiness": "Investor-grade model ready",
            "lender_presentation_ready": True,
            "equity_investor_ready": True,
            "dfi_board_paper_ready": True,
            "outstanding_items": [
                "Anchor load off-take contracts (Dangote, Lekki FTZ) not yet executed — revenue line uses LOI assumptions",
                "Nigeria tax treaty confirmation pending — 25% blended rate may reduce to 22% upon confirmation",
                "WAPP ancillary services revenue assumes market operationalization by 2031 — subject to regulatory risk"
            ]
        },

        "message": (
            "Full 25-year DCF model complete for $900M Abidjan-Lagos corridor infrastructure. "
            "Core metrics: Equity IRR 15.1% (target: 14.0% ✓), Project IRR 10.3% (target: 9.0% ✓), "
            "NPV $218M at 5.66% WACC (positive ✓), Min DSCR 1.42x in Year 3 (covenant floor: 1.30x ✓). "
            "Payback period: 11.5 years. Equity multiple: 2.8x over 25-year life. "
            "Model is investor-grade and ready for DFI board submission. "
            "3 outstanding items flagged — anchor load contracts and Nigeria tax confirmation "
            "are priority actions before financial close. "
            "Proceed to `perform_risk_and_sensitivity_analysis` to stress-test these assumptions."
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