import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import ScenarioAnalysisInput


@tool("perform_impact_scenario_analysis", description=TOOL_DESCRIPTION)
def perform_impact_scenario_analysis_tool(
    payload: ScenarioAnalysisInput, runtime: ToolRuntime
) -> Command:
    """Compares baseline vs project development trajectories."""

    # In a real-world scenario, this tool would:
    # 1. Run Monte Carlo simulations for 'No Project' vs 'With Project' scenarios.
    # 2. Visualize the 'GDP Delta' over a 20-year lifecycle analysis.
    # 3. Calculate the Opportunity Cost of non-investment.

    response = {
        # ── Analysis header ────────────────────────────────────────────────────
        "corridor_id": "ABIDJAN_LAGOS_CORRIDOR_v1",
        "analysis_type": "impact_scenario_analysis",
        "analysis_scope": (
            "20-year counterfactual comparison — Business as Usual vs. "
            "Enhanced Development trajectory across 5 ECOWAS corridor nations"
        ),
        "analysis_horizon_years": 20,
        "currency": "USD",

        # ── Methodology ────────────────────────────────────────────────────────
        "methodology": {
            "computation_mode": (
                "MOCK — static demonstration values; production uses "
                "Monte Carlo simulation (10,000 iterations) + Dynamic CGE model"
            ),
            "reference_frameworks": [
                "World Bank Computable General Equilibrium (CGE) infrastructure model",
                "AfDB Long-Term Economic Projection Framework (LTEPF)",
                "IMF Regional Economic Outlook — Sub-Saharan Africa baselines",
                "ECOWAS Vision 2050 growth trajectory benchmarks",
            ],
            "scenario_definitions": {
                "baseline_bau": (
                    "Business as Usual — no corridor infrastructure investment. "
                    "Existing national grids, fragmented transport, "
                    "current border friction, no regional energy market."
                ),
                "enhanced_development": (
                    "Full corridor investment — $2.6–3.4B infrastructure package "
                    "comprising grid interconnection backbone, distributed solar + storage, "
                    "and digital platform. Full anchor load realisation by Year 7."
                ),
            },
            "variables_modeled": [
                "GDP growth trajectory (national + regional)",
                "Employment (direct, indirect, induced)",
                "Poverty headcount ($2.15/day line)",
                "Electricity access and reliability",
                "Intra-regional trade volume",
                "Sector output (mining, agriculture, manufacturing, digital)",
                "Foreign direct investment attraction",
                "Government fiscal revenue",
            ],
            "monte_carlo_parameters": {
                "iterations": 10000,
                "variables_varied": 18,
                "key_stochastic_inputs": [
                    "Anchor load realization rate (60–100%)",
                    "GDP baseline growth rate (±1.5%)",
                    "Construction cost variance (±25%)",
                    "Commodity price cycles — gold, cocoa, oil (±30%)",
                    "Exchange rate volatility (±15%)",
                    "AfCFTA implementation pace (2–8 year range)",
                    "Climate risk — hydrology impact on Akosombo (±20% output)",
                ],
            },
            "confidence_interval": "95%",
        },

        # ── Scenario comparison — headline ────────────────────────────────────
        "scenario_comparison": {

            "gdp_growth_trajectory": {
                "baseline_bau_20yr_cagr":        "4.2%",
                "enhanced_development_20yr_cagr": "6.8%",
                "delta_percentage_points":         2.6,
                "interpretation": (
                    "The 2.6pp annual growth uplift compounds significantly — "
                    "by Year 20 the corridor economies are 68% larger under "
                    "Enhanced Development than under BAU."
                ),
            },

            "cumulative_gdp_delta": {
                "year_5_usd":  "12.4B",
                "year_10_usd": "47.2B",
                "year_20_usd": "198.6B",
                "annual_value_add_at_year_10_usd": "7.5B",
                "note": (
                    "Cumulative delta represents the total additional economic "
                    "output generated across all 5 countries vs. BAU over the period."
                ),
            },

            "opportunity_cost_of_non_investment": {
                "gdp_foregone_by_year_10_usd": "47.2B",
                "jobs_foregone_by_year_10":    "180,000–240,000",
                "people_remaining_in_poverty_vs_project": "2.1M additional",
                "electricity_access_gap_maintained_people": "8.4M",
                "trade_value_unrealised_usd": "18.9B cumulative",
                "interpretation": (
                    "Every year of delay in investment decision costs the corridor "
                    "economies an estimated $4.7B in foregone GDP and "
                    "perpetuates energy poverty for 8.4M people."
                ),
            },
        },

        # ── GDP detail by scenario ─────────────────────────────────────────────
        "gdp_analysis": {

            "baseline_bau": {
                "description": "No infrastructure investment. Fragmented national development.",
                "corridor_gdp_year_0_usd": "485B",
                "corridor_gdp_year_10_usd": "714B",
                "corridor_gdp_year_20_usd": "1.05T",
                "growth_drivers": [
                    "Organic population growth and demographic dividend",
                    "Commodity exports (oil, gold, cocoa) at current efficiency",
                    "Incremental urban consumption growth",
                ],
                "growth_constraints": [
                    "Persistent energy deficit — 40–60% of industrial potential unrealised",
                    "High logistics costs suppressing intra-regional trade",
                    "Limited FDI due to infrastructure risk premium",
                    "Power outages costing corridor economies est. 2–4% GDP/year",
                ],
            },

            "enhanced_development": {
                "description": "Full corridor investment realised by Year 7.",
                "corridor_gdp_year_0_usd": "485B",
                "corridor_gdp_year_10_usd": "761B",
                "corridor_gdp_year_20_usd": "1.75T",
                "growth_drivers": [
                    "Industrial electrification unlocking 940–3,880 MW anchor load demand",
                    "32% intra-corridor trade volume increase ($2.7B/year additional)",
                    "Mining sector FDI of $10.5–18B (reliable bulk power)",
                    "Agricultural value-chain deepening — cocoa, rice, palm oil",
                    "Digital economy growth — $240–390M/year by Year 5",
                    "SEZ full buildout — Lekki (200,000 jobs), Tema, Cotonou",
                ],
                "key_inflection_points": [
                    "Year 2 — First transmission segment (Abidjan–Tema) energised; SEZ growth accelerates",
                    "Year 4 — Full backbone operational; WAPP energy trading begins at scale",
                    "Year 7 — Anchor load portfolio fully realised; GDP delta peaks at $7.5B/year",
                    "Year 10 — Digital platform at maturity; AfSEM integration drives compounding gains",
                ],
            },

            "gdp_by_country_year_10": [
                {
                    "country": "Nigeria",
                    "bau_gdp_usd": "468B",
                    "enhanced_gdp_usd": "512B",
                    "delta_usd": "44B",
                    "delta_pct": "9.4%",
                    "primary_growth_source": "Dangote/Lekki industrial cluster + petroleum export expansion",
                },
                {
                    "country": "Ghana",
                    "bau_gdp_usd": "112B",
                    "enhanced_gdp_usd": "128B",
                    "delta_usd": "16B",
                    "delta_pct": "14.3%",
                    "primary_growth_source": "Electricity export revenue + mining output + agro-processing",
                },
                {
                    "country": "Côte d'Ivoire",
                    "bau_gdp_usd": "98B",
                    "enhanced_gdp_usd": "111B",
                    "delta_usd": "13B",
                    "delta_pct": "13.3%",
                    "primary_growth_source": "Cocoa value-chain deepening + grid export revenue",
                },
                {
                    "country": "Benin",
                    "bau_gdp_usd": "24B",
                    "enhanced_gdp_usd": "29B",
                    "delta_usd": "5B",
                    "delta_pct": "20.8%",
                    "primary_growth_source": "Energy import cost reduction + transit logistics formalisation",
                },
                {
                    "country": "Togo",
                    "bau_gdp_usd": "12B",
                    "enhanced_gdp_usd": "15B",
                    "delta_usd": "3B",
                    "delta_pct": "25.0%",
                    "primary_growth_source": "Port of Lomé competitiveness + industrial zone growth",
                    "note": "Highest proportional GDP gain — currently most constrained by energy deficit",
                },
            ],
        },

        # ── Employment comparison ──────────────────────────────────────────────
        "employment_comparison": {
            "baseline_bau_jobs_created_by_year_10":    "420,000",
            "enhanced_development_jobs_by_year_10":    "620,000–660,000",
            "additional_jobs_vs_bau":                  "200,000–240,000",
            "jobs_delta_breakdown": {
                "direct_infrastructure_jobs":  "3,500–5,000 (construction + O&M)",
                "mining_sector_jobs":          "45,000–55,000",
                "agro_processing_jobs":        "82,000–95,000",
                "manufacturing_sez_jobs":      "60,000–80,000 (Lekki, Tema, Cotonou)",
                "digital_ict_jobs":            "15,000–20,000",
                "induced_jobs":                "80,000–100,000",
            },
            "quality_metrics": {
                "formal_sector_share_pct":   62,
                "female_employment_share_pct": 38,
                "youth_employment_share_pct":  54,
                "average_wage_uplift_vs_bau_pct": 22,
            },
        },

        # ── Poverty and welfare comparison ────────────────────────────────────
        "poverty_welfare_comparison": {
            "baseline_bau": {
                "people_below_2_15_line_year_10": "38.2M",
                "electrification_rate_corridor_pct": 54,
                "average_household_energy_cost_pct_income": 11.2,
            },
            "enhanced_development": {
                "people_below_2_15_line_year_10": "36.1M",
                "electrification_rate_corridor_pct": 71,
                "average_household_energy_cost_pct_income": 7.4,
            },
            "delta": {
                "people_lifted_above_poverty_line": "2.1M",
                "additional_people_electrified":    "8.4M",
                "household_energy_cost_saving_pct": "34%",
                "average_household_income_gain_usd_per_year": 340,
            },
        },

        # ── Sector output comparison ──────────────────────────────────────────
        "sector_output_comparison_year_10": {
            "mining": {
                "bau_annual_output_usd":      "18.4B",
                "enhanced_annual_output_usd": "21.8B",
                "delta_usd":                   "3.4B",
                "delta_pct":                   "18.5%",
            },
            "agriculture_agro_processing": {
                "bau_annual_output_usd":      "42.1B",
                "enhanced_annual_output_usd": "49.6B",
                "delta_usd":                   "7.5B",
                "delta_pct":                   "17.8%",
            },
            "manufacturing": {
                "bau_annual_output_usd":      "28.3B",
                "enhanced_annual_output_usd": "35.2B",
                "delta_usd":                   "6.9B",
                "delta_pct":                   "24.4%",
            },
            "digital_economy": {
                "bau_annual_output_usd":      "8.6B",
                "enhanced_annual_output_usd": "13.4B",
                "delta_usd":                   "4.8B",
                "delta_pct":                   "55.8%",
                "note": "Highest percentage gain — digital economy most sensitive to connectivity improvement",
            },
        },

        # ── Monte Carlo risk profile ───────────────────────────────────────────
        "monte_carlo_risk_profile": {
            "confidence_interval": "95%",
            "gdp_delta_year_10_distribution": {
                "p10_usd": "28.4B",
                "p25_usd": "36.1B",
                "p50_usd": "47.2B",
                "p75_usd": "58.9B",
                "p90_usd": "71.3B",
                "mean_usd": "47.8B",
            },
            "probability_of_positive_gdp_delta": "99.2%",
            "probability_gdp_delta_exceeds_10b_year_10": "94.7%",
            "probability_gdp_delta_exceeds_30b_year_10": "71.3%",
            "downside_scenario_floor": {
                "worst_5pct_gdp_delta_usd": "18.1B",
                "conditions": (
                    "Simultaneous: 60% anchor load realisation + commodity price crash "
                    "+ 3-year AfCFTA delay + Nigeria grid reform stall"
                ),
            },
            "tornado_diagram_top_5_drivers": [
                {"rank": 1, "variable": "Anchor load realization rate",      "pct_of_irr_variance": 38},
                {"rank": 2, "variable": "Commodity price cycle (gold/cocoa)", "pct_of_irr_variance": 22},
                {"rank": 3, "variable": "AfCFTA implementation pace",         "pct_of_irr_variance": 17},
                {"rank": 4, "variable": "Construction cost variance",         "pct_of_irr_variance": 13},
                {"rank": 5, "variable": "Exchange rate volatility",           "pct_of_irr_variance": 10},
            ],
        },

        # ── Sensitivity bands ──────────────────────────────────────────────────
        "sensitivity_band_analysis": {
            "low_case": {
                "enhanced_20yr_cagr": "5.4%",
                "gdp_delta_year_10_usd": "28.4B",
                "jobs_delta_year_10": "120,000",
                "people_lifted_from_poverty": "900,000",
                "assumptions": (
                    "60% anchor load realisation; commodity price downturn; "
                    "AfCFTA delay 5 years; construction cost overrun 20%"
                ),
            },
            "base_case": {
                "enhanced_20yr_cagr": "6.8%",
                "gdp_delta_year_10_usd": "47.2B",
                "jobs_delta_year_10": "200,000–240,000",
                "people_lifted_from_poverty": "2.1M",
                "assumptions": "Current investment commitments; on-schedule delivery; base commodity prices",
            },
            "high_case": {
                "enhanced_20yr_cagr": "8.1%",
                "gdp_delta_year_10_usd": "71.3B",
                "jobs_delta_year_10": "310,000",
                "people_lifted_from_poverty": "3.4M",
                "assumptions": (
                    "95% anchor load realisation; AfCFTA fully operational Year 3; "
                    "commodity price boom; digital economy exceeds projections"
                ),
            },
        },

        # ── Investment decision summary ────────────────────────────────────────
        "investment_decision_summary": {
            "total_infrastructure_investment_usd": "2.6B–3.4B",
            "cumulative_gdp_return_20yr_usd": "198.6B",
            "return_on_investment_ratio": "58–76x (cumulative GDP / CAPEX)",
            "breakeven_year": "Year 4 (cumulative GDP delta exceeds total CAPEX)",
            "dfi_recommendation": "STRONG BUY — highest risk-adjusted development return in WAPP pipeline",
            "urgency_flag": (
                "HIGH — each year of delay costs $4.7B in foregone GDP "
                "and perpetuates energy poverty for 8.4M people. "
                "2027 construction start is the critical path milestone."
            ),
        },

        # ── Audit metadata ─────────────────────────────────────────────────────
        "audit_metadata": {
            "version": "1.0.0-mock",
            "generator": "perform_impact_scenario_analysis_tool",
            "timestamp": "2026-01-26T00:00:00Z",
            "data_source": "MOCK — Corridor Intelligence Platform demo dataset",
            "upstream_tool_inputs": [
                "calculate_gdp_multipliers",
                "model_employment_impact",
                "assess_poverty_reduction",
                "quantify_catalytic_effects",
                "model_regional_integration",
            ],
            "validation_status": "DEMO — not validated against live macro data",
            "intended_use": "Stakeholder demonstration and platform UX development",
        },

        # ── Executive summary ──────────────────────────────────────────────────
        "message": (
            "Comparative impact analysis complete. "
            "Enhanced Development trajectory delivers a 2.6pp annual GDP growth uplift "
            "over BAU (6.8% vs 4.2%), generating $47.2B in additional corridor GDP by Year 10 "
            "and $198.6B cumulatively over 20 years — a 58–76x return on the $2.6–3.4B investment. "
            "The project lifts 2.1M people above the $2.15/day poverty line, "
            "electrifies 8.4M additional people, and creates 200,000–240,000 jobs vs. BAU. "
            "Monte Carlo analysis confirms 99.2% probability of positive GDP delta. "
            "Togo and Benin show the highest proportional gains (25% and 21% GDP uplift). "
            "Every year of delay costs the corridor $4.7B in foregone output."
        ),
    }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response, indent=2),
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )