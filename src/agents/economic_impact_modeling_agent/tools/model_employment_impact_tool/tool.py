import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import EmploymentModelingInput


@tool("model_employment_impact", description=TOOL_DESCRIPTION)
def model_employment_impact_tool(
    payload: EmploymentModelingInput, runtime: ToolRuntime
) -> Command:
    """Estimates job creation across construction and operations phases."""

    # In a real-world scenario, this tool would:
    # 1. Estimate direct construction jobs based on labor-to-CAPEX ratios.
    # 2. Project 'Enabled' jobs in the 57 anchor loads (e.g., workers needed for a new mine).
    # 3. Use employment elasticities to calculate 'Induced' jobs in the local service economy.

    response = {
        # ================================================================
        # ANALYSIS HEADER
        # ================================================================
        "corridor_id": "AL_CORRIDOR_POC_001",
        "analysis_type": "Employment Impact Assessment",
        "analysis_scope": "Construction + Operations + Enabled Industry + Induced Employment",
        "analysis_horizon_years": 20,
        "construction_period_years": 4,
        "post_commissioning_years_modeled": 16,
        "currency": "USD",
        # ================================================================
        # METHODOLOGY & ASSUMPTIONS (DFI-STYLE)
        # ================================================================
        "methodology": {
            "computation_mode": "Hardcoded benchmark registry (demo mode)",
            "job_accounting_units": {
                "construction": "person_years + peak_headcount",
                "operations": "ongoing_FTE_jobs",
                "enabled_industry": "ongoing_FTE_jobs (ramped over time)",
                "induced": "ongoing_FTE_jobs (linked to wage + demand effects)",
            },
            "definitions": {
                "direct_construction_jobs": "Workers hired directly for corridor asset engineering, civil works, erection, and installation (temporary).",
                "direct_operational_jobs": "Permanent staff for O&M: line patrol, substation ops, SCADA control, vegetation management, safety, security.",
                "enabled_industrial_jobs": "Jobs created in anchor loads and zones that become viable/expand because of improved power reliability and capacity.",
                "induced_jobs": "Jobs created in the local service economy due to new household income and business spending.",
            },
            "core_reference_benchmarks": [
                "AfDB infrastructure employment benchmarks (illustrative registry)",
                "World Bank transport & energy job multipliers (illustrative registry)",
                "ECOWAS labor market structure (illustrative registry)",
            ],
            "key_model_assumptions": {
                "local_labor_share_pct": 83,
                "domestic_procurement_share_pct": 68,
                "contractor_mechanization_level": "medium",
                "skills_availability_constraint": "moderate (requires training pipeline for HV technicians)",
                "enabled_jobs_realization_rate": "Base case assumes 75% of identified anchor load expansions materialize by Year 10",
            },
            "important_notes": [
                "Construction jobs are temporary and reported as peak headcount + person-years (not permanent jobs).",
                "Enabled and induced jobs are dependent on power reliability, tariff competitiveness, and complementary policies (SEZ governance, logistics, permits).",
                "This is a demo output using pre-calibrated corridor benchmarks; not an audited forecast.",
            ],
        },
        # ================================================================
        # EMPLOYMENT SUMMARY (KEEP YOUR EXISTING SHAPE)
        # ================================================================
        "employment_summary": {
            # Keep your existing keys, but now they’re clearly interpreted.
            "direct_construction_jobs": 75000,
            "direct_operational_jobs": 12000,
            "enabled_industrial_jobs": 145000,
            "induced_jobs": 68000,
        },
        # ================================================================
        # TOTALS
        # ================================================================
        "total_jobs_created": 300000,
        # ================================================================
        # BREAKDOWNS THAT MAKE IT “PRODUCTION-READY”
        # ================================================================
        "breakdowns": {
            # ---------- Construction details ----------
            "direct_construction_detail": {
                "peak_headcount_jobs": 8200,
                "total_person_years": 24500,
                "time_profile_peak_years": ["Year 2", "Year 3"],
                "job_families": {
                    "civil_works_and_right_of_way": 31000,
                    "tower_erection_and_line_stringing": 16500,
                    "substation_construction_and_installation": 12000,
                    "engineering_project_management_hse": 8500,
                    "security_and_site_support": 7000,
                },
                "notes": [
                    "Peak headcount represents maximum simultaneous construction employment, not annual total.",
                    "Person-years represent cumulative construction labor demand over the build period.",
                ],
            },
            # ---------- Operations details ----------
            "direct_operations_detail": {
                "ongoing_FTE_jobs": 12000,
                "operations_job_families": {
                    "grid_operations_control_SCADA": 1200,
                    "substation_operations_and_maintenance": 2600,
                    "transmission_line_maintenance_and_patrol": 2400,
                    "vegetation_management_and_right_of_way": 1900,
                    "security_and_asset_protection": 2400,
                    "commercial_metering_and_customer_interface": 500,
                    "administration_procurement_compliance": 1000,
                },
                "reliability_uptime_assumption": "High-priority backbone with strengthened O&M",
                "notes": [
                    "Operations staffing includes both utility-side and contracted O&M services.",
                    "Security staffing is higher than global averages due to corridor asset exposure.",
                ],
            },
            # ---------- Enabled jobs details ----------
            "enabled_industrial_detail": {
                "enabled_job_sources": {
                    "special_economic_zones_and_industrial_parks": 54000,
                    "ports_and_logistics": 22000,
                    "mining_operations_and_processing": 32000,
                    "agro_processing_and_cold_chain": 25000,
                    "data_centers_and_digital_services": 12000,
                },
                "anchor_load_dependency": {
                    "baseline_anchor_loads_identified": "45-57 sites (ports, SEZs, mines, agro-processing, data centers, refineries)",
                    "power_reliability_threshold": "Enabled growth assumes >99% reliability for critical industrial loads",
                    "tariff_competitiveness_requirement": "Growth assumes tariffs competitive vs diesel generation alternative",
                },
                "ramp_profile": {
                    "year_1_to_3_realized_pct": 20,
                    "year_4_to_7_realized_pct": 55,
                    "year_8_to_10_realized_pct": 75,
                    "year_11_to_20_realized_pct": 90,
                },
                "notes": [
                    "Enabled jobs are scenario-dependent and require complementary investments (distribution, last-mile, industrial policy)."
                ],
            },
            # ---------- Induced jobs details ----------
            "induced_detail": {
                "induced_job_sources": {
                    "retail_trade_and_markets": 21000,
                    "transport_services_informal_and_formal": 15000,
                    "housing_and_local_construction": 9000,
                    "food_services_and_hospitality": 11000,
                    "education_health_and_social_services": 7000,
                    "small_business_services": 5000,
                },
                "income_transmission_logic": {
                    "primary_driver": "Household spending increases driven by construction wages + enabled industry payroll",
                    "local_multiplier_condition": "Higher induced jobs in districts with strong SME ecosystems and access to finance",
                },
            },
        },
        # ================================================================
        # DISTRIBUTION BY COUNTRY (COMMON DFI ASK)
        # ================================================================
        "impact_by_country": {
            "cote_divoire": {
                "share_pct": 17,
                "direct_construction_jobs": 12000,
                "direct_operational_jobs": 1800,
                "enabled_industrial_jobs": 24000,
                "induced_jobs": 10500,
                "primary_drivers": "Abidjan energy hub works + port-industrial activity",
            },
            "ghana": {
                "share_pct": 37,
                "direct_construction_jobs": 26000,
                "direct_operational_jobs": 3600,
                "enabled_industrial_jobs": 52000,
                "induced_jobs": 22000,
                "primary_drivers": "Tema industrial hub + Volta agriculture + mining spurs",
            },
            "togo": {
                "share_pct": 11,
                "direct_construction_jobs": 8000,
                "direct_operational_jobs": 1200,
                "enabled_industrial_jobs": 15000,
                "induced_jobs": 7000,
                "primary_drivers": "Lomé logistics platform + corridor reinforcement",
            },
            "benin": {
                "share_pct": 10,
                "direct_construction_jobs": 7000,
                "direct_operational_jobs": 1100,
                "enabled_industrial_jobs": 14000,
                "induced_jobs": 6000,
                "primary_drivers": "Cotonou industrial zone + port modernization effects",
            },
            "nigeria": {
                "share_pct": 25,
                "direct_construction_jobs": 22000,
                "direct_operational_jobs": 4300,
                "enabled_industrial_jobs": 40000,
                "induced_jobs": 22500,
                "primary_drivers": "Lagos/Lekki industrial cluster + refinery and FTZ expansion",
            },
        },
        # ================================================================
        # SKILLS & INCLUSION (OPTIONAL BUT VERY DFI)
        # ================================================================
        "skills_and_inclusion": {
            "construction_skill_split_pct": {
                "skilled": 28,
                "semi_skilled": 34,
                "unskilled": 38,
            },
            "operations_skill_split_pct": {
                "skilled": 55,
                "semi_skilled": 35,
                "unskilled": 10,
            },
            "localization_and_capacity_building": {
                "training_required_roles": [
                    "HV line technicians",
                    "substation protection engineers",
                    "SCADA operators",
                    "HSE supervisors",
                ],
                "recommended_training_programs": [
                    "Apprenticeship programs with utilities and EPCs",
                    "Regional training centers for high-voltage maintenance",
                    "Safety certification pipeline",
                ],
            },
            "gender_lens": {
                "gender_tracking_status": "Not estimated in demo mode",
                "implementation_note": "In production, require EPC workforce reporting and apply sectoral female participation baselines.",
            },
        },
        # ================================================================
        # TIME PROFILE (WHAT DECISION-MAKERS ASK FIRST)
        # ================================================================
        "time_profile": {
            "construction_phase_peak_jobs_by_year": {
                "Year_1": 1200,
                "Year_2": 7800,
                "Year_3": 8200,
                "Year_4": 5600,
            },
            "operations_phase_FTE_by_year": {
                "Year_5": 3000,
                "Year_6": 8000,
                "Year_7": 12000,
                "Year_8_to_20": 12000,
            },
            "enabled_jobs_realization_path": {
                "Year_3": 15000,
                "Year_5": 55000,
                "Year_7": 95000,
                "Year_10": 145000,
                "Year_20": 165000,
            },
            "interpretation": (
                "Construction employment peaks in Years 2–3, then declines as civil works finish. "
                "Operations roles ramp up after commissioning. Enabled industrial employment ramps over "
                "a 10-year horizon as anchor loads expand and new investments reach maturity."
            ),
        },
        # ================================================================
        # RISK & SENSITIVITY (MAKES IT TRUSTWORTHY)
        # ================================================================
        "sensitivity_band_analysis": {
            "low_case": {
                "enabled_jobs_realization_rate": "55% by Year 10",
                "total_jobs_created": 225000,
                "main_downside_drivers": [
                    "delays in industrial park buildout",
                    "tariffs remain uncompetitive vs diesel",
                    "grid reliability improvements lag",
                ],
            },
            "base_case": {
                "enabled_jobs_realization_rate": "75% by Year 10",
                "total_jobs_created": 300000,
            },
            "high_case": {
                "enabled_jobs_realization_rate": "90% by Year 10",
                "total_jobs_created": 385000,
                "main_upside_drivers": [
                    "accelerated SEZ investments",
                    "faster cross-border power trade",
                    "large anchor loads sign long-term off-take early",
                ],
            },
        },
        # ================================================================
        # AUDIT METADATA (PRODUCTION READINESS)
        # ================================================================
        "audit_metadata": {
            "analysis_version": "EIM-EMP-1.0-DEMO",
            "generated_by": "Economic Impact Modeling Agent",
            "generation_timestamp": "2026-02-23T10:15:00Z",
            "data_source_type": "Pre-calibrated corridor benchmark registry",
            "external_validation_status": "Not externally audited (demo mode)",
            "intended_use": "Strategic corridor planning and DFI concept validation",
        },
        # ================================================================
        # EXECUTIVE MESSAGE (SHORT + DFI FRIENDLY)
        # ================================================================
        "message": (
            "Employment projection indicates ~300,000 total jobs supported across corridor economies, "
            "including ~75,000 direct construction jobs (temporary), ~12,000 ongoing operational jobs, "
            "~145,000 enabled industrial jobs driven by anchor load expansion, and ~68,000 induced jobs "
            "in the local service economy. Construction employment peaks in Years 2–3, while enabled "
            "industrial employment ramps over a 10-year horizon depending on reliability and tariff competitiveness."
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
