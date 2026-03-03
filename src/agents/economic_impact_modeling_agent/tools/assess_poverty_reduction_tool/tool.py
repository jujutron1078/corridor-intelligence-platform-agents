import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import PovertyReductionInput


@tool("assess_poverty_reduction", description=TOOL_DESCRIPTION)
def assess_poverty_reduction_tool(
    payload: PovertyReductionInput, runtime: ToolRuntime
) -> Command:
    """Models electricity access expansion and resulting income effects."""

    # In a real-world scenario, this tool would:
    # 1. Correlate energy access with increased household productivity hours.
    # 2. Apply income-growth coefficients to the newly electrified populations.
    # 3. Project the number of individuals crossing the $2.15/day threshold.

    response = {
        # ================================================================
        # ANALYSIS HEADER
        # ================================================================
        "corridor_id": "AL_CORRIDOR_POC_001",
        "analysis_type": "Poverty Reduction & Household Welfare Impact Assessment",
        "analysis_scope": "Electricity access + reliability-driven income effects",
        "analysis_horizon_years": 10,
        "currency": "USD",
        # ================================================================
        # METHODOLOGY (DEMO MODE, BUT PRODUCTION-STYLE)
        # ================================================================
        "methodology": {
            "computation_mode": "Hardcoded benchmark registry (demo mode)",
            "poverty_framework": {
                "primary_poverty_line": "International extreme poverty line: $2.15/day (2017 PPP)",
                "secondary_lines_supported_in_production": [
                    "$3.65/day (2017 PPP) - lower-middle income benchmark",
                    "National poverty lines (country-specific)",
                ],
                "reporting_unit": "people (headcount) and households",
            },
            "modeled_population_segments": {
                "newly_electrified_households": "Households gaining first-time reliable electricity access",
                "reliability_upgraded_households": "Households already connected but experiencing large outage reduction",
                "excluded_in_demo": [
                    "long-run human capital effects (education/health) monetization",
                    "macro GDP feedback loops (handled by GDP multiplier tool)",
                    "distribution network last-mile constraints (assumed addressed)",
                ],
            },
            "impact_channels": [
                "income uplift from productive-use activities (MSMEs, home businesses, extended working hours)",
                "energy expenditure savings (diesel/kerosene/generator fuel + maintenance displacement)",
                "reduced downtime costs for cold storage and processing micro-enterprises",
                "improved reliability for basic services (qualitative in demo mode)",
            ],
            "core_assumptions": {
                "average_household_size": 4.6,
                "baseline_poverty_rate_corridor_zone_weighted": "approx. 30–40% (varies by country and district)",
                "income_uplift_for_newly_electrified_households_avg_pct": 18,
                "income_uplift_for_reliability_upgraded_households_avg_pct": 7,
                "annual_energy_cost_savings_per_household_usd": 120,
                "poverty_transition_rate_among_affected_households_base_case": "6–10% over 10 years (benchmark)",
                "notes": [
                    "Income uplift is an average benchmark: effects are higher for enterprise households and lower for purely residential households.",
                    "Transition rates are sensitive to tariff competitiveness vs diesel and the realized reliability improvement.",
                ],
            },
        },
        # ================================================================
        # PRIMARY OUTPUT (KEEP YOUR EXISTING SHAPE)
        # ================================================================
        "poverty_reduction_impact": {
            "additional_people_electrified": 1_500_000,
            "estimated_poverty_reduction_count": 450_000,
            "avg_household_income_gain": "18%",
        },
        # ================================================================
        # PRODUCTION-GRADE DETAIL (EXTENSIONS)
        # ================================================================
        "welfare_and_poverty_detail": {
            "affected_population": {
                "newly_electrified_people": 1_500_000,
                "reliability_upgraded_people": 3_900_000,
                "total_people_directly_affected": 5_400_000,
                "households_newly_electrified_est": 326_000,
                "households_reliability_upgraded_est": 848_000,
            },
            "poverty_reduction_breakdown": {
                "people_lifted_above_2_15_line": 450_000,
                "households_lifted_above_2_15_line_est": 98_000,
                "people_near_threshold_receiving_welfare_gain_but_not_crossing": 780_000,
                "interpretation": (
                    "Approximately 450k people are estimated to move above the $2.15/day extreme poverty threshold "
                    "over the analysis horizon. A larger population experiences meaningful welfare gains "
                    "(cost savings, productivity increases) but remains below the threshold in the base case."
                ),
            },
            "income_and_cost_effects": {
                "average_household_income_uplift": {
                    "newly_electrified_households": "18% (benchmark average)",
                    "reliability_upgraded_households": "7% (benchmark average)",
                },
                "energy_cost_savings": {
                    "avg_annual_savings_per_household_usd": 120,
                    "primary_displaced_costs": [
                        "diesel generator fuel and servicing",
                        "kerosene/charcoal lighting substitution",
                        "battery charging and phone charging fees",
                        "ice purchases / spoilage losses for small vendors (partial)",
                    ],
                    "why_it_matters": (
                        "Energy spending displacement increases disposable income and reduces volatility "
                        "for poor households, supporting poverty transitions and resilience."
                    ),
                },
            },
            "pathways_to_income_gain": {
                "productive_use_examples": [
                    "barber/salon operations extending into evening hours",
                    "welding and small fabrication shops",
                    "grain milling and agro-processing micro-enterprises",
                    "refrigeration for fish/produce vendors (reduced spoilage)",
                    "phone charging, internet kiosks, and micro-retail expansion",
                ],
                "reliability_examples": [
                    "reduced interruption for clinics and schools (service continuity)",
                    "lower downtime for cold storage and processing equipment",
                    "improved safety and night-time commerce due to lighting",
                ],
            },
        },
        # ================================================================
        # DISTRIBUTION BY COUNTRY (COMMON DFI REQUIREMENT)
        # ================================================================
        "impact_by_country": {
            "cote_divoire": {
                "additional_people_electrified": 210_000,
                "people_lifted_above_2_15_line": 62_000,
                "primary_drivers": "Urban/peri-urban MSME productivity + reduced generator use around Abidjan industrial zones",
            },
            "ghana": {
                "additional_people_electrified": 480_000,
                "people_lifted_above_2_15_line": 155_000,
                "primary_drivers": "Agro-processing + irrigation productivity + SME growth in Tema/Volta catchments",
            },
            "togo": {
                "additional_people_electrified": 170_000,
                "people_lifted_above_2_15_line": 48_000,
                "primary_drivers": "Reliability improvements for SMEs and logistics services linked to Lomé",
            },
            "benin": {
                "additional_people_electrified": 160_000,
                "people_lifted_above_2_15_line": 45_000,
                "primary_drivers": "Reduced diesel dependence in Cotonou + industrial zone power stability",
            },
            "nigeria": {
                "additional_people_electrified": 480_000,
                "people_lifted_above_2_15_line": 140_000,
                "primary_drivers": "Generator displacement + SME productivity gains in Lagos-peri-urban corridor communities",
            },
        },
        # ================================================================
        # TIME PROFILE (REALISTIC RAMP-UP)
        # ================================================================
        "time_profile": {
            "electrification_rollout_people": {
                "Year_1": 120_000,
                "Year_2": 280_000,
                "Year_3": 420_000,
                "Year_4": 680_000,
            },
            "poverty_transitions_people": {
                "Year_3": 65_000,
                "Year_5": 190_000,
                "Year_7": 320_000,
                "Year_10": 450_000,
            },
            "interpretation": (
                "Poverty transitions lag electrification because households and SMEs require time to adopt appliances, "
                "stabilize income, and expand productive activities. The model assumes a 2–3 year ramp before "
                "material poverty threshold crossings accelerate."
            ),
        },
        # ================================================================
        # SENSITIVITY / CONFIDENCE BANDS
        # ================================================================
        "sensitivity_band_analysis": {
            "low_case": {
                "people_lifted_above_2_15_line": 280_000,
                "assumptions": [
                    "tariffs remain close to diesel parity (weak savings)",
                    "productive-use uptake is limited",
                    "reliability improvements are partial",
                ],
            },
            "base_case": {
                "people_lifted_above_2_15_line": 450_000,
                "assumptions": [
                    "moderate tariff advantage vs diesel",
                    "moderate productive-use adoption",
                    "reliability improvement materializes as planned",
                ],
            },
            "high_case": {
                "people_lifted_above_2_15_line": 650_000,
                "assumptions": [
                    "strong tariff advantage vs diesel",
                    "high productive-use uptake (MSME growth)",
                    "distribution upgrades support appliance adoption",
                ],
            },
            "main_variance_drivers": [
                "tariff competitiveness vs diesel and kerosene",
                "reliability improvement magnitude (outage reduction)",
                "MSME financing availability and appliance adoption rates",
                "speed of distribution/last-mile connections",
            ],
        },
        # ================================================================
        # GOVERNANCE METADATA (TRUST BUILDING)
        # ================================================================
        "audit_metadata": {
            "analysis_version": "EIM-POV-1.0-DEMO",
            "generated_by": "Economic Impact Modeling Agent",
            "generation_timestamp": "2026-02-23T10:15:00Z",
            "data_source_type": "Pre-calibrated poverty/electrification benchmark registry",
            "external_validation_status": "Not externally audited (demo mode)",
            "intended_use": "DFI concept note / early-stage impact justification",
        },
        # ================================================================
        # EXECUTIVE MESSAGE
        # ================================================================
        "message": (
            "Base-case poverty reduction estimates indicate ~450,000 people may be lifted above the "
            "$2.15/day extreme poverty line over a 10-year horizon, supported by electrification of ~1.5M "
            "people and reliability upgrades affecting an additional ~3.9M people. The average modeled "
            "household income uplift for newly electrified households is ~18%, driven by productive-use "
            "activities and energy expenditure savings. Results are sensitive to tariff competitiveness, "
            "reliability improvements, and adoption of productive appliances by MSMEs."
        ),
    }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response), tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )
