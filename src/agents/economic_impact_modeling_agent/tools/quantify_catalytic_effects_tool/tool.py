import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import CatalyticEffectsInput


@tool("quantify_catalytic_effects", description=TOOL_DESCRIPTION)
def quantify_catalytic_effects_tool(
    payload: CatalyticEffectsInput, runtime: ToolRuntime
) -> Command:
    """Calculates sector-specific growth unlocked by infrastructure."""

    # In a real-world scenario, this tool would:
    # 1. Calculate energy-cost savings for processing plants (e.g., Cocoa in Ghana).
    # 2. Model the increase in mining output enabled by reliable bulk power.
    # 3. Estimate 'Digital Economy' growth from fiber-optic co-location on power lines.

    response = {
        # ── Analysis header ────────────────────────────────────────────────────
        "corridor_id": "ABIDJAN_LAGOS_CORRIDOR_v1",
        "analysis_type": "catalytic_effects_quantification",
        "analysis_scope": "Multi-sector infrastructure unlock — Abidjan–Lagos Economic Corridor",
        "analysis_horizon_years": 20,
        "currency": "USD",

        # ── Methodology ────────────────────────────────────────────────────────
        "methodology": {
            "computation_mode": "MOCK — static demonstration values; production uses sector I-O linkage models",
            "reference_frameworks": [
                "AfDB Spatial Development Initiative (SDI) sector unlock model",
                "World Bank Infrastructure-to-Sector Linkage Framework",
                "ECOWAS Regional Agricultural Investment Plan baselines",
            ],
            "catalytic_effect_definition": (
                "Economic value created in non-infrastructure sectors "
                "directly attributable to energy reliability, cost reduction, "
                "and connectivity improvements delivered by the corridor."
            ),
            "unlock_mechanism": {
                "energy_cost_reduction": "Grid power at $0.08–0.10/kWh vs. diesel at $0.25/kWh",
                "reliability_improvement": "99%+ uptime vs. 78–85% baseline (15–20 outages/month)",
                "logistics_connectivity": "25% transport cost reduction, border friction reduction",
                "fiber_co_location": "30–40% reduction in broadband deployment cost",
            },
            "sectors_modeled": [
                "Agriculture & Agro-Processing",
                "Mining & Minerals",
                "Manufacturing & Light Industry",
                "Digital Economy & ICT",
            ],
            "key_assumptions": {
                "anchor_load_realization_rate_pct": 80,
                "ramp_up_period_years": 7,
                "domestic_value_capture_pct": 65,
                "energy_cost_saving_applied_to_opex_pct": 18,
            },
        },

        # ── Sector unlock values ───────────────────────────────────────────────
        "sector_unlock_value_usd": {

            "agriculture_agro_processing": {
                "total_unlock_value": "1.2B",
                "annual_production_value_at_maturity": "800M–1.2B",
                "primary_drivers": [
                    "Cocoa processing scale-up — Côte d'Ivoire (2.2M tonnes/yr, 70% currently exported raw)",
                    "Rice irrigation and milling — Volta Region, Ghana (100,000 ha potential)",
                    "Palm oil and cashew agro-processing — Benin coastal zone",
                    "Cold chain infrastructure enabling perishable export markets",
                ],
                "energy_requirement_mw": "260 MW (5 SAPZs at full buildout)",
                "key_interventions": [
                    "Special Agro-Industrial Processing Zones (SAPZs) — 5 sites, $1.02B investment",
                    "Solar-powered irrigation systems replacing diesel pumps",
                    "Cold storage network — 50,000–100,000 MT capacity, 15–20 facilities",
                ],
                "jobs_enabled": "82,000 direct + 120,000 indirect",
                "import_substitution_value_usd": "200M/year (rice self-sufficiency — Ghana)",
                "realization_confidence": "HIGH",
            },

            "mining_minerals": {
                "total_unlock_value": "2.4B",
                "annual_production_uplift_at_maturity": "1.5B–2.4B",
                "primary_drivers": [
                    "Obuasi Gold Mine — AngloGold Ashanti, 400,000 oz/yr; each 1% uptime gain = $5–8M",
                    "Côte d'Ivoire gold expansion — 40 tonnes/yr growing, lithium and cobalt exploration",
                    "Nigeria artisanal and small-scale mining formalization",
                    "Shared transmission spurs reducing per-mine connection cost by 40–60%",
                ],
                "energy_requirement_mw": "800–1,080 MW across 73 existing + 50–68 new operations",
                "key_interventions": [
                    "50 km 161 kV spur to Obuasi — $50–70M, payback 2–3 years",
                    "Aggregated multi-mine transmission planning reducing per-site cost",
                    "Grid reliability lifting effective capacity utilization from 85% to 99%+",
                ],
                "jobs_enabled": "45,000 direct mining + 90,000 supply chain",
                "foreign_direct_investment_attracted_usd": "10.5B–18B (4 countries, 2025–2035)",
                "realization_confidence": "HIGH",
            },

            "manufacturing": {
                "total_unlock_value": "0.9B",
                "annual_output_value_at_maturity": "600M–900M",
                "primary_drivers": [
                    "Lekki Free Trade Zone — 16,500 ha, $20B committed; reliable grid unlocks full buildout",
                    "Tema Free Zone — 200-ha expansion; hybrid solar + storage lifts capacity from 60% to 100%",
                    "Zone Industrielle Cotonou modernisation — $200–400M additional investment enabled",
                    "Port-adjacent light manufacturing at Abidjan and Lomé",
                ],
                "energy_requirement_mw": "800–1,200 MW (SEZs at full buildout by 2035)",
                "key_interventions": [
                    "Tema Free Zone hybrid solar + storage ($145M) — unlocks $500M additional zone investment",
                    "Lekki FTZ 330 kV grid tie-in ($80–120M) — redundancy enabling $20B buildout",
                    "Cotonou industrial zone 330 kV backbone ($150M) — reduces production costs 25–35%",
                ],
                "jobs_enabled": "200,000+ (Lekki FTZ alone targets 200,000 by 2035)",
                "energy_cost_saving_per_year_usd": "40–60M across all SEZs (grid vs. diesel)",
                "realization_confidence": "MEDIUM-HIGH",
            },
        },

        # ── Digital economy ────────────────────────────────────────────────────
        "digital_economy_impact": {
            "overall_rating": "HIGH",
            "rationale": "Fiber-optic backbone co-located with transmission right-of-way",
            "components": {
                "fiber_backbone": {
                    "route_km": 1080,
                    "deployment_cost_usd": "30–50M (co-located) vs. 60–90M standalone",
                    "capex_saving_pct": "30–40%",
                    "capacity": "96–144 fiber pairs, scalable",
                },
                "data_center_network": {
                    "primary_hubs": ["Abidjan", "Accra", "Lagos"],
                    "secondary_nodes": ["Lomé", "Cotonou"],
                    "edge_micro_centers": "15–20 (1–2 MW each)",
                    "total_investment_usd": "800M–1.2B",
                    "power_requirement_mw": "150–250 (high reliability)",
                    "revenue_potential_usd_per_year": "200–350M",
                },
                "bandwidth_and_connectivity": {
                    "bandwidth_cost_reduction_pct": "40–60%",
                    "5g_corridor_cities_enabled": 5,
                    "ict_jobs_created": "5,000–8,000",
                },
                "smart_corridor_systems": {
                    "intelligent_transport_systems_mw": "10–15",
                    "smart_grid_scada_fiber_enabled": True,
                    "public_wifi_and_5g_mw": "5–10",
                    "operations_center_investment_usd": "50–80M",
                },
            },
            "total_digital_investment_usd": "1.0B–1.5B",
            "annual_digital_revenue_at_maturity_usd": "240–390M",
            "ict_jobs_total": "15,000–20,000",
        },

        # ── Aggregate catalytic summary ────────────────────────────────────────
        "aggregate_catalytic_impact": {
            "total_sector_unlock_value_usd": "4.5B–5.4B",
            "enabled_investment_attracted_usd": "10B–18B",
            "gdp_multiplier_on_infrastructure_capex": "1.80–2.20x",
            "total_annual_gdp_impact_by_year_10_usd": "4.7B–7.5B",
            "total_jobs_direct_indirect_induced": "200,000–300,000",
            "sectors_ranked_by_unlock_value": [
                {"rank": 1, "sector": "Mining & Minerals",              "value_usd": "2.4B"},
                {"rank": 2, "sector": "Agriculture & Agro-Processing",  "value_usd": "1.2B"},
                {"rank": 3, "sector": "Manufacturing",                  "value_usd": "0.9B"},
                {"rank": 4, "sector": "Digital Economy",                "value_usd": "0.9B (revenue, not unlock)"},
            ],
        },

        # ── Sensitivity band ───────────────────────────────────────────────────
        "sensitivity_band_analysis": {
            "low_case": {
                "anchor_load_realization_rate_pct": 60,
                "total_sector_unlock_value_usd": "2.8B",
                "assumptions": "Delayed SEZ buildout; suppressed commodity prices; 20% higher grid costs",
            },
            "base_case": {
                "anchor_load_realization_rate_pct": 80,
                "total_sector_unlock_value_usd": "4.5B",
                "assumptions": "Current investment commitments realized on schedule",
            },
            "high_case": {
                "anchor_load_realization_rate_pct": 95,
                "total_sector_unlock_value_usd": "6.1B",
                "assumptions": "AfCFTA fully operational; accelerated mining exploration; digital economy boom",
            },
            "main_variance_drivers": [
                "Anchor load realization rate (60% impact on total unlock value)",
                "Commodity prices — gold and cocoa (25% impact)",
                "SEZ buildout pace — Lekki FTZ specifically (15% impact)",
            ],
        },

        # ── Audit metadata ─────────────────────────────────────────────────────
        "audit_metadata": {
            "version": "1.0.0-mock",
            "generator": "quantify_catalytic_effects_tool",
            "timestamp": "2026-01-26T00:00:00Z",
            "data_source": "MOCK — Corridor Intelligence Platform demo dataset",
            "validation_status": "DEMO — not validated against live data",
            "intended_use": "Stakeholder demonstration and platform UX development",
        },

        # ── Executive summary ──────────────────────────────────────────────────
        "message": (
            "Sector-specific catalytic effects quantified for the Abidjan–Lagos corridor. "
            "Infrastructure investment unlocks an estimated $4.5B–5.4B in sector value "
            "across agriculture, mining, manufacturing, and digital economy, "
            "attracting $10B–18B in downstream investment and supporting "
            "200,000–300,000 jobs by Year 10."
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