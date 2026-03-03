import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import RegionalIntegrationInput


@tool("model_regional_integration", description=TOOL_DESCRIPTION)
def model_regional_integration_tool(
    payload: RegionalIntegrationInput, runtime: ToolRuntime
) -> Command:
    """Models the impact on cross-border trade and market integration."""

    # In a real-world scenario, this tool would:
    # 1. Use Gravity Models to predict increased trade flows between Abidjan and Lagos.
    # 2. Model the impact of synchronized infrastructure on cross-border utility trading.
    # 3. Quantify the reduction in 'Trade Friction' across the 5 corridor countries.

    response = {
        # ── Analysis header ────────────────────────────────────────────────────
        "corridor_id": "ABIDJAN_LAGOS_CORRIDOR_v1",
        "analysis_type": "regional_integration_modeling",
        "analysis_scope": (
            "Cross-border trade, energy market integration, and market "
            "harmonisation across 5 ECOWAS corridor nations"
        ),
        "analysis_horizon_years": 20,
        "currency": "USD",

        # ── Methodology ────────────────────────────────────────────────────────
        "methodology": {
            "computation_mode": "MOCK — static demonstration values; production uses "
                                "Gravity Model trade flow engine + WAPP energy dispatch model",
            "reference_frameworks": [
                "Anderson-van Wincoop Gravity Model (bilateral trade flows)",
                "ECOWAS Regional Electricity Market (REM) integration framework",
                "World Bank Trade Facilitation and Logistics Performance Index",
                "AfDB African Regional Integration Index (ARII)",
                "AfSEM (African Single Electricity Market) connectivity benchmarks",
            ],
            "trade_friction_components_modeled": [
                "Physical transport cost reduction (highway + border crossings)",
                "Energy cost convergence across corridor countries",
                "Regulatory and standards harmonisation (AfCFTA alignment)",
                "Border crossing time reduction (5 modern facilities planned)",
                "Informal trade formalisation (mobile payments + digital corridor ID)",
            ],
            "energy_integration_components_modeled": [
                "Cross-border electricity wheeling capacity (330–400 kV backbone)",
                "WAPP dispatch optimisation (Ghana surplus → Togo/Benin deficit)",
                "Renewable energy pooling (Nzema Solar + Akosombo hydro balancing)",
                "Real-time grid balancing across 5 national systems",
            ],
            "key_assumptions": {
                "baseline_intra_ecowas_trade_usd": "22.6B (2024 estimate)",
                "transport_cost_reduction_pct": 25,
                "border_crossing_time_reduction_pct": 40,
                "energy_price_convergence_years": 7,
                "informal_trade_formalisation_rate_pct": 30,
                "afsem_adoption_timeline_years": 10,
            },
        },

        # ── Headline integration score ─────────────────────────────────────────
        "regional_integration_score": {
            "composite_score": 0.88,
            "score_interpretation": "Very High — corridor addresses structural barriers "
                                    "across all 5 ARII dimensions",
            "score_components": {
                "trade_integration":          {"score": 0.91, "weight_pct": 25},
                "infrastructure_integration": {"score": 0.94, "weight_pct": 25},
                "productive_integration":     {"score": 0.85, "weight_pct": 20},
                "financial_integration":      {"score": 0.79, "weight_pct": 15},
                "social_integration":         {"score": 0.82, "weight_pct": 15},
            },
            "benchmark_comparison": {
                "current_ecowas_arii_score": 0.51,
                "corridor_projected_score":  0.88,
                "improvement_vs_baseline":   "+73%",
                "top_performing_rec_benchmark": "EAC (0.54) — corridor would exceed by 63%",
            },
        },

        # ── Trade flow projections ─────────────────────────────────────────────
        "trade_flow_projections": {
            "baseline_intra_corridor_trade_usd": "8.4B/year (2024)",
            "projected_trade_volume_increase_pct": "32%",
            "projected_intra_corridor_trade_usd": "11.1B/year (by Year 7)",
            "additional_trade_value_usd": "2.7B/year",

            "trade_increase_by_driver": {
                "transport_cost_reduction":       {"contribution_pct": 38, "value_usd": "1.03B/year"},
                "border_friction_reduction":      {"contribution_pct": 27, "value_usd": "0.73B/year"},
                "energy_cost_convergence":        {"contribution_pct": 20, "value_usd": "0.54B/year"},
                "informal_trade_formalisation":   {"contribution_pct": 15, "value_usd": "0.40B/year"},
            },

            "trade_increase_by_country_pair": [
                {
                    "pair": "Nigeria ↔ Ghana",
                    "baseline_usd": "3.1B",
                    "projected_usd": "4.2B",
                    "increase_pct": "35%",
                    "primary_commodities": ["petroleum products", "cocoa", "manufactured goods"],
                },
                {
                    "pair": "Nigeria ↔ Côte d'Ivoire",
                    "baseline_usd": "1.8B",
                    "projected_usd": "2.4B",
                    "increase_pct": "33%",
                    "primary_commodities": ["refined oil", "cashew", "industrial inputs"],
                },
                {
                    "pair": "Ghana ↔ Côte d'Ivoire",
                    "baseline_usd": "1.4B",
                    "projected_usd": "1.9B",
                    "increase_pct": "36%",
                    "primary_commodities": ["cocoa", "electricity", "agro-processing outputs"],
                },
                {
                    "pair": "Togo & Benin ↔ All partners",
                    "baseline_usd": "2.1B",
                    "projected_usd": "2.6B",
                    "increase_pct": "24%",
                    "primary_commodities": ["transit logistics", "pineapple", "cotton"],
                    "note": "Smaller absolute gain but highest proportional development impact",
                },
            ],

            "gravity_model_elasticities": {
                "transport_cost_elasticity":  -0.82,
                "border_time_elasticity":     -0.61,
                "energy_cost_elasticity":     -0.44,
                "gdp_growth_elasticity":       1.23,
            },
        },

        # ── Energy market integration ──────────────────────────────────────────
        "energy_market_integration": {
            "cross_border_electricity_trade": {
                "year_1_gwh": 1500,
                "year_5_gwh": 4000,
                "year_10_gwh": 8500,
                "trade_value_year_5_usd": "150–200M/year",
                "trade_value_year_10_usd": "320–425M/year",
            },

            "energy_security_improvement": {
                "togo_import_dependency_reduction_pct": 45,
                "benin_import_dependency_reduction_pct": 42,
                "outage_frequency_reduction_togo_benin_pct": "40–60%",
                "grid_reliability_uplift": "78–85% → 99%+ uptime",
            },

            "renewable_energy_pooling": {
                "nzema_solar_export_potential_mw": 100,
                "akosombo_hydro_balancing_mw": "200–400",
                "regional_renewable_share_increase_pct": 12,
                "carbon_reduction_ktco2_per_year": 850,
            },

            "afsem_alignment": {
                "contribution_to_afsem_goals": "HIGH",
                "wapp_interconnection_strengthened": True,
                "cross_pool_links_enabled": ["WAPP ↔ CAPP (via Nigeria-Benin node)"],
                "market_harmonisation_milestones": [
                    "Year 3 — bilateral wheeling agreements operational",
                    "Year 6 — corridor-wide spot market pilot",
                    "Year 10 — full WAPP dispatch optimisation online",
                ],
            },
        },

        # ── Trade facilitation ─────────────────────────────────────────────────
        "trade_facilitation_impact": {
            "border_crossing_improvements": {
                "facilities_upgraded": 5,
                "average_crossing_time_hours_before": 18.4,
                "average_crossing_time_hours_after": 4.2,
                "reduction_pct": "77%",
                "annual_logistics_cost_saving_usd": "340M",
            },
            "transport_cost_reduction": {
                "average_cost_per_km_before_usd": 0.12,
                "average_cost_per_km_after_usd": 0.09,
                "reduction_pct": "25%",
                "annual_freight_saving_usd": "620M",
            },
            "digital_trade_infrastructure": {
                "single_window_customs_enabled": True,
                "electronic_cargo_tracking": True,
                "sme_digital_marketplace_access": "15,000+ businesses",
                "informal_trade_formalised_usd": "400M/year",
            },
        },

        # ── Country-level integration gains ───────────────────────────────────
        "impact_by_country": [
            {
                "country": "Nigeria",
                "integration_gain_usd": "1.1B/year",
                "primary_benefit": "Export market expansion for petroleum products and manufactured goods",
                "energy_role": "Net exporter — Egbin surplus wheeled to Benin (200–300 MW)",
                "afsem_role": "Eastern anchor — largest grid on corridor",
            },
            {
                "country": "Ghana",
                "integration_gain_usd": "620M/year",
                "primary_benefit": "Electricity export revenue + agro-processing trade growth",
                "energy_role": "Hub exporter — Akosombo hydro + Nzema solar",
                "afsem_role": "Central hub connecting Francophone and Anglophone blocs",
            },
            {
                "country": "Côte d'Ivoire",
                "integration_gain_usd": "540M/year",
                "primary_benefit": "Cocoa and cashew value-chain integration into regional market",
                "energy_role": "Net exporter — CIPREL + Azito combined 986 MW hub",
                "afsem_role": "Western anchor — gateway to CAPP interconnect",
            },
            {
                "country": "Benin",
                "integration_gain_usd": "280M/year",
                "primary_benefit": "Transit logistics formalisation + import cost reduction",
                "energy_role": "Net importer — reliability improvement 40–60% outage reduction",
                "afsem_role": "Transit node — Cotonou port as regional logistics hub",
            },
            {
                "country": "Togo",
                "integration_gain_usd": "160M/year",
                "primary_benefit": "Port of Lomé competitiveness + industrial zone growth",
                "energy_role": "Net importer — greatest proportional energy security gain",
                "afsem_role": "Transit node — Lomé as deepwater transshipment hub",
            },
        ],

        # ── Time profile ───────────────────────────────────────────────────────
        "time_profile": {
            "year_1_to_3": {
                "trade_increase_pct": "8–12%",
                "energy_trade_gwh": 1500,
                "key_milestones": [
                    "Phase 1 highway segments operational",
                    "2 border crossings upgraded",
                    "Abidjan–Tema 330 kV segment energised",
                ],
            },
            "year_4_to_7": {
                "trade_increase_pct": "20–27%",
                "energy_trade_gwh": 4000,
                "key_milestones": [
                    "Full transmission backbone operational",
                    "All 5 border crossings upgraded",
                    "WAPP bilateral wheeling agreements active",
                    "AfCFTA corridor preferential tariffs applied",
                ],
            },
            "year_8_to_20": {
                "trade_increase_pct": "32–45%",
                "energy_trade_gwh": "8,500–12,000",
                "key_milestones": [
                    "Full AfSEM corridor node integration",
                    "Digital single market for corridor trade",
                    "Renewable energy pooling at scale",
                    "Corridor becomes top-5 regional trade route globally",
                ],
            },
            "interpretation": (
                "Integration gains are back-loaded — physical infrastructure "
                "delivers early wins but regulatory harmonisation and market "
                "maturation drive the larger gains in Years 4–10."
            ),
        },

        # ── Sensitivity band ───────────────────────────────────────────────────
        "sensitivity_band_analysis": {
            "low_case": {
                "trade_volume_increase_pct": "18%",
                "energy_trade_year_5_gwh": 2200,
                "regional_integration_score": 0.71,
                "assumptions": (
                    "AfCFTA implementation delayed 3 years; "
                    "Nigeria grid constraints persist; "
                    "border digitalisation slow rollout"
                ),
            },
            "base_case": {
                "trade_volume_increase_pct": "32%",
                "energy_trade_year_5_gwh": 4000,
                "regional_integration_score": 0.88,
                "assumptions": "Current policy trajectory; on-schedule infrastructure delivery",
            },
            "high_case": {
                "trade_volume_increase_pct": "47%",
                "energy_trade_year_5_gwh": 5800,
                "regional_integration_score": 0.94,
                "assumptions": (
                    "AfCFTA fully operational by Year 3; "
                    "digital customs single window adopted by all 5 countries; "
                    "Dangote refinery petroleum exports accelerate"
                ),
            },
            "main_variance_drivers": [
                "AfCFTA implementation pace (35% of variance)",
                "Nigeria grid reform and export policy (28% of variance)",
                "Border digitalisation rollout speed (22% of variance)",
                "Commodity price cycles — cocoa, gold, oil (15% of variance)",
            ],
        },

        # ── Strategic alignment ────────────────────────────────────────────────
        "strategic_alignment": {
            "ecowas_vision_2050":   "DIRECT — corridor is flagship ECOWAS infrastructure project",
            "afcfta_alignment":     "HIGH — reduces NTBs, enables intra-Africa manufactured goods trade",
            "afsem_contribution":   "HIGH — WAPP backbone strengthening, cross-pool links enabled",
            "pida_alignment":       "DIRECT — listed Programme for Infrastructure Development in Africa project",
            "sdg_contributions":    ["SDG 7 (Clean Energy)", "SDG 8 (Decent Work)", "SDG 9 (Industry & Infrastructure)", "SDG 10 (Reduced Inequalities)", "SDG 17 (Partnerships)"],
            "eu_global_gateway":    "ELIGIBLE — regional integration + energy security criteria met",
        },

        # ── Audit metadata ─────────────────────────────────────────────────────
        "audit_metadata": {
            "version": "1.0.0-mock",
            "generator": "model_regional_integration_tool",
            "timestamp": "2026-01-26T00:00:00Z",
            "data_source": "MOCK — Corridor Intelligence Platform demo dataset",
            "validation_status": "DEMO — not validated against live trade data",
            "intended_use": "Stakeholder demonstration and platform UX development",
        },

        # ── Executive summary ──────────────────────────────────────────────────
        "message": (
            "Regional integration benefits projected for all 5 ECOWAS corridor members. "
            "Composite integration score of 0.88 — 73% above current ECOWAS baseline. "
            "Intra-corridor trade projected to grow 32% (+$2.7B/year) by Year 7, driven by "
            "25% transport cost reduction, 77% border crossing time reduction, and "
            "1,500–8,500 GWh/year in cross-border electricity trade. "
            "Nigeria and Ghana are the primary beneficiaries by value; "
            "Togo and Benin see the highest proportional development impact."
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