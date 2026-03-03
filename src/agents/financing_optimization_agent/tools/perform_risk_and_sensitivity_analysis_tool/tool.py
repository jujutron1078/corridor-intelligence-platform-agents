import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import RiskAnalysisInput


@tool("perform_risk_and_sensitivity_analysis", description=TOOL_DESCRIPTION)
def perform_risk_and_sensitivity_analysis_tool(
    payload: RiskAnalysisInput, runtime: ToolRuntime
) -> Command:
    """Runs 10,000 simulations to determine the probability distribution of returns."""

    # In a real-world scenario, this tool would:
    # 1. Extract all variable assumptions from the financial model (Tool 3 output).
    # 2. Define probability distributions for each variable (normal, triangular, uniform)
    #    based on historical project data from comparable African infrastructure deals.
    # 3. Run a Monte Carlo simulation with 10,000+ iterations, sampling from each
    #    distribution simultaneously using Latin Hypercube Sampling for efficiency.
    # 4. For each iteration, recompute the full DCF and record: equity IRR, project IRR,
    #    NPV, min DSCR, and payback period.
    # 5. Build a tornado diagram by running one-at-a-time sensitivity analysis:
    #    vary each input across its range while holding all others at base case.
    #    Rank variables by total IRR swing (high – low).
    # 6. Compute break-even thresholds: the minimum value each variable can take
    #    before equity IRR drops below target or DSCR breaches covenant floor.
    # 7. Flag any scenario where DSCR < 1.30x as a lender covenant breach event
    #    and report its probability.
    # 8. Produce a correlation matrix to identify which variables move together
    #    (e.g., currency devaluation + revenue shortfall often co-move in West Africa).

    response = {

        # ------------------------------------------------------------------ #
        #  SIMULATION CONFIGURATION                                            #
        #  Production: configured dynamically from variable_variances input.  #
        #  Mock: pre-set for Abidjan-Lagos $900M corridor infrastructure.     #
        # ------------------------------------------------------------------ #
        "simulation_configuration": {
            "iterations": 10_000,
            "sampling_method": "Latin Hypercube Sampling (LHS)",
            "base_case_equity_irr": "15.1%",
            "base_case_project_irr": "10.3%",
            "base_case_min_dscr": 1.42,
            "base_case_npv_usd": 218_000_000,
            "variables_modelled": 12,
            "correlation_matrix_applied": True,
            "covenant_floor_dscr": 1.30,
            "target_equity_irr": "14.0%"
        },

        # ------------------------------------------------------------------ #
        #  MONTE CARLO RESULTS                                                 #
        #  Production: computed from 10,000-iteration simulation engine.      #
        #  Mock: pre-built reflecting realistic West African project outcomes. #
        # ------------------------------------------------------------------ #
        "monte_carlo_results": {

            # --- Equity IRR Distribution ---
            "equity_irr_distribution": {
                "prob_irr_above_14_percent": "71.4%",     # Above target
                "prob_irr_above_12_percent": "88.2%",     # Above minimum acceptable
                "prob_irr_above_10_percent": "96.1%",     # Above DFI floor
                "prob_irr_below_8_percent": "1.3%",       # Tail risk
                "p10_irr": "17.8%",                       # Best 10% of outcomes
                "p50_irr": "14.9%",                       # Median outcome
                "p90_irr": "11.2%",                       # Worst 10% of outcomes
                "mean_irr": "14.6%",
                "std_deviation": "2.1%",
                "skewness": "-0.34",                      # Slight left skew — downside tail
                "interpretation": (
                    "71.4% probability of exceeding 14% target IRR. "
                    "P90 IRR of 11.2% remains above the 10% DFI floor, "
                    "indicating resilience even in adverse scenarios."
                )
            },

            # --- DSCR Distribution ---
            "dscr_distribution": {
                "prob_dscr_above_1_40x": "68.3%",
                "prob_dscr_above_1_30x": "84.7%",         # Above covenant floor
                "prob_covenant_breach": "15.3%",           # DSCR drops below 1.30x
                "p50_min_dscr": "1.41x",
                "p90_min_dscr": "1.19x",                   # Worst 10% — breaches covenant
                "mean_min_dscr": "1.44x",
                "covenant_breach_primary_driver": "Revenue shortfall >18% combined with CAPEX overrun >12%",
                "interpretation": (
                    "15.3% probability of DSCR covenant breach is above the 10% lender comfort threshold. "
                    "Credit enhancement (Tool 6) or a cash flow sweep reserve account is recommended "
                    "to bring breach probability below 8%."
                )
            },

            # --- NPV Distribution ---
            "npv_distribution": {
                "prob_npv_positive": "91.4%",
                "p50_npv_usd": 204_000_000,
                "p90_npv_usd": 48_000_000,                 # Still positive in worst decile
                "p10_npv_usd": 387_000_000,
                "mean_npv_usd": 211_000_000
            }
        },

        # ------------------------------------------------------------------ #
        #  TORNADO DIAGRAM — SENSITIVITY ANALYSIS                             #
        #  Production: computed by one-at-a-time sensitivity runs.            #
        #  Mock: ranked by IRR swing for Abidjan-Lagos base case.             #
        # ------------------------------------------------------------------ #
        "tornado_diagram": {
            "metric_analysed": "Equity IRR",
            "base_case": "15.1%",
            "note": "Variables ranked by total IRR swing (high case minus low case). Wider bar = higher impact.",
            "variables": [
                {
                    "rank": 1,
                    "variable": "Anchor Load Revenue Realization",
                    "description": "% of projected anchor load demand that materializes by Year 3",
                    "base_case_assumption": "85% realization",
                    "low_case": "60% realization",
                    "high_case": "100% realization",
                    "irr_low_case": "10.8%",
                    "irr_high_case": "17.9%",
                    "irr_swing": "7.1%",
                    "dscr_impact_low": "1.19x (covenant breach risk)",
                    "sensitivity_label": "CRITICAL",
                    "mitigation": "Secure take-or-pay off-take contracts before financial close"
                },
                {
                    "rank": 2,
                    "variable": "Construction CAPEX Overrun",
                    "description": "% cost overrun above base case $900M CAPEX",
                    "base_case_assumption": "0% overrun",
                    "low_case": "+25% overrun ($225M)",
                    "high_case": "-5% under budget (-$45M)",
                    "irr_low_case": "11.4%",
                    "irr_high_case": "15.9%",
                    "irr_swing": "4.5%",
                    "dscr_impact_low": "1.28x (near covenant breach)",
                    "sensitivity_label": "HIGH",
                    "mitigation": "Fixed-price EPC contract with performance bonds; 15% contingency reserve"
                },
                {
                    "rank": 3,
                    "variable": "Currency Devaluation (NGN/XOF vs USD)",
                    "description": "Depreciation of local currencies reduces USD-equivalent revenue",
                    "base_case_assumption": "2.5% annual depreciation",
                    "low_case": "8% annual depreciation",
                    "high_case": "0% (stable)",
                    "irr_low_case": "11.9%",
                    "irr_high_case": "16.1%",
                    "irr_swing": "4.2%",
                    "dscr_impact_low": "1.31x (just above covenant)",
                    "sensitivity_label": "HIGH",
                    "mitigation": "USD-denominated tariffs for cross-border wheeling; currency swap for NGN revenue tranche"
                },
                {
                    "rank": 4,
                    "variable": "Construction Timeline Delay",
                    "description": "Delay in commercial operations start date (months)",
                    "base_case_assumption": "0 months delay",
                    "low_case": "18-month delay",
                    "high_case": "3-month early completion",
                    "irr_low_case": "12.3%",
                    "irr_high_case": "15.6%",
                    "irr_swing": "3.3%",
                    "dscr_impact_low": "1.33x (above covenant but stressed)",
                    "sensitivity_label": "HIGH",
                    "mitigation": "Phased construction aligned with highway corridor; liquidated damages in EPC contract"
                },
                {
                    "rank": 5,
                    "variable": "Commercial Interest Rate (SOFR)",
                    "description": "Movement in SOFR base rate affecting commercial debt tranche",
                    "base_case_assumption": "SOFR = 5.3% (current)",
                    "low_case": "SOFR + 200bps = 7.3%",
                    "high_case": "SOFR - 150bps = 3.8%",
                    "irr_low_case": "13.1%",
                    "irr_high_case": "16.2%",
                    "irr_swing": "3.1%",
                    "dscr_impact_low": "1.36x",
                    "sensitivity_label": "MEDIUM",
                    "mitigation": "Interest rate swap to fix commercial debt rate at financial close"
                },
                {
                    "rank": 6,
                    "variable": "Transmission Tariff Level",
                    "description": "Regulated wheeling tariff set by national utility regulators",
                    "base_case_assumption": "$0.021/kWh blended",
                    "low_case": "$0.015/kWh (-29%)",
                    "high_case": "$0.026/kWh (+24%)",
                    "irr_low_case": "13.0%",
                    "irr_high_case": "16.8%",
                    "irr_swing": "3.8%",
                    "dscr_impact_low": "1.32x",
                    "sensitivity_label": "MEDIUM",
                    "mitigation": "Lock in cost-reflective tariff methodology in concession agreements before construction"
                },
                {
                    "rank": 7,
                    "variable": "OPEX Escalation",
                    "description": "Annual operating cost growth rate above base 2.5%",
                    "base_case_assumption": "2.5% per annum",
                    "low_case": "5.0% per annum",
                    "high_case": "1.5% per annum",
                    "irr_low_case": "14.1%",
                    "irr_high_case": "15.6%",
                    "irr_swing": "1.5%",
                    "dscr_impact_low": "1.39x",
                    "sensitivity_label": "LOW",
                    "mitigation": "Long-term O&M contracts with indexed caps; in-house maintenance capability"
                },
                {
                    "rank": 8,
                    "variable": "Inflation Rate (West Africa)",
                    "description": "Regional inflation affecting local cost base",
                    "base_case_assumption": "4.5% blended",
                    "low_case": "8.0%",
                    "high_case": "2.5%",
                    "irr_low_case": "14.3%",
                    "irr_high_case": "15.5%",
                    "irr_swing": "1.2%",
                    "dscr_impact_low": "1.40x",
                    "sensitivity_label": "LOW",
                    "mitigation": "USD-denominated contracts for major equipment and EPC"
                }
            ]
        },

        # ------------------------------------------------------------------ #
        #  BREAK-EVEN ANALYSIS                                                 #
        #  Production: computed by binary search on each variable.            #
        #  Mock: pre-calculated thresholds for critical variables.            #
        # ------------------------------------------------------------------ #
        "break_even_analysis": {
            "metric": "Equity IRR = 14.0% (target floor)",
            "thresholds": [
                {
                    "variable": "Anchor Load Revenue Realization",
                    "break_even_value": "71% realization",
                    "headroom_from_base": "14 percentage points below base (85%)",
                    "interpretation": "Revenue can fall 14pp below base before IRR target is missed"
                },
                {
                    "variable": "CAPEX Overrun",
                    "break_even_value": "+19% overrun ($171M)",
                    "headroom_from_base": "$171M buffer above base CAPEX",
                    "interpretation": "Project tolerates up to $171M cost overrun before missing IRR target"
                },
                {
                    "variable": "Construction Delay",
                    "break_even_value": "14-month delay",
                    "headroom_from_base": "14 months before IRR target missed",
                    "interpretation": "Standard EPC buffer but tight — early completion incentives recommended"
                },
                {
                    "variable": "Transmission Tariff",
                    "break_even_value": "$0.017/kWh",
                    "headroom_from_base": "19% below base tariff of $0.021/kWh",
                    "interpretation": "Tariff can be cut 19% before IRR target is missed — moderate buffer"
                }
            ],
            "dscr_covenant_break_even": {
                "metric": "Min DSCR = 1.30x (covenant floor)",
                "revenue_shortfall_threshold": "Revenue must not fall below 72% of base case in any single year",
                "combined_stress_threshold": "CAPEX overrun >12% AND revenue shortfall >10% simultaneously triggers breach",
                "probability_of_combined_stress": "8.4% — above 5% lender comfort level"
            }
        },

        # ------------------------------------------------------------------ #
        #  CORRELATION MATRIX — KEY VARIABLE PAIRS                            #
        #  Production: computed from historical West African project data.    #
        #  Mock: pre-assessed for corridor-specific co-movement risks.        #
        # ------------------------------------------------------------------ #
        "correlation_risks": {
            "note": "Correlated variables that move together amplify downside scenarios beyond single-variable analysis.",
            "high_correlation_pairs": [
                {
                    "variable_a": "Currency Devaluation",
                    "variable_b": "Anchor Load Revenue Shortfall",
                    "correlation": 0.68,
                    "explanation": "Currency crises in West Africa historically reduce industrial output and therefore power demand simultaneously",
                    "combined_downside_irr": "9.4%",
                    "risk_level": "HIGH"
                },
                {
                    "variable_a": "Construction Delay",
                    "variable_b": "CAPEX Overrun",
                    "correlation": 0.72,
                    "explanation": "Delays almost always accompany cost overruns in African infrastructure — same root causes (permitting, logistics)",
                    "combined_downside_irr": "10.1%",
                    "risk_level": "HIGH"
                },
                {
                    "variable_a": "SOFR Rate Increase",
                    "variable_b": "Currency Devaluation",
                    "correlation": 0.55,
                    "explanation": "USD strengthening periods coincide with local currency weakness, raising debt cost while compressing local revenue",
                    "combined_downside_irr": "11.8%",
                    "risk_level": "MEDIUM"
                }
            ]
        },

        # ------------------------------------------------------------------ #
        #  CRITICAL RISKS SUMMARY                                             #
        #  Production: ranked by probability × impact (expected loss).        #
        #  Mock: pre-ranked for Abidjan-Lagos corridor risk profile.          #
        # ------------------------------------------------------------------ #
        "critical_risks": [
            {
                "rank": 1,
                "risk": "Anchor load revenue realization below 71%",
                "probability": "22%",
                "irr_impact": "-4.3% on equity IRR",
                "dscr_impact": "Potential covenant breach if below 65%",
                "severity": "CRITICAL",
                "mitigation": "Execute take-or-pay off-take contracts with Dangote, Lekki FTZ, and Obuasi Mine before financial close. These 3 alone cover 38% of Year 1 revenue."
            },
            {
                "rank": 2,
                "risk": "CAPEX overrun exceeding 19% ($171M)",
                "probability": "18%",
                "irr_impact": "-2.8% on equity IRR",
                "dscr_impact": "1.28x min DSCR — near covenant breach",
                "severity": "HIGH",
                "mitigation": "Fixed-price lump-sum EPC contract with 10% performance bond. Retain 15% contingency in reserve account."
            },
            {
                "rank": 3,
                "risk": "NGN/XOF currency devaluation >8% annually",
                "probability": "24%",
                "irr_impact": "-3.2% on equity IRR",
                "dscr_impact": "1.31x min DSCR — just above covenant",
                "severity": "HIGH",
                "mitigation": "Structure cross-border wheeling tariffs in USD. Arrange currency swap for NGN revenue tranche with a local commercial bank."
            },
            {
                "rank": 4,
                "risk": "Construction delay >14 months",
                "probability": "31%",
                "irr_impact": "-1.9% on equity IRR",
                "dscr_impact": "Interest during construction increases, equity injection timing impacted",
                "severity": "HIGH",
                "mitigation": "Phased construction strategy — Phase 1 segments serve highest anchor load density first, generating early revenue."
            },
            {
                "rank": 5,
                "risk": "Regulatory tariff review reduces wheeling rate below $0.017/kWh",
                "probability": "14%",
                "irr_impact": "-2.1% on equity IRR",
                "dscr_impact": "1.33x min DSCR",
                "severity": "MEDIUM",
                "mitigation": "Lock in cost-reflective tariff methodology in concession agreements with all 5 national regulators before financial close."
            },
            {
                "rank": 6,
                "risk": "Political risk — expropriation or contract renegotiation in 1+ countries",
                "probability": "8%",
                "irr_impact": "Potentially catastrophic in isolated country",
                "dscr_impact": "Depends on affected country's revenue share",
                "severity": "MEDIUM",
                "mitigation": "MIGA political risk insurance for all 5 countries. ICSID arbitration clause in concession agreements. Multi-country structure reduces single-country exposure."
            }
        ],

        # ------------------------------------------------------------------ #
        #  RECOMMENDED ACTIONS BEFORE FINANCIAL CLOSE                         #
        # ------------------------------------------------------------------ #
        "pre_financial_close_actions": [
            {
                "priority": 1,
                "action": "Execute take-or-pay off-take contracts with top 3 anchor loads",
                "target_coverage": "Minimum 55% of Year 1 projected revenue under contract",
                "responsible": "Commercial Development Team",
                "deadline": "Before financial close — non-negotiable for lender sign-off"
            },
            {
                "priority": 2,
                "action": "Procure MIGA political risk insurance for all 5 corridor countries",
                "target_coverage": "$270M commercial debt tranche",
                "responsible": "Financing Team",
                "deadline": "Month 6 — required for commercial lender credit approval"
            },
            {
                "priority": 3,
                "action": "Execute interest rate swap on commercial debt tranche",
                "target": "Fix SOFR component to lock in current rate environment",
                "responsible": "Treasury / Financial Advisor",
                "deadline": "At financial close"
            },
            {
                "priority": 4,
                "action": "Establish 6-month debt service reserve account (DSRA)",
                "amount_usd": 38_000_000,
                "rationale": "Reduces covenant breach probability from 15.3% to ~6.8%",
                "responsible": "Financing Team",
                "deadline": "At financial close — standard lender requirement"
            },
            {
                "priority": 5,
                "action": "Negotiate USD-denominated tariff clauses for cross-border segments",
                "target": "Eliminate local currency revenue exposure for Togo–Nigeria segments",
                "responsible": "Legal and Regulatory Team",
                "deadline": "Before concession agreements are signed"
            }
        ],

        "message": (
            "Risk and sensitivity analysis complete across 12 variables with 10,000 Monte Carlo iterations. "
            "Base case equity IRR: 15.1%. Probability of exceeding 14% target: 71.4%. P90 IRR: 11.2% — "
            "above 10% DFI floor in worst decile. "
            "CRITICAL FLAG: DSCR covenant breach probability is 15.3% — above the 10% lender comfort threshold. "
            "Primary driver: anchor load revenue shortfall below 72% of base case. "
            "Top risk: Anchor load realization (IRR swing of 7.1%) — "
            "take-or-pay contracts covering 55%+ of Year 1 revenue must be executed before financial close. "
            "Correlated risk alert: Currency devaluation + revenue shortfall co-movement (r=0.68) "
            "creates a combined downside IRR of 9.4% — USD tariff structuring is critical. "
            "Proceed to `optimize_debt_terms` to sculpt repayment profile to reduce trough-year DSCR stress, "
            "then `model_credit_enhancement` to address the 15.3% covenant breach probability."
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