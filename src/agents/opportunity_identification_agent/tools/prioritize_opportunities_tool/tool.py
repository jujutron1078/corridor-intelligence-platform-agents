import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION


@tool("prioritize_opportunities", description=TOOL_DESCRIPTION)
def prioritize_opportunities_tool(
    payload: dict, runtime: ToolRuntime
) -> Command:
    """
    Final synthesis tool for the Opportunity Identification Agent.

    Synthesizes outputs from all five upstream tools into a ranked,
    phased action plan for infrastructure investment:

        scan_anchor_loads        → WHO each facility is
        calculate_current_demand → HOW MUCH power, HOW CONSISTENTLY, HOW CRITICALLY
        assess_bankability       → CAN WE TRUST THEM to pay for 20+ years
        model_growth_trajectory  → HOW MUCH will they need in 20 years
        economic_gap_analysis    → WHERE is infrastructure failing the corridor

    Scoring methodology (weighted MCDA):
        Bankability tier     35% — no bankability = no financing
        Current demand MW    25% — immediate revenue services debt
        Growth trajectory    20% — long-term NPV drives equity returns
        Gap severity         15% — strategic importance to corridor
        Cluster multiplier    5% — shared infrastructure savings

    Phase assignment criteria:
        Phase 1 — Tier 1 bankability + Critical/High gap + current MW ≥ 18
                   OR part of cluster with combined demand ≥ 50 MW
        Phase 2 — Tier 1/2 bankability + clear credit enhancement path
                   + current MW ≥ 10 OR addressable demand ≥ 50 MW
        Phase 3 — Tier 3 / identity unresolved / conditional growth
                   Cannot commit until verification or licence conditions met

    Anchor loads ranked: 24 (all from scan_anchor_loads pipeline)
    Gaps referenced: 14 (all from economic_gap_analysis)
    Generation assets and substations excluded throughout.

    This tool does NOT return:
        - Route geometry           → infrastructure_optimization_agent
        - Detailed financial model → financing_optimization_agent
        - Tariff structures        → financing_optimization_agent
        - Environmental analysis   → geospatial_intelligence_agent
    """

    response = {
        "corridor_id": "AL_CORRIDOR_POC_001",
        "total_anchors_ranked": 24,
        "scoring_methodology": {
            "bankability_weight": 0.35,
            "current_demand_weight": 0.25,
            "growth_trajectory_weight": 0.20,
            "gap_severity_weight": 0.15,
            "cluster_multiplier_weight": 0.05,
            "score_range": "0–100",
        },

        # ================================================================
        # RANKED PRIORITY LIST
        # ================================================================
        "priority_list": [

            # ============================================================
            # PHASE 1 — ANCHOR & DE-RISK (Years 1–3)
            # Highest bankability + largest current demand + Critical gaps
            # These anchors generate revenue from Day 1 and anchor debt
            # ============================================================

            {
                "rank": 1,
                "anchor_id": "AL_ANC_027",
                "detection_id": "DET-027",
                "name": "Dangote Refinery",
                "sector": "Energy",
                "sub_sector": "Petroleum Refinery & Petrochemical",
                "country": "Nigeria",
                "phase": "Phase 1",
                "gaps_addressed": ["GAP_003"],  # Lekki 330kV capacity gap
                "composite_score": 97.8,
                "score_breakdown": {
                    "bankability_score": 96.0,    # Tier 1, 0.96
                    "demand_score": 99.0,          # 1,000 MW — highest on corridor
                    "growth_score": 92.0,          # 1,000 → 1,800 MW by Year 20
                    "gap_severity_score": 99.0,    # GAP_003 Critical — 885 MW unmet
                    "cluster_score": 99.0,         # Anchors Lekki cluster
                },
                "current_mw": 1000.0,
                "year_5_mw": 1350.0,
                "year_10_mw": 1600.0,
                "bankability_tier": "Tier 1",
                "bankability_score": 0.96,
                "reliability_class": "Critical",
                "load_factor": 0.92,
                "rationale": (
                    "Dominant anchor on the entire corridor — no other single facility "
                    "comes close in demand scale, bankability, or strategic importance. "
                    "1,000 MW current demand growing to 1,800 MW by Year 20. "
                    "Dangote Industries corporate guarantee eliminates credit risk. "
                    "Currently operates on expensive captive gas generation ($25–35M/year "
                    "above grid cost) — very high motivation to sign immediately. "
                    "Critical reliability class — refinery shutdown risks $24M/day "
                    "production loss, making this the strongest PPA motivation on the corridor. "
                    "Anchors GAP_003 (Lekki 330kV hub) which also serves Lekki FTZ "
                    "and Lekki Deep Sea Port — cluster multiplier makes hub "
                    "investment dramatically stronger."
                ),
                "recommended_action": (
                    "Immediate PPA negotiation — target 20-year take-or-pay agreement. "
                    "Dangote corporate guarantee as primary security. "
                    "400kV dedicated transmission hub at Lekki Peninsula, "
                    "Phase 1A: 500 MW capacity ($145M). "
                    "Phase 1B: upgrade to 2,500 MW by Year 5 aligned with FTZ buildout ($235M). "
                    "Co-locate with Dangote access road — 18% CAPEX reduction. "
                    "Bundle with Lekki FTZ (Rank 2) and Lekki Deep Sea Port (Rank 3) "
                    "into single Lekki Cluster PPA package."
                ),
                "estimated_annual_revenue_usd_m": 95.0,
                "phase_capex_contribution_usd_m": 380.0,
            },

            {
                "rank": 2,
                "anchor_id": "AL_ANC_028",
                "detection_id": "DET-028",
                "name": "Lekki Free Trade Zone",
                "sector": "Industrial",
                "sub_sector": "Special Economic Zone",
                "country": "Nigeria",
                "phase": "Phase 1",
                "gaps_addressed": ["GAP_003"],  # Lekki 330kV capacity gap
                "composite_score": 94.2,
                "score_breakdown": {
                    "bankability_score": 88.0,    # Tier 1, 0.88
                    "demand_score": 88.0,          # 150 MW current, 1,200 MW at buildout
                    "growth_score": 99.0,          # 10.8% CAGR — highest committed growth
                    "gap_severity_score": 99.0,    # GAP_003 Critical
                    "cluster_score": 99.0,         # Part of Lekki cluster
                },
                "current_mw": 150.0,
                "year_5_mw": 420.0,
                "year_10_mw": 750.0,
                "bankability_tier": "Tier 1",
                "bankability_score": 0.88,
                "reliability_class": "Critical",
                "load_factor": 0.74,
                "rationale": (
                    "$20B+ committed Chinese sovereign investment — "
                    "dual sovereign guarantee pathway (Chinese state + Lagos State). "
                    "Currently at only 34% buildout — 66% of committed investment still incoming. "
                    "Highest CAGR of any confirmed anchor (10.8%) — "
                    "150 MW today becomes 1,200 MW at full buildout. "
                    "Adjacent to Dangote Refinery — shared Lekki hub infrastructure "
                    "means this anchor is essentially free to add once GAP_003 is addressed. "
                    "Full buildout creates 200,000 jobs — highest regional impact on corridor."
                ),
                "recommended_action": (
                    "Bundle into Lekki Cluster PPA alongside Dangote and Lekki Port. "
                    "LFZDC as PPA counterparty with Chinese sovereign co-signature. "
                    "Shared 400kV hub from Rank 1 investment. "
                    "Phase load commitment: 150 MW Year 1, 420 MW Year 5, 750 MW Year 10. "
                    "Phased tariff structure tied to zone buildout milestones."
                ),
                "estimated_annual_revenue_usd_m": 14.0,
                "phase_capex_contribution_usd_m": 0.0,
                # Note: CAPEX attributed to GAP_003 Lekki hub — shared with Rank 1
            },

            {
                "rank": 3,
                "anchor_id": "AL_ANC_029",
                "detection_id": "DET-029",
                "name": "Lekki Deep Sea Port",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics",
                "country": "Nigeria",
                "phase": "Phase 1",
                "gaps_addressed": ["GAP_003"],  # Lekki 330kV capacity gap
                "composite_score": 91.8,
                "score_breakdown": {
                    "bankability_score": 87.0,    # Tier 1, 0.87
                    "demand_score": 72.0,          # 35 MW
                    "growth_score": 88.0,          # 7.2% CAGR
                    "gap_severity_score": 99.0,    # GAP_003 Critical
                    "cluster_score": 99.0,         # Lekki cluster
                },
                "current_mw": 35.0,
                "year_5_mw": 60.0,
                "year_10_mw": 88.0,
                "bankability_tier": "Tier 1",
                "bankability_score": 0.87,
                "reliability_class": "Critical",
                "load_factor": 0.82,
                "rationale": (
                    "Tolaram / CMA CGM JV — investment-grade operators with "
                    "45-year concession providing very long revenue horizon. "
                    "Fully operational since 2024 — immediate revenue from Day 1. "
                    "Dangote Refinery supply chains generate growing cargo volumes "
                    "compounding port demand. "
                    "Shares Lekki hub with Dangote and Lekki FTZ — "
                    "CAPEX is already justified by Ranks 1 and 2. "
                    "This anchor is essentially incremental revenue on existing infrastructure."
                ),
                "recommended_action": (
                    "Include in Lekki Cluster PPA bundle. "
                    "Tolaram / CMA CGM corporate guarantee. "
                    "Dedicated feeder from Lekki hub — no additional backbone CAPEX. "
                    "20-year take-or-pay aligned with 45-year concession term."
                ),
                "estimated_annual_revenue_usd_m": 3.5,
                "phase_capex_contribution_usd_m": 0.0,
                # Note: CAPEX attributed to GAP_003 Lekki hub
            },

            {
                "rank": 4,
                "anchor_id": "AL_ANC_030",
                "detection_id": "DET-030",
                "name": "MainOne Data Center (MDX-i Lagos)",
                "sector": "Digital",
                "sub_sector": "Data Center — Tier III/IV",
                "country": "Nigeria",
                "phase": "Phase 1",
                "gaps_addressed": ["GAP_014"],  # Lagos digital cluster grid readiness
                "composite_score": 91.2,
                "score_breakdown": {
                    "bankability_score": 95.0,    # Tier 1, 0.95 — Equinix S&P 500
                    "demand_score": 65.0,          # 18 MW — modest but highly certain
                    "growth_score": 99.0,          # 10.8% CAGR, 18 → 140 MW by Year 20
                    "gap_severity_score": 72.0,    # GAP_014 Medium
                    "cluster_score": 88.0,         # Lagos digital cluster
                },
                "current_mw": 18.0,
                "year_5_mw": 42.0,
                "year_10_mw": 72.0,
                "bankability_tier": "Tier 1",
                "bankability_score": 0.95,
                "reliability_class": "Critical",
                "load_factor": 0.95,
                "rationale": (
                    "Equinix (NASDAQ, S&P 500) is the strongest digital credit on the corridor. "
                    "99.982% uptime SLA means they will sign a long PPA immediately — "
                    "internal Equinix standard procedure. "
                    "Current diesel backup costs $4–6M/year — "
                    "immediate and quantifiable motivation to sign. "
                    "Expansion confirmed (floor space doubling) — "
                    "10.8% CAGR makes this the highest long-term value digital anchor. "
                    "Phase 1 because Equinix's S&P 500 credit needs no enhancement "
                    "and contract can be executed within 90 days of decision."
                ),
                "recommended_action": (
                    "Immediate PPA negotiation — Equinix has standard PPA templates. "
                    "N+1 dual grid feed from Lekki hub and Omotosho grid point. "
                    "100ms automatic changeover — mandatory for Tier III/IV SLA. "
                    "Bundle with Rank 5 (Apapa Port) for shared Lagos backbone segment. "
                    "20-year PPA with 5-year extension options aligned with expansion phases."
                ),
                "estimated_annual_revenue_usd_m": 1.8,
                "phase_capex_contribution_usd_m": 65.0,
            },

            {
                "rank": 5,
                "anchor_id": "AL_ANC_031",
                "detection_id": "DET-031",
                "name": "Apapa Port Complex",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics",
                "country": "Nigeria",
                "phase": "Phase 1",
                "gaps_addressed": ["GAP_003"],  # Lagos transmission
                "composite_score": 88.5,
                "score_breakdown": {
                    "bankability_score": 82.0,    # Tier 1, 0.82
                    "demand_score": 85.0,          # 55 MW
                    "growth_score": 78.0,          # 3.9% CAGR — steady
                    "gap_severity_score": 92.0,    # Part of Lagos Critical gap
                    "cluster_score": 85.0,         # Lagos cluster
                },
                "current_mw": 55.0,
                "year_5_mw": 72.0,
                "year_10_mw": 88.0,
                "bankability_tier": "Tier 1",
                "bankability_score": 0.82,
                "reliability_class": "Critical",
                "load_factor": 0.85,
                "rationale": (
                    "APM Terminals concession — investment-grade operator "
                    "handling 70% of Nigeria's import/export cargo. "
                    "Critical reliability — national supply chain disruption risk "
                    "makes government very motivated to ensure reliable power. "
                    "55 MW current demand, steady 3.9% CAGR. "
                    "Served by same Lagos backbone segment as Lekki cluster — "
                    "incremental revenue on existing infrastructure investment."
                ),
                "recommended_action": (
                    "APM Terminals corporate guarantee as primary PPA counterparty. "
                    "NPA as secondary guarantor. "
                    "Dedicated feeder from Lagos backbone — shared with Lekki segment. "
                    "20-year PPA with NPA strategic importance backing."
                ),
                "estimated_annual_revenue_usd_m": 5.5,
                "phase_capex_contribution_usd_m": 18.0,
            },

            {
                "rank": 6,
                "anchor_id": "AL_ANC_012",
                "detection_id": "DET-012",
                "name": "Obuasi Gold Mine (AngloGold Ashanti)",
                "sector": "Mining",
                "sub_sector": "Underground Gold Mine",
                "country": "Ghana",
                "phase": "Phase 1",
                "gaps_addressed": ["GAP_004"],  # Obuasi 98km spur gap
                "composite_score": 87.9,
                "score_breakdown": {
                    "bankability_score": 95.0,    # Tier 1, 0.95 — strongest mining credit
                    "demand_score": 78.0,          # 68 MW
                    "growth_score": 75.0,          # 3.7% CAGR
                    "gap_severity_score": 85.0,    # GAP_004 High
                    "cluster_score": 55.0,         # Standalone spur
                },
                "current_mw": 68.0,
                "year_5_mw": 88.0,
                "year_10_mw": 108.0,
                "bankability_tier": "Tier 1",
                "bankability_score": 0.95,
                "reliability_class": "Critical",
                "load_factor": 0.93,
                "rationale": (
                    "AngloGold Ashanti (NYSE/JSE listed) — highest mining bankability "
                    "score on the corridor at 0.95. "
                    "Critical reliability class — underground operations require 99%+ uptime "
                    "for worker safety; this is a regulatory obligation, not a preference. "
                    "22 outages/year at current 161kV feed = $8–12M annual production loss. "
                    "Phase 3 mine expansion ($250M) is on critical path requiring "
                    "reliable power — AngloGold Ashanti will co-invest in spur. "
                    "Corporate guarantee anchors spur financing independently. "
                    "Ideal standalone proof-of-concept for DFI mining spur structure."
                ),
                "recommended_action": (
                    "330kV dedicated spur, Kumasi substation to Obuasi mine, ~98km. "
                    "AngloGold Ashanti corporate guarantee as spur anchor — "
                    "they can prepay or provide equity co-investment. "
                    "20-year take-or-pay PPA at Critical reliability premium tariff. "
                    "New 330/11kV mine substation at Obuasi. "
                    "Estimated spur payback: 4–5 years at Phase 3 expansion demand."
                ),
                "estimated_annual_revenue_usd_m": 6.8,
                "phase_capex_contribution_usd_m": 88.0,
            },

            {
                "rank": 7,
                "anchor_id": "AL_ANC_008",
                "detection_id": "DET-008",
                "name": "Tema Port — Meridian Port Services",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics",
                "country": "Ghana",
                "phase": "Phase 1",
                "gaps_addressed": ["GAP_006"],  # Tema industrial cluster
                "composite_score": 86.4,
                "score_breakdown": {
                    "bankability_score": 87.0,    # Tier 1, 0.87
                    "demand_score": 75.0,          # 38 MW
                    "growth_score": 82.0,          # 5.3% CAGR
                    "gap_severity_score": 95.0,    # GAP_006 Critical
                    "cluster_score": 92.0,         # Tema industrial cluster
                },
                "current_mw": 38.0,
                "year_5_mw": 55.0,
                "year_10_mw": 72.0,
                "bankability_tier": "Tier 1",
                "bankability_score": 0.87,
                "reliability_class": "Critical",
                "load_factor": 0.82,
                "rationale": (
                    "APM Terminals JV with 35-year concession — investment-grade operator. "
                    "Critical reliability class — vessel demurrage at $20–50K/hour "
                    "makes power reliability a contractual obligation. "
                    "Part of Tema industrial cluster (also serves TOR and Tema FTZ) — "
                    "GAP_006 reinforcement investment serves three anchors simultaneously. "
                    "Phase 2 terminal expansion doubling capacity confirmed — "
                    "demand growth from 38 to 72 MW by Year 10 is virtually certain. "
                    "Anchors the Ghana segment of the corridor financing."
                ),
                "recommended_action": (
                    "APM Terminals corporate guarantee as primary PPA counterparty. "
                    "GPHA sovereign backstop as secondary. "
                    "Shared 330kV Tema industrial cluster reinforcement (GAP_006) "
                    "with TOR and Tema Free Zone — $83M net capex shared across "
                    "three anchors reduces per-anchor cost significantly. "
                    "20-year PPA with phase-2 expansion commitment built in."
                ),
                "estimated_annual_revenue_usd_m": 3.8,
                "phase_capex_contribution_usd_m": 28.0,
                # Note: $83M total GAP_006 shared across Tema cluster anchors
            },

            {
                "rank": 8,
                "anchor_id": "AL_ANC_009",
                "detection_id": "DET-009",
                "name": "Tema Free Zone",
                "sector": "Industrial",
                "sub_sector": "Special Economic Zone",
                "country": "Ghana",
                "phase": "Phase 1",
                "gaps_addressed": ["GAP_006"],  # Tema industrial cluster
                "composite_score": 85.1,
                "score_breakdown": {
                    "bankability_score": 80.0,    # Tier 1, 0.80
                    "demand_score": 80.0,          # 52 MW
                    "growth_score": 88.0,          # 7.5% CAGR
                    "gap_severity_score": 95.0,    # GAP_006 Critical
                    "cluster_score": 92.0,         # Tema cluster
                },
                "current_mw": 52.0,
                "year_5_mw": 92.0,
                "year_10_mw": 138.0,
                "bankability_tier": "Tier 1",
                "bankability_score": 0.80,
                "reliability_class": "High",
                "load_factor": 0.77,
                "rationale": (
                    "GFZA with 200+ enterprise tenants — diversified off-take risk. "
                    "Currently at 60% capacity due to power constraint — "
                    "reliable grid power alone unlocks 20–25 MW immediately "
                    "(suppressed demand unlock). "
                    "7.5% CAGR driven by 200-hectare Phase 2 expansion "
                    "and GFZA 400-enterprise target. "
                    "Shares Tema industrial reinforcement (GAP_006) with "
                    "Tema Port and TOR — cost per anchor is low. "
                    "Ghana government backstop strengthens creditworthiness."
                ),
                "recommended_action": (
                    "GFZA as aggregate PPA counterparty — Ghana government letter of support. "
                    "Shared 330kV Tema cluster reinforcement with Tema Port (Rank 7). "
                    "Aggregated PPA across zone tenants with GFZA as single counterparty. "
                    "Phase load commitment aligned with zone occupancy targets."
                ),
                "estimated_annual_revenue_usd_m": 5.2,
                "phase_capex_contribution_usd_m": 28.0,
                # Note: $83M total GAP_006 shared
            },

            {
                "rank": 9,
                "anchor_id": "AL_ANC_017",
                "detection_id": "DET-017",
                "name": "Port of Lomé — Container Terminal",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics",
                "country": "Togo",
                "phase": "Phase 1",
                "gaps_addressed": ["GAP_002", "GAP_007"],  # Lomé–Cotonou + Lomé industrial
                "composite_score": 84.8,
                "score_breakdown": {
                    "bankability_score": 85.0,    # Tier 1, 0.85
                    "demand_score": 70.0,          # 28 MW
                    "growth_score": 82.0,          # 5.9% CAGR
                    "gap_severity_score": 98.0,    # GAP_002 Critical + GAP_007 High
                    "cluster_score": 85.0,         # Lomé industrial cluster
                },
                "current_mw": 28.0,
                "year_5_mw": 42.0,
                "year_10_mw": 58.0,
                "bankability_tier": "Tier 1",
                "bankability_score": 0.85,
                "reliability_class": "Critical",
                "load_factor": 0.83,
                "rationale": (
                    "MSC / Bolloré JV — investment-grade operators running "
                    "West Africa's deepest natural port. "
                    "Without Lomé port as anchor, the $125M Lomé–Cotonou "
                    "330kV interconnector (GAP_002) cannot be financed. "
                    "This anchor is the keystone for the entire Togo segment — "
                    "its PPA makes the backbone investment bankable. "
                    "Togo grid at 65% import dependency — "
                    "port currently spending $5–7M/year on backup diesel. "
                    "Critical reliability class, 28 MW baseload, 24/7 operations."
                ),
                "recommended_action": (
                    "MSC/Bolloré JV corporate guarantee as primary PPA counterparty. "
                    "Port as anchor off-taker for GAP_002 Lomé–Cotonou 330kV line. "
                    "20-year take-or-pay PPA — critical for interconnector financing. "
                    "Bundle with WACEM cement (Rank 10) and Lomé Free Zone (Rank 11) "
                    "into Lomé industrial cluster PPA package."
                ),
                "estimated_annual_revenue_usd_m": 2.8,
                "phase_capex_contribution_usd_m": 42.0,
                # Note: $125M GAP_002 shared across Lomé–Cotonou corridor anchors
            },

            {
                "rank": 10,
                "anchor_id": "AL_ANC_003",
                "detection_id": "DET-003",
                "name": "Port of Abidjan — Vridi Terminal",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics",
                "country": "Côte d'Ivoire",
                "phase": "Phase 1",
                "gaps_addressed": ["GAP_001", "GAP_009"],  # Abidjan–Takoradi + Abidjan reliability
                "composite_score": 83.6,
                "score_breakdown": {
                    "bankability_score": 84.0,    # Tier 1, 0.84
                    "demand_score": 76.0,          # 45 MW
                    "growth_score": 78.0,          # 4.8% CAGR
                    "gap_severity_score": 95.0,    # GAP_001 Critical
                    "cluster_score": 82.0,         # Abidjan cluster
                },
                "current_mw": 45.0,
                "year_5_mw": 62.0,
                "year_10_mw": 80.0,
                "bankability_tier": "Tier 1",
                "bankability_score": 0.84,
                "reliability_class": "Critical",
                "load_factor": 0.80,
                "rationale": (
                    "APM Terminals concession at West Africa's largest port — "
                    "investment-grade operator with long concession providing revenue certainty. "
                    "Largest port in West Africa anchors the Abidjan segment financing. "
                    "Currently spending $8M/year on backup diesel — "
                    "strong motivation to sign. "
                    "Anchors GAP_001 (Abidjan–Takoradi 330kV link) — "
                    "without this PPA the $340M backbone investment "
                    "cannot be financed. "
                    "New TC2 terminal under construction confirms "
                    "long-term demand growth to 115 MW by Year 20."
                ),
                "recommended_action": (
                    "APM Terminals corporate guarantee as primary PPA counterparty. "
                    "APDL sovereign backstop. "
                    "Anchor off-taker for GAP_001 Abidjan–Takoradi 330kV line. "
                    "20-year take-or-pay PPA — essential for backbone financing. "
                    "Bundle with ZIEX (Rank 11) and Cargill (Rank 12) "
                    "into Abidjan industrial cluster package."
                ),
                "estimated_annual_revenue_usd_m": 4.5,
                "phase_capex_contribution_usd_m": 113.0,
                # Note: $340M GAP_001 shared across Abidjan–Takoradi corridor
            },

            # ============================================================
            # PHASE 2 — CATALYTIC EXPANSION (Years 3–6)
            # Strong fundamentals but require credit enhancement, government
            # co-investment, or anchor tenant confirmation before proceeding
            # ============================================================

            {
                "rank": 11,
                "anchor_id": "AL_ANC_019",
                "detection_id": "DET-019",
                "name": "Lomé Cement Plant (WACEM)",
                "sector": "Industrial",
                "sub_sector": "Cement & Clinker Manufacturing",
                "country": "Togo",
                "phase": "Phase 2",
                "gaps_addressed": ["GAP_007"],  # Lomé industrial cluster
                "composite_score": 78.4,
                "score_breakdown": {
                    "bankability_score": 79.0,    # Tier 2, 0.79
                    "demand_score": 72.0,          # 35 MW
                    "growth_score": 75.0,          # 5.0% CAGR
                    "gap_severity_score": 85.0,    # GAP_007 High
                    "cluster_score": 85.0,         # Lomé cluster
                },
                "current_mw": 35.0,
                "year_5_mw": 50.0,
                "year_10_mw": 65.0,
                "bankability_tier": "Tier 2",
                "bankability_score": 0.79,
                "reliability_class": "High",
                "load_factor": 0.85,
                "rationale": (
                    "Largest industrial electricity consumer in Togo — "
                    "35 MW running continuously at kilns. "
                    "High load factor (0.85) means reliable revenue contribution. "
                    "Phase 2 because WACEM is private with limited credit transparency — "
                    "GuarantCo partial risk guarantee needed. "
                    "Shares Lomé industrial cluster infrastructure with Port of Lomé "
                    "and Lomé Free Zone — CAPEX already largely justified. "
                    "Power reliability directly reduces kiln restart costs "
                    "($4M/year current loss) creating strong motivation."
                ),
                "recommended_action": (
                    "GuarantCo partial risk guarantee to cover WACEM credit risk. "
                    "Escrow arrangement for PPA payments recommended. "
                    "Shared 161kV Lomé industrial feeder (GAP_007) — "
                    "CAPEX incremental to Phase 1 Lomé infrastructure. "
                    "15-year PPA minimum for bankability."
                ),
                "estimated_annual_revenue_usd_m": 3.5,
                "phase_capex_contribution_usd_m": 14.0,
            },

            {
                "rank": 12,
                "anchor_id": "AL_ANC_022",
                "detection_id": "DET-022",
                "name": "Port of Cotonou — Bénin Terminal",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics",
                "country": "Benin",
                "phase": "Phase 2",
                "gaps_addressed": ["GAP_002", "GAP_008"],  # Lomé–Cotonou + Cotonou reliability
                "composite_score": 77.8,
                "score_breakdown": {
                    "bankability_score": 80.0,    # Tier 1, 0.80
                    "demand_score": 68.0,          # 24 MW
                    "growth_score": 72.0,          # 5.6% CAGR
                    "gap_severity_score": 92.0,    # GAP_002 Critical (eastern end)
                    "cluster_score": 75.0,         # Cotonou cluster
                },
                "current_mw": 24.0,
                "year_5_mw": 36.0,
                "year_10_mw": 48.0,
                "bankability_tier": "Tier 1",
                "bankability_score": 0.80,
                "reliability_class": "Critical",
                "load_factor": 0.79,
                "rationale": (
                    "Bolloré concession — investment-grade operator at Benin's primary port. "
                    "Phase 2 (not Phase 1) because Benin sovereign risk context "
                    "requires careful structuring — Bolloré corporate guarantee "
                    "as primary counterparty reduces but does not eliminate this risk. "
                    "Eastern anchor for GAP_002 Lomé–Cotonou interconnector — "
                    "PPA from this end of the line closes the interconnector financing gap. "
                    "Primary gateway for Niger, Burkina Faso, Mali — "
                    "hinterland transit demand creates long-term revenue floor."
                ),
                "recommended_action": (
                    "Bolloré corporate guarantee as primary PPA counterparty. "
                    "Benin government letter of support as secondary. "
                    "Eastern anchor off-taker for GAP_002 interconnector. "
                    "20-year PPA — coordinate timing with Phase 1 Lomé port agreement "
                    "so both ends of GAP_002 are contracted simultaneously."
                ),
                "estimated_annual_revenue_usd_m": 2.4,
                "phase_capex_contribution_usd_m": 42.0,
            },

            {
                "rank": 13,
                "anchor_id": "AL_ANC_005",
                "detection_id": "DET-005",
                "name": "Abidjan Export Processing Zone (ZIEX)",
                "sector": "Industrial",
                "sub_sector": "Special Economic Zone",
                "country": "Côte d'Ivoire",
                "phase": "Phase 2",
                "gaps_addressed": ["GAP_009"],  # Abidjan industrial reliability
                "composite_score": 76.5,
                "score_breakdown": {
                    "bankability_score": 78.0,    # Tier 2, 0.78
                    "demand_score": 74.0,          # 42 MW
                    "growth_score": 78.0,          # 5.8% CAGR
                    "gap_severity_score": 78.0,    # GAP_009 High
                    "cluster_score": 82.0,         # Abidjan cluster
                },
                "current_mw": 42.0,
                "year_5_mw": 65.0,
                "year_10_mw": 88.0,
                "bankability_tier": "Tier 2",
                "bankability_score": 0.78,
                "reliability_class": "High",
                "load_factor": 0.72,
                "rationale": (
                    "APEX-CI government-administered SEZ with Côte d'Ivoire sovereign backing. "
                    "42 MW current demand growing at 5.8% CAGR to 88 MW by Year 10. "
                    "Zone at 58% capacity — reliable power unlocks immediate suppressed demand. "
                    "Shares Abidjan industrial cluster infrastructure with Port of Abidjan "
                    "(Rank 10) — incremental CAPEX only. "
                    "Phase 2 because multi-tenant aggregate PPA structure takes time to establish. "
                    "MIGA partial risk guarantee recommended to cover tenant credit variability."
                ),
                "recommended_action": (
                    "MIGA partial risk guarantee for tenant credit risk. "
                    "Côte d'Ivoire government letter of support. "
                    "Shared 225kV Vridi industrial substation upgrade (GAP_009) "
                    "with Port of Abidjan — incremental feeder only. "
                    "Aggregated zone PPA with APEX-CI as counterparty."
                ),
                "estimated_annual_revenue_usd_m": 4.2,
                "phase_capex_contribution_usd_m": 16.0,
            },

            {
                "rank": 14,
                "anchor_id": "AL_ANC_023",
                "detection_id": "DET-023",
                "name": "Zone Industrielle de Cotonou (PK10)",
                "sector": "Industrial",
                "sub_sector": "Industrial Zone",
                "country": "Benin",
                "phase": "Phase 2",
                "gaps_addressed": ["GAP_008"],  # Cotonou industrial reliability
                "composite_score": 72.1,
                "score_breakdown": {
                    "bankability_score": 62.0,    # Tier 2, 0.62
                    "demand_score": 70.0,          # 30 MW
                    "growth_score": 72.0,          # 5.5% CAGR
                    "gap_severity_score": 82.0,    # GAP_008 High
                    "cluster_score": 75.0,         # Cotonou cluster
                },
                "current_mw": 30.0,
                "year_5_mw": 44.0,
                "year_10_mw": 58.0,
                "bankability_tier": "Tier 2",
                "bankability_score": 0.62,
                "reliability_class": "High",
                "load_factor": 0.60,
                "rationale": (
                    "Government-administered zone with Benin sovereign guarantee "
                    "as only meaningful credit. "
                    "Zone at 60% capacity — significant suppressed demand. "
                    "150-ha expansion ($200–400M) stalled entirely by power unreliability. "
                    "Phase 2 because Benin fiscal capacity requires AfDB/World Bank "
                    "partial risk guarantee before financeable. "
                    "Reliable power will increase load factor from 0.60 to 0.82+ "
                    "and unlock expansion — making the investment case stronger over time. "
                    "GAP_008 infrastructure is incremental to Phase 1 GAP_002 backbone."
                ),
                "recommended_action": (
                    "Benin government sovereign guarantee as PPA counterparty essential. "
                    "AfDB or World Bank partial risk guarantee to cover sovereign default risk. "
                    "Payment escrow arrangement. "
                    "Dedicated 33kV industrial feeder + SVC power quality equipment (GAP_008). "
                    "Coordinates with GAP_002 Phase 1 backbone for upstream reliability."
                ),
                "estimated_annual_revenue_usd_m": 3.0,
                "phase_capex_contribution_usd_m": 20.0,
            },

            {
                "rank": 15,
                "anchor_id": "AL_ANC_020",
                "detection_id": "DET-020",
                "name": "Lomé Free Zone (SAZOF)",
                "sector": "Industrial",
                "sub_sector": "Special Economic Zone",
                "country": "Togo",
                "phase": "Phase 2",
                "gaps_addressed": ["GAP_007"],  # Lomé industrial cluster
                "composite_score": 71.4,
                "score_breakdown": {
                    "bankability_score": 71.0,    # Tier 2, 0.71
                    "demand_score": 65.0,          # 22 MW
                    "growth_score": 88.0,          # 8.2% CAGR — strong
                    "gap_severity_score": 85.0,    # GAP_007 High
                    "cluster_score": 85.0,         # Lomé cluster
                },
                "current_mw": 22.0,
                "year_5_mw": 40.0,
                "year_10_mw": 62.0,
                "bankability_tier": "Tier 2",
                "bankability_score": 0.71,
                "reliability_class": "High",
                "load_factor": 0.70,
                "rationale": (
                    "Togo government-administered SEZ with significant suppressed demand. "
                    "Zone at 44% occupancy — reliable power expected to increase "
                    "to 70%+ occupancy immediately, unlocking 15–18 MW. "
                    "8.2% CAGR driven by Smart Lomé $1.2B infrastructure programme. "
                    "Phase 2 because multi-tenant PPA structure takes time. "
                    "Shares Lomé cluster infrastructure with Port of Lomé (Rank 9) "
                    "and WACEM (Rank 11) — CAPEX incremental only. "
                    "Togo sovereign guarantee as PPA counterparty."
                ),
                "recommended_action": (
                    "Togo government sovereign guarantee as PPA counterparty. "
                    "AfDB/EU Global Gateway co-financing for connection infrastructure. "
                    "Shared 161kV Lomé industrial feeder (GAP_007). "
                    "Aggregated zone PPA with SAZOF as counterparty."
                ),
                "estimated_annual_revenue_usd_m": 2.2,
                "phase_capex_contribution_usd_m": 14.0,
            },

            # Remaining Phase 2 anchors below Top 15 threshold
            {
                "rank": 16,
                "anchor_id": "AL_ANC_007",
                "detection_id": "DET-007",
                "name": "Tema Oil Refinery (TOR)",
                "sector": "Energy",
                "country": "Ghana",
                "phase": "Phase 2",
                "gaps_addressed": ["GAP_006"],
                "composite_score": 68.9,
                "current_mw": 32.0,
                "year_5_mw": 52.0,
                "bankability_tier": "Tier 2",
                "bankability_score": 0.68,
                "reliability_class": "High",
                "rationale": (
                    "State-owned, under rehabilitation — reliable power is prerequisite "
                    "for full restart. Sovereign guarantee + escrow required. "
                    "Phase 2 because rehabilitation timeline creates near-term uncertainty. "
                    "Shares Tema cluster infrastructure (GAP_006) with Tema Port and Free Zone."
                ),
                "recommended_action": (
                    "Ghana government sovereign guarantee. Escrow for payments. "
                    "Shared Tema industrial reinforcement. Phase trigger: rehabilitation milestone."
                ),
                "estimated_annual_revenue_usd_m": 3.2,
                "phase_capex_contribution_usd_m": 27.0,
            },

            {
                "rank": 17,
                "anchor_id": "AL_ANC_004",
                "detection_id": "DET-004",
                "name": "Cargill Cocoa Processing Plant — Abidjan Hinterland",
                "sector": "Agriculture",
                "country": "Côte d'Ivoire",
                "phase": "Phase 2",
                "gaps_addressed": ["GAP_009"],
                "composite_score": 67.5,
                "current_mw": 18.0,
                "year_5_mw": 28.0,
                "bankability_tier": "Tier 2",
                "bankability_score": 0.72,
                "reliability_class": "High",
                "rationale": (
                    "Fortune 500 credit — upgrades to Tier 1 once identity fully confirmed. "
                    "Partial RCCM match means PPA cannot be executed until verified. "
                    "Priority action: identity confirmation. "
                    "Once confirmed, expected to rise to Rank 7–8."
                ),
                "recommended_action": (
                    "PRIORITY: field verify identity. Once confirmed — immediate PPA. "
                    "Shared Abidjan cluster feeder (GAP_009)."
                ),
                "estimated_annual_revenue_usd_m": 1.8,
                "phase_capex_contribution_usd_m": 0.0,
            },

            {
                "rank": 18,
                "anchor_id": "AL_ANC_016",
                "detection_id": "DET-016",
                "name": "Accra Data Center (ADC)",
                "sector": "Digital",
                "country": "Ghana",
                "phase": "Phase 2",
                "gaps_addressed": ["GAP_006"],
                "composite_score": 66.2,
                "current_mw": 12.0,
                "year_5_mw": 25.0,
                "bankability_tier": "Tier 1",
                "bankability_score": 0.86,
                "reliability_class": "Critical",
                "rationale": (
                    "Strong bankability (0.86) but 12 MW current demand is modest. "
                    "Phase 2 because scale does not individually justify dedicated investment. "
                    "Shared Tema industrial reinforcement (GAP_006) serves this anchor "
                    "as part of broader Tema cluster. 10.2% CAGR makes this a "
                    "valuable long-term contributor."
                ),
                "recommended_action": (
                    "Bundle into Tema industrial cluster. N+1 dual feed from Tema reinforcement. "
                    "Equinix-standard PPA template."
                ),
                "estimated_annual_revenue_usd_m": 1.2,
                "phase_capex_contribution_usd_m": 0.0,
            },

            {
                "rank": 19,
                "anchor_id": "AL_ANC_032",
                "detection_id": "DET-032",
                "name": "Sagamu-Interchange Manufacturing Cluster",
                "sector": "Industrial",
                "country": "Nigeria",
                "phase": "Phase 2",
                "gaps_addressed": ["GAP_010"],
                "composite_score": 62.8,
                "current_mw": 45.0,
                "year_5_mw": 62.0,
                "bankability_tier": "Tier 2",
                "bankability_score": 0.58,
                "reliability_class": "High",
                "rationale": (
                    "Multi-tenant cluster — no single creditworthy counterparty. "
                    "Ogun State government aggregation model required. "
                    "45 MW current demand with 4.9% CAGR is commercially interesting "
                    "but contract complexity makes Phase 2 correct timing."
                ),
                "recommended_action": (
                    "Ogun State as aggregate PPA counterparty. "
                    "132/33kV substation capacity upgrade (GAP_010). "
                    "NEXIM co-financing."
                ),
                "estimated_annual_revenue_usd_m": 4.5,
                "phase_capex_contribution_usd_m": 28.0,
            },

            {
                "rank": 20,
                "anchor_id": "AL_ANC_015",
                "detection_id": "DET-015",
                "name": "Takoradi Port — Bulk & General Cargo Terminal",
                "sector": "Industrial",
                "country": "Ghana",
                "phase": "Phase 2",
                "gaps_addressed": ["GAP_012"],
                "composite_score": 61.4,
                "current_mw": 18.0,
                "year_5_mw": 28.0,
                "bankability_tier": "Tier 2",
                "bankability_score": 0.78,
                "reliability_class": "High",
                "rationale": (
                    "Bolloré concession with GPHA backstop — solid credit. "
                    "18 MW current demand is modest but liquid bulk jetty expansion "
                    "is confirmed. Shares Takoradi agro-processing cluster "
                    "infrastructure (GAP_012) with cocoa belt corridor."
                ),
                "recommended_action": (
                    "GPHA backstop as secondary guarantor. "
                    "Shared Takoradi ring main reinforcement (GAP_012). "
                    "Bundle with cocoa processing cluster."
                ),
                "estimated_annual_revenue_usd_m": 1.8,
                "phase_capex_contribution_usd_m": 10.0,
            },

            # ============================================================
            # PHASE 3 — CONDITIONAL (Post Year 6)
            # Require identity verification, licence grants, or aggregation
            # mechanisms before investment can be committed
            # ============================================================

            {
                "rank": 21,
                "anchor_id": "AL_ANC_014",
                "detection_id": "DET-014",
                "name": "Weta Rice Farm & Milling Hub — Volta Region",
                "sector": "Agriculture",
                "country": "Ghana",
                "phase": "Phase 3",
                "gaps_addressed": ["GAP_011"],
                "composite_score": 48.2,
                "current_mw": 8.0,
                "year_5_mw": 8.0,
                "bankability_tier": "Tier 3",
                "bankability_score": 0.45,
                "reliability_class": "Standard",
                "rationale": (
                    "Highest development impact on corridor (95,000 jobs) but "
                    "weakest bankability (0.45). No grid connection, fragmented ownership, "
                    "identity partially resolved. "
                    "Base case: flat at 8 MW. Upside: 150 MW if connected. "
                    "Cannot anchor financing alone — requires full blended finance structure. "
                    "Conditions before proceeding: identity confirmed, COCOBOD aggregation "
                    "established, AfDB SAPZ co-financing approved."
                ),
                "recommended_action": (
                    "Phase 3 only. Conditions: identity confirm + COCOBOD aggregation + AfDB SAPZ. "
                    "161kV spur from Akuse, ~35km, $32M (GAP_011). "
                    "Blended: AfDB grant 20% + World Bank concessional 40% + "
                    "Ghana gov 25% + commercial 15%."
                ),
                "estimated_annual_revenue_usd_m": 0.8,
                "phase_capex_contribution_usd_m": 32.0,
            },

            {
                "rank": 22,
                "anchor_id": "AL_ANC_034",
                "detection_id": "DET-034",
                "name": "Unverified Hyperscale Data Center — Lagos Island North",
                "sector": "Digital",
                "country": "Nigeria",
                "phase": "Phase 3",
                "gaps_addressed": ["GAP_014"],
                "composite_score": 38.5,
                "current_mw": 35.0,
                "year_5_mw": 35.0,
                "bankability_tier": "Tier 3",
                "bankability_score": 0.35,
                "reliability_class": "Critical",
                "rationale": (
                    "Identity completely unresolved — cannot be included in any "
                    "financing structure. If confirmed as hyperscale DC, "
                    "immediate upgrade to Rank 3–4 with score 0.92+. "
                    "Priority field verification target — "
                    "potential $200M+ annual revenue contribution at buildout."
                ),
                "recommended_action": (
                    "PRIORITY VERIFICATION ACTION: NCC registry check + field visit. "
                    "Reassess immediately on confirmation. "
                    "If confirmed hyperscale: fast-track to Phase 1."
                ),
                "estimated_annual_revenue_usd_m": 0.0,
                "phase_capex_contribution_usd_m": 0.0,
            },

            {
                "rank": 23,
                "anchor_id": "AL_ANC_024",
                "detection_id": "DET-024",
                "name": "Unidentified Agro-Processing Cluster — Benin Coastal",
                "sector": "Agriculture",
                "country": "Benin",
                "phase": "Phase 3",
                "gaps_addressed": ["GAP_013"],
                "composite_score": 31.2,
                "current_mw": 4.5,
                "year_5_mw": 4.5,
                "bankability_tier": "Tier 3",
                "bankability_score": 0.28,
                "reliability_class": "Standard",
                "rationale": (
                    "Identity completely unresolved, demand modest at 4.5 MW. "
                    "Phase 3 only. If multinational agro-processor confirmed, "
                    "score upgrades significantly. "
                    "AfDB SAPZ programme connection would improve trajectory."
                ),
                "recommended_action": (
                    "Field verification required before any assessment. "
                    "33kV extension from Cotonou network edge (GAP_013), ~12km, $14M. "
                    "Conditional on identity + SAPZ programme confirmation."
                ),
                "estimated_annual_revenue_usd_m": 0.0,
                "phase_capex_contribution_usd_m": 0.0,
            },

            {
                "rank": 24,
                "anchor_id": "AL_ANC_035",
                "detection_id": "DET-035",
                "name": "Lithium Exploration & Processing Site — Ghana North",
                "sector": "Mining",
                "country": "Ghana",
                "phase": "Phase 3",
                "gaps_addressed": ["GAP_005"],
                "composite_score": 29.8,
                "current_mw": 8.0,
                "year_5_mw": 8.0,
                "bankability_tier": "Tier 3",
                "bankability_score": 0.42,
                "reliability_class": "High",
                "rationale": (
                    "Operator redacted, mining licence not yet granted. "
                    "At full production: 120–150 MW Tier 1 anchor. "
                    "Currently uninvestable — conditions: licence + identity + guarantee. "
                    "Highest strategic future value of all Phase 3 anchors "
                    "given global EV battery demand for lithium."
                ),
                "recommended_action": (
                    "Request Minerals Commission cadastre access. "
                    "Monitor licence application status. "
                    "161kV spur from Mampong, ~44km, $42M (GAP_005). "
                    "Conditional on mining licence grant and operator confirmation."
                ),
                "estimated_annual_revenue_usd_m": 0.0,
                "phase_capex_contribution_usd_m": 0.0,
            },
        ],

        # ================================================================
        # CLUSTER SUMMARY
        # ================================================================
        "clusters": {
            "lekki_lagos_cluster": {
                "anchors": ["AL_ANC_027", "AL_ANC_028", "AL_ANC_029", "AL_ANC_030", "AL_ANC_031"],
                "current_mw": 1258.0,
                "year_10_mw": 2448.0,
                "gap": "GAP_003",
                "cluster_capex_usd_m": 380.0,
                "annual_revenue_year_1_usd_m": 110.6,
                "cluster_rationale": (
                    "Dominant cluster on the corridor — 1,258 MW today, "
                    "2,448 MW by Year 10. Single 400kV hub investment ($380M) "
                    "serves all five anchors. Dangote alone justifies the hub. "
                    "Every other anchor in this cluster is incremental revenue."
                ),
            },
            "tema_accra_cluster": {
                "anchors": ["AL_ANC_007", "AL_ANC_008", "AL_ANC_009", "AL_ANC_016"],
                "current_mw": 134.0,
                "year_10_mw": 300.0,
                "gap": "GAP_006",
                "cluster_capex_usd_m": 83.0,
                "annual_revenue_year_1_usd_m": 13.4,
                "cluster_rationale": (
                    "Ghana's industrial anchor cluster. Single 330kV reinforcement "
                    "serves port, free zone, refinery, and data center. "
                    "134 MW today growing to 300 MW by Year 10."
                ),
            },
            "lome_cluster": {
                "anchors": ["AL_ANC_017", "AL_ANC_019", "AL_ANC_020"],
                "current_mw": 85.0,
                "year_10_mw": 185.0,
                "gap": "GAP_002 + GAP_007",
                "cluster_capex_usd_m": 167.0,
                "annual_revenue_year_1_usd_m": 8.5,
                "cluster_rationale": (
                    "Togo cluster anchored by West Africa's deepest port. "
                    "GAP_002 interconnector + GAP_007 industrial feeder "
                    "together transform Togo's grid reliability."
                ),
            },
            "cotonou_cluster": {
                "anchors": ["AL_ANC_022", "AL_ANC_023"],
                "current_mw": 54.0,
                "year_10_mw": 106.0,
                "gap": "GAP_002 + GAP_008",
                "cluster_capex_usd_m": 62.0,
                "annual_revenue_year_1_usd_m": 5.4,
                "cluster_rationale": (
                    "Benin cluster requiring sovereign guarantee structuring. "
                    "Eastern anchor of GAP_002 interconnector."
                ),
            },
            "abidjan_cluster": {
                "anchors": ["AL_ANC_003", "AL_ANC_004", "AL_ANC_005"],
                "current_mw": 105.0,
                "year_10_mw": 205.0,
                "gap": "GAP_001 + GAP_009",
                "cluster_capex_usd_m": 129.0,
                "annual_revenue_year_1_usd_m": 10.5,
                "cluster_rationale": (
                    "Abidjan cluster anchors the western end of the corridor backbone. "
                    "Port as primary off-taker makes GAP_001 backbone financeable."
                ),
            },
        },

        # ================================================================
        # PHASED ROADMAP
        # ================================================================
        "phased_roadmap": {
            "phase_1": {
                "label": "Phase 1 — Anchor & De-risk (Years 1–3)",
                "ranks": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "anchor_count": 10,
                "total_current_mw": 1493.0,
                "total_year_5_mw": 2220.0,
                "total_year_10_mw": 3008.0,
                "total_phase_capex_usd_m": 754.0,
                "total_annual_revenue_year_1_usd_m": 148.7,
                "gaps_addressed": [
                    "GAP_001 — Abidjan–Takoradi 330kV link ($340M net)",
                    "GAP_002 — Lomé–Cotonou 330kV interconnector ($125M net, partial)",
                    "GAP_003 — Lekki 400kV hub ($355M net)",
                    "GAP_004 — Obuasi 330kV spur ($80M net)",
                    "GAP_006 — Tema industrial reinforcement ($83M net, partial)",
                    "GAP_007 — Lomé industrial feeder ($42M net, partial)",
                ],
                "focus": (
                    "Secure PPAs with 10 Tier 1 anchors to underwrite the transmission "
                    "backbone debt. These 10 anchors contribute 1,493 MW today and "
                    "2,220 MW by Year 5 — sufficient to service the full corridor "
                    "financing structure. "
                    "Lekki cluster alone (Ranks 1–3) contributes 1,185 MW — "
                    "Dangote Refinery anchors the Lagos hub independently. "
                    "Phase 1 generates $148.7M annual revenue in Year 1 "
                    "against $754M total CAPEX — 19.7% revenue/CAPEX ratio."
                ),
                "key_risks": [
                    "Dangote PPA negotiation timeline — target 90-day execution",
                    "GAP_001 Abidjan–Takoradi backbone CAPEX is largest single item",
                    "Togo grid import dependency creates backbone reliability risk "
                    "until GAP_002 is complete",
                ],
            },
            "phase_2": {
                "label": "Phase 2 — Catalytic Expansion (Years 3–6)",
                "ranks": [11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
                "anchor_count": 10,
                "total_current_mw": 278.0,
                "total_year_5_mw": 404.0,
                "total_year_10_mw": 566.0,
                "total_phase_capex_usd_m": 171.0,
                "total_annual_revenue_year_1_usd_m": 28.8,
                "gaps_addressed": [
                    "GAP_002 — Lomé–Cotonou (eastern end completion)",
                    "GAP_006 — Tema industrial (TOR rehabilitation phase)",
                    "GAP_007 — Lomé industrial (WACEM + SAZOF)",
                    "GAP_008 — Cotonou industrial reliability",
                    "GAP_009 — Abidjan Vridi industrial reliability",
                    "GAP_010 — Sagamu manufacturing cluster",
                    "GAP_012 — Takoradi agro-processing",
                ],
                "focus": (
                    "Deploy blended finance instruments to unlock industrial and agricultural "
                    "zones where credit enhancement is needed. "
                    "Phase 1 revenue ($148.7M/year) provides construction funding bridge. "
                    "AfDB, World Bank, MIGA, GuarantCo instruments used for Tier 2 anchors. "
                    "Phase 2 adds 278 MW current demand and 566 MW by Year 10 "
                    "at $171M CAPEX — highly efficient on existing backbone infrastructure."
                ),
                "key_risks": [
                    "Sovereign risk in Benin requires careful guarantee structuring",
                    "Multi-tenant PPA aggregation takes 12–18 months to execute",
                    "TOR rehabilitation timeline uncertainty",
                ],
            },
            "phase_3": {
                "label": "Phase 3 — Conditional Pipeline (Post Year 6)",
                "ranks": [21, 22, 23, 24],
                "anchor_count": 4,
                "total_current_mw": 55.5,
                "total_addressable_mw_if_confirmed": 535.0,
                "total_phase_capex_usd_m": 46.0,
                "focus": (
                    "Conditional opportunities requiring verification, licence grants, "
                    "or aggregation mechanisms. Do not commit CAPEX until conditions met. "
                    "Priority actions: (1) field verify Lagos DC identity (Rank 22 — "
                    "potential Rank 3–4 upgrade), (2) confirm Cargill identity (Rank 17 — "
                    "potential Rank 7 upgrade), (3) monitor Ghana lithium licence status. "
                    "If all four Phase 3 anchors confirmed, corridor addressable demand "
                    "increases by 535 MW — $40–60M additional annual revenue."
                ),
                "conditions_before_commit": [
                    "AL_ANC_034: Identity field verification",
                    "AL_ANC_014: COCOBOD aggregation + AfDB SAPZ approval",
                    "AL_ANC_024: Operator identity field verification",
                    "AL_ANC_035: Mining licence grant + operator identity confirmation",
                ],
            },
        },

        # ================================================================
        # FINANCIAL SUMMARY FOR FINANCING OPTIMIZATION AGENT
        # ================================================================
        "financial_summary": {
            "total_corridor_current_mw": 2127.5,
            "phase_1_current_mw": 1493.0,
            "phase_2_current_mw": 278.0,
            "phase_3_conditional_mw": 55.5,

            "total_corridor_year_10_mw_base": 4690.0,
            "total_corridor_year_10_mw_upside": 5280.0,

            "total_net_capex_usd_m": 1293.0,
            "phase_1_capex_usd_m": 754.0,
            "phase_2_capex_usd_m": 171.0,
            "phase_3_capex_usd_m": 46.0,
            "co_location_savings_usd_m": 175.0,

            "estimated_year_1_revenue_usd_m": 148.7,
            "estimated_year_5_revenue_usd_m": 285.0,
            "estimated_year_10_revenue_usd_m": 445.0,

            "tier_1_anchor_count": 13,
            "tier_2_anchor_count": 8,
            "tier_3_anchor_count": 3,

            "indicative_project_irr_range": "14–18%",
            "indicative_payback_years": "7–9",

            "key_financing_instruments_needed": [
                "Senior debt — IFC / AfDB / commercial banks (Phase 1 backbone)",
                "Subordinated debt — DFI concessional (Phase 1 Obuasi spur)",
                "Partial risk guarantees — MIGA / GuarantCo (Phase 2 Tier 2 anchors)",
                "Grant co-financing — AfDB SAPZ / EU Global Gateway (Phase 3 catalytic)",
                "Sovereign guarantees — Ghana, Togo, Benin, Nigeria (per anchor)",
            ],
        },

        "recommendation": (
            "Phase 1 priority: secure PPAs with the 10 Tier 1 anchors (Ranks 1–10) "
            "before finalising transmission route and substation sizing. "
            "Dangote Refinery (Rank 1) alone — 1,000 MW at 0.96 bankability — "
            "is sufficient to anchor the Lagos segment financing independently. "
            "Lekki Cluster (Ranks 1–3) contributes 1,185 MW and justifies the "
            "$380M Lagos hub on its own. "
            "Ghana central segment anchored by Obuasi Mine (Rank 6) and "
            "Tema cluster (Ranks 7–8). "
            "Togo/Benin segment anchored by Port of Lomé (Rank 9) and "
            "Port of Cotonou (Rank 12). "
            "Do not commit Phase 2 capex until Phase 1 PPAs signed. "
            "Do not commit Phase 3 capex until verification conditions met. "
            "Priority verification actions that could accelerate timeline: "
            "(1) Lagos DC identity — if hyperscale confirmed, fast-track to Phase 1; "
            "(2) Cargill identity — if confirmed, add to Phase 1 Abidjan cluster."
        ),

        "message": (
            "24 anchor loads ranked across 5 sectors and 5 corridor countries. "
            "Phase 1 (10 anchors): 1,493 MW current, $754M capex, $148.7M Year 1 revenue. "
            "Phase 2 (10 anchors): 278 MW current, $171M capex, requires blended finance. "
            "Phase 3 (4 anchors): conditional — 535 MW unlockable if confirmed. "
            "Total corridor: 2,127.5 MW current → 6,017 MW Year 20 base case. "
            "Indicative project IRR: 14–18%. Payback: 7–9 years. "
            "Lekki cluster dominates at 59% of Phase 1 demand — "
            "Dangote Refinery is the single most important anchor on the corridor."
        ),
    }

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=json.dumps(response),
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )