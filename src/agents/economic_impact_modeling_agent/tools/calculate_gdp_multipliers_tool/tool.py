import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import GDPMultiplierInput


@tool("calculate_gdp_multipliers", description=TOOL_DESCRIPTION)
def calculate_gdp_multipliers_tool(
    payload: GDPMultiplierInput, runtime: ToolRuntime
) -> Command:
    """
    Generates a detailed macroeconomic impact assessment
    for corridor infrastructure CAPEX.

    NOTE:
    This demo version uses pre-calibrated benchmark values.
    No real-time economic computation is performed.
    """

    response = {

        # ================================================================
        # ANALYSIS HEADER
        # ================================================================
        "corridor_id": "AL_CORRIDOR_POC_001",
        "analysis_type": "Macroeconomic Multiplier Impact Assessment",
        "analysis_scope": "Construction Phase Economic Effects Only",
        "analysis_horizon_years": 4,
        "currency": "USD",

        # ================================================================
        # METHODOLOGY FRAMEWORK
        # ================================================================
        "methodology": {
            "model_type": "Regional Input-Output Benchmark Model (Simulated)",
            "reference_frameworks": [
                "AfDB West Africa I-O Tables 2023",
                "ECOWAS Regional Economic Accounts 2024",
                "World Bank Infrastructure Multiplier Meta-Study 2022"
            ],
            "multiplier_basis": "Infrastructure Construction — Transmission & Grid Assets",
            "import_leakage_treatment": "Embedded within calibrated multiplier",
            "domestic_value_capture_assumption": "Approx. 68% of CAPEX retained regionally",
            "computation_mode": "Pre-calibrated deterministic benchmark (demo mode)"
        },

        # ================================================================
        # MULTIPLIER STRUCTURE
        # ================================================================
        "multiplier_structure": {
            "direct_effect_multiplier": 1.00,
            "indirect_effect_multiplier": 0.74,
            "induced_effect_multiplier": 0.44,
            "total_regional_multiplier": 2.18,
            "benchmark_range_west_africa": "1.9x – 2.4x",
            "positioning_within_range": "Mid-upper quartile (high regional integration)"
        },

        # ================================================================
        # CONSOLIDATED GDP IMPACT
        # ================================================================
        "gdp_impact_summary": {
            "gross_capex_reference_usd": 938_904_000,
            "total_gdp_impact_usd": 2_047_000_000,
            "average_annual_gdp_impact_usd": 511_750_000,
            "peak_year_impact_usd": 612_000_000,
            "share_of_regional_gdp_pct": "0.38% cumulative uplift across corridor economies"
        },

        # ================================================================
        # IMPACT BREAKDOWN (ABSOLUTE VALUES)
        # ================================================================
        "impact_breakdown_usd": {
            "direct_effects": {
                "construction_wages": 624_000_000,
                "engineering_services": 118_000_000,
                "local_material_supply": 142_000_000,
                "subtotal_direct": 884_000_000
            },
            "indirect_effects": {
                "cement_and_steel_supply_chain": 328_000_000,
                "transport_and_logistics": 182_000_000,
                "equipment_maintenance_services": 96_000_000,
                "industrial_support_services": 88_000_000,
                "subtotal_indirect": 694_000_000
            },
            "induced_effects": {
                "household_consumption_expansion": 347_000_000,
                "retail_and_services_uplift": 86_000_000,
                "housing_and_local_construction": 36_000_000,
                "subtotal_induced": 469_000_000
            }
        },

        # ================================================================
        # IMPACT DISTRIBUTION BY COUNTRY
        # ================================================================
        "impact_by_country": {
            "cote_divoire": {
                "gdp_impact_usd": 341_000_000,
                "pct_of_total": "16.7%",
                "primary_drivers": "Western backbone segment construction + Vridi upgrade"
            },
            "ghana": {
                "gdp_impact_usd": 756_000_000,
                "pct_of_total": "36.9%",
                "primary_drivers": "Backbone + Obuasi spur + Tema industrial hub"
            },
            "togo": {
                "gdp_impact_usd": 228_000_000,
                "pct_of_total": "11.1%",
                "primary_drivers": "Lomé hub + industrial ring reinforcement"
            },
            "benin": {
                "gdp_impact_usd": 212_000_000,
                "pct_of_total": "10.3%",
                "primary_drivers": "Cotonou hub + eastern backbone works"
            },
            "nigeria": {
                "gdp_impact_usd": 510_000_000,
                "pct_of_total": "24.9%",
                "primary_drivers": "Lekki 400kV hub + Lagos underground works"
            }
        },

        # ================================================================
        # SECTORAL GDP CONTRIBUTION
        # ================================================================
        "sectoral_gdp_contribution": {
            "construction_and_civil_works": "43%",
            "manufacturing_and_materials": "21%",
            "transport_and_logistics": "11%",
            "professional_services": "9%",
            "retail_and_household_services": "8%",
            "energy_and_utilities_support": "8%"
        },

        # ================================================================
        # MACROECONOMIC EFFECTS
        # ================================================================
        "macroeconomic_transmission_channels": {
            "investment_component_gdp": "Strong short-term uplift (Infrastructure CAPEX injection)",
            "consumption_component_gdp": "Moderate induced household demand expansion",
            "industrial_capacity_utilization": "Increased steel and cement plant load factors",
            "cross_border_value_chains": "Strengthened regional supply interlinkages"
        },

        # ================================================================
        # RISK & SENSITIVITY
        # ================================================================
        "sensitivity_band_analysis": {
            "low_case_multiplier": 1.95,
            "high_case_multiplier": 2.35,
            "low_case_total_gdp_usd": 1_830_000_000,
            "high_case_total_gdp_usd": 2_206_000_000,
            "variance_driver": "Import leakage + labor intensity variation"
        },

        # ================================================================
        # AUDIT & GOVERNANCE METADATA
        # ================================================================
        "audit_metadata": {
            "analysis_version": "EIM-1.0-DEMO",
            "generated_by": "Economic Impact Modeling Agent",
            "generation_timestamp": "2026-02-23T10:15:00Z",
            "data_source_type": "Pre-calibrated corridor economic benchmark registry",
            "external_validation_status": "Not externally audited (demo mode)",
            "intended_use": "Strategic corridor planning and DFI concept validation"
        },

        # ================================================================
        # EXECUTIVE MESSAGE
        # ================================================================
        "message": (
            "Construction-phase CAPEX of $939M generates an estimated "
            "$2.05B in total GDP impact across corridor economies "
            "using a 2.18x regional infrastructure multiplier. "
            "Direct construction accounts for 43% of total impact, "
            "with significant indirect supply chain activation in steel, cement, "
            "and logistics. Ghana captures the largest share (36.9%) due to "
            "backbone concentration and industrial anchor loads. "
            "Sensitivity analysis indicates total GDP impact range "
            "of $1.83B–$2.21B depending on import leakage and labor intensity."
        ),
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