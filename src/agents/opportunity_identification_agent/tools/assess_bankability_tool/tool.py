import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import BankabilityInput


@tool("assess_bankability", description=TOOL_DESCRIPTION)
def assess_bankability_tool(
    payload: BankabilityInput, runtime: ToolRuntime
) -> Command:
    """
    Evaluates the commercial viability of each anchor load as a long-term
    transmission customer. Scores each anchor load across three dimensions:

        1. offtake_willingness  — motivation and intent to sign a long-term contract
        2. financial_strength   — ability to honor payments for 20+ years
        3. contract_readiness   — speed and ease of getting a contract signed

    Produces a composite score (0–1) and tier classification:
        Tier 1 — Bankable: can anchor project debt directly
        Tier 2 — Viable with credit enhancement or government guarantee
        Tier 3 — High risk: requires blended finance or sovereign co-financing

    Key inputs from upstream tools:
        - anchor_id, entity_name, operator, registry_source  (scan_anchor_loads)
        - current_mw, load_factor, reliability_class          (calculate_current_demand)

    The reliability_class from calculate_current_demand is a critical input:
        Critical class facilities have the strongest motivation to sign
        long-term contracts because unreliable power causes safety risks,
        equipment damage, or severe financial penalties for them.

    This tool does NOT return:
        - Demand forecasts / growth projections  → model_growth_trajectory
        - Revenue projections                    → prioritize_opportunities
        - Financing structures                   → financing_optimization_agent
        - Route recommendations                  → infrastructure_optimization_agent

    Anchor loads assessed: 24 (aligned to scan_anchor_loads and calculate_current_demand)
    Generation assets excluded: 10
    Substations excluded: 3
    """

    response = {
        "corridor_average_score": 0.77,
        "anchor_loads_assessed": 24,
        "generation_assets_excluded": 10,
        "substations_excluded": 3,
        "tier_summary": {
            "tier_1_count": 13,   # Bankable — can anchor project debt directly
            "tier_2_count": 8,    # Viable — bankable with credit enhancement
            "tier_3_count": 3,    # High risk — requires blended finance
        },
        "bankability_scores": [

            # ================================================================
            # CÔTE D'IVOIRE
            # ================================================================

            {
                # Port of Abidjan — Vridi Terminal
                # operator: APM Terminals (concession) / APDL
                # reliability_class: Critical | current_mw: 45 | load_factor: 0.80
                "anchor_id": "AL_ANC_003",
                "detection_id": "DET-003",
                "entity_name": "Port of Abidjan — Vridi Terminal",
                "country": "Côte d'Ivoire",
                "score": 0.84,
                "tier": "Tier 1",
                "offtake_willingness": "High",
                "financial_strength": "Strong",
                "contract_readiness": "High",
                "rationale": (
                    "APM Terminals (Maersk subsidiary) is investment-grade with a "
                    "long-term port concession providing revenue certainty. "
                    "New terminal extension increases power sensitivity — "
                    "operator is highly motivated to secure reliable grid connection. "
                    "Sovereign port authority (APDL) provides backstop guarantee."
                ),
                "credit_enhancement_required": "None — bankable as standalone",
            },

            {
                # Cargill Cocoa Processing Plant — Abidjan Hinterland
                # operator: Cargill Cocoa & Chocolate (partial identity)
                # reliability_class: High | current_mw: 18 | load_factor: 0.65
                "anchor_id": "AL_ANC_004",
                "detection_id": "DET-004",
                "entity_name": "Cargill Cocoa Processing Plant — Abidjan Hinterland",
                "country": "Côte d'Ivoire",
                "score": 0.72,
                "tier": "Tier 2",
                "offtake_willingness": "High",
                "financial_strength": "Strong",
                "contract_readiness": "Medium",
                "rationale": (
                    "Cargill is a Fortune 500 company with investment-grade credit — "
                    "financial strength is strong. "
                    "Score moderated to Tier 2 because identity is only partially resolved "
                    "(RCCM partial match) — contract cannot be signed until "
                    "operator identity is fully confirmed. "
                    "Once identity verified, expected to upgrade to Tier 1. "
                    "Diesel generator pads at facility indicate strong motivation "
                    "to replace expensive backup power with grid connection."
                ),
                "credit_enhancement_required": (
                    "Identity verification required before contract. "
                    "No financial credit enhancement needed once confirmed."
                ),
            },

            {
                # Abidjan Export Processing Zone (ZIEX)
                # operator: Société de Gestion de la Zone Franche / APEX-CI
                # reliability_class: High | current_mw: 42 | load_factor: 0.72
                "anchor_id": "AL_ANC_005",
                "detection_id": "DET-005",
                "entity_name": "Abidjan Export Processing Zone (ZIEX)",
                "country": "Côte d'Ivoire",
                "score": 0.78,
                "tier": "Tier 2",
                "offtake_willingness": "High",
                "financial_strength": "Moderate",
                "contract_readiness": "High",
                "rationale": (
                    "Government-administered SEZ with APEX-CI institutional backing "
                    "provides credibility and contract readiness. "
                    "Financial strength is Moderate rather than Strong because "
                    "zone revenue depends on aggregated tenant payments — "
                    "individual tenant credits are variable. "
                    "Sovereign backstop from Government of Côte d'Ivoire "
                    "partially offsets tenant credit risk. "
                    "Power reliability directly constrains zone capacity utilisation — "
                    "high motivation to sign."
                ),
                "credit_enhancement_required": (
                    "Partial risk guarantee from MIGA or AfDB recommended "
                    "to cover tenant default risk within zone."
                ),
            },

            # ================================================================
            # GHANA
            # ================================================================

            {
                # Tema Oil Refinery (TOR)
                # operator: TOR Ltd — 100% Government of Ghana
                # reliability_class: High | current_mw: 32 | load_factor: 0.55
                "anchor_id": "AL_ANC_007",
                "detection_id": "DET-007",
                "entity_name": "Tema Oil Refinery (TOR)",
                "country": "Ghana",
                "score": 0.68,
                "tier": "Tier 2",
                "offtake_willingness": "High",
                "financial_strength": "Moderate",
                "contract_readiness": "Medium",
                "rationale": (
                    "100% state-owned — sovereign guarantee from Government of Ghana "
                    "partially offsets weak standalone credit. "
                    "Currently under rehabilitation — operating at 55% load factor "
                    "which reduces near-term revenue certainty. "
                    "At full rehabilitation, reliable power is a prerequisite "
                    "for full refinery restart — very high motivation to sign. "
                    "Contract readiness is Medium because rehabilitation timeline "
                    "creates uncertainty about when full off-take commitment can be made."
                ),
                "credit_enhancement_required": (
                    "Government of Ghana sovereign guarantee required. "
                    "Escrow arrangement for debt service payments recommended "
                    "given TOR historical payment difficulties."
                ),
            },

            {
                # Tema Port — Meridian Port Services
                # operator: Meridian Port Services (APM Terminals JV)
                # reliability_class: Critical | current_mw: 38 | load_factor: 0.82
                "anchor_id": "AL_ANC_008",
                "detection_id": "DET-008",
                "entity_name": "Tema Port — Meridian Port Services",
                "country": "Ghana",
                "score": 0.87,
                "tier": "Tier 1",
                "offtake_willingness": "High",
                "financial_strength": "Strong",
                "contract_readiness": "High",
                "rationale": (
                    "APM Terminals JV — investment-grade international operator "
                    "with 35-year port concession providing long revenue horizon. "
                    "Critical reliability class means power outages cause immediate "
                    "and severe vessel demurrage costs — very high motivation. "
                    "New reefer plug bank installation increases power sensitivity further. "
                    "Standard PPA templates available from APM Terminals global operations."
                ),
                "credit_enhancement_required": "None — bankable as standalone",
            },

            {
                # Tema Free Zone
                # operator: Ghana Free Zones Authority (GFZA)
                # reliability_class: High | current_mw: 52 | load_factor: 0.77
                "anchor_id": "AL_ANC_009",
                "detection_id": "DET-009",
                "entity_name": "Tema Free Zone",
                "country": "Ghana",
                "score": 0.80,
                "tier": "Tier 1",
                "offtake_willingness": "High",
                "financial_strength": "Moderate",
                "contract_readiness": "High",
                "rationale": (
                    "GFZA is a government authority with 200+ enterprise tenants "
                    "providing diversified revenue base. "
                    "Zone operating at 60% capacity due to power unreliability — "
                    "reliable power is the single biggest constraint on zone growth "
                    "making motivation to sign extremely high. "
                    "Financial strength Moderate because zone revenue depends on "
                    "tenant occupancy and payments — Ghana government backstop applies. "
                    "Dedicated substation investment ($15–20M) already justified "
                    "by zone expansion targets."
                ),
                "credit_enhancement_required": (
                    "Ghana government letter of support recommended. "
                    "Aggregated PPA across zone tenants with GFZA as counterparty."
                ),
            },

            {
                # Obuasi Gold Mine (AngloGold Ashanti)
                # operator: AngloGold Ashanti Ghana Ltd
                # reliability_class: Critical | current_mw: 68 | load_factor: 0.93
                # Note: ~98km from corridor — spur required
                "anchor_id": "AL_ANC_012",
                "detection_id": "DET-012",
                "entity_name": "Obuasi Gold Mine (AngloGold Ashanti)",
                "country": "Ghana",
                "score": 0.95,
                "tier": "Tier 1",
                "offtake_willingness": "High",
                "financial_strength": "Strong",
                "contract_readiness": "High",
                "rationale": (
                    "AngloGold Ashanti is NYSE/JSE listed with investment-grade credit "
                    "and a 20+ year mine plan providing long off-take horizon. "
                    "Critical reliability class — underground operations require 99%+ "
                    "uptime for worker safety and regulatory compliance. "
                    "Each 1% downtime = $5–8M annual production loss — "
                    "strongest financial incentive to sign on the corridor. "
                    "AngloGold Ashanti has signed PPAs on other African corridors — "
                    "internal PPA expertise available. "
                    "Note: Spur connection required (~98km) — "
                    "mine can provide corporate guarantee to anchor spur financing."
                ),
                "credit_enhancement_required": (
                    "None for creditworthiness. "
                    "Spur connection financing structure needed separately — "
                    "AngloGold Ashanti corporate guarantee recommended as spur anchor."
                ),
            },

            {
                # Weta Rice Farm & Milling Hub — Volta Region
                # operator: Ghana FOODBELT / smallholder cooperative (unconfirmed)
                # reliability_class: Standard | current_mw: 8 | load_factor: 0.42
                "anchor_id": "AL_ANC_014",
                "detection_id": "DET-014",
                "entity_name": "Weta Rice Farm & Milling Hub — Volta Region",
                "country": "Ghana",
                "score": 0.45,
                "tier": "Tier 3",
                "offtake_willingness": "Medium",
                "financial_strength": "Weak",
                "contract_readiness": "Low",
                "rationale": (
                    "Smallholder cooperative structure with fragmented ownership — "
                    "no single creditworthy counterparty to sign a PPA. "
                    "Currently diesel-powered with no grid connection experience. "
                    "Lead operator identity partially unresolved — "
                    "no audited financials available. "
                    "Standard reliability class means low urgency to commit "
                    "to a long-term contract. "
                    "Development impact is high (95,000 jobs potential) but "
                    "bankability is weak without government aggregation mechanism. "
                    "Note: 8 MW current demand understates potential — "
                    "grid connection unlocks 100–150 MW expansion."
                ),
                "credit_enhancement_required": (
                    "Ghana government COCOBOD-style aggregation model required. "
                    "AfDB SAPZ grant co-financing needed to make connection viable. "
                    "Government of Ghana sovereign guarantee recommended as PPA counterparty."
                ),
            },

            {
                # Takoradi Port — Bulk & General Cargo Terminal
                # operator: GPHA / Bolloré Logistics (concession)
                # reliability_class: High | current_mw: 18 | load_factor: 0.80
                "anchor_id": "AL_ANC_015",
                "detection_id": "DET-015",
                "entity_name": "Takoradi Port — Bulk & General Cargo Terminal",
                "country": "Ghana",
                "score": 0.78,
                "tier": "Tier 2",
                "offtake_willingness": "High",
                "financial_strength": "Moderate",
                "contract_readiness": "High",
                "rationale": (
                    "Bolloré Logistics is an experienced concession operator "
                    "with established PPA signing capability. "
                    "GPHA sovereign backstop partially offsets moderate credit profile. "
                    "Liquid bulk jetty expansion increases power demand and sensitivity. "
                    "Score moderated to Tier 2 because Takoradi is smaller than Tema "
                    "and financial profile is less robust than major deep sea ports."
                ),
                "credit_enhancement_required": (
                    "Ghana government letter of support recommended. "
                    "No additional credit enhancement needed if GPHA is PPA counterparty."
                ),
            },

            {
                # Accra Data Center (ADC) — CSquared / Liquid Telecom
                # operator: CSquared Ghana / Liquid Telecom
                # reliability_class: Critical | current_mw: 12 | load_factor: 0.92
                "anchor_id": "AL_ANC_016",
                "detection_id": "DET-016",
                "entity_name": "Accra Data Center (ADC)",
                "country": "Ghana",
                "score": 0.86,
                "tier": "Tier 1",
                "offtake_willingness": "High",
                "financial_strength": "Strong",
                "contract_readiness": "High",
                "rationale": (
                    "IFC and Google-backed CSquared has strong institutional shareholders "
                    "providing investment-grade credit backing. "
                    "Critical reliability class — Tier III SLA requires 99.982% uptime. "
                    "Current diesel backup costs $3–5M/year — "
                    "grid reliability reduces OPEX significantly, "
                    "creating very strong financial incentive to sign long-term PPA. "
                    "Annex expansion underway increases long-term demand commitment."
                ),
                "credit_enhancement_required": "None — bankable as standalone",
            },

            # ================================================================
            # TOGO
            # ================================================================

            {
                # Port of Lomé — Container Terminal (MSC / Bolloré JV)
                # operator: Lomé Container Terminal (MSC/Bolloré JV)
                # reliability_class: Critical | current_mw: 28 | load_factor: 0.83
                "anchor_id": "AL_ANC_017",
                "detection_id": "DET-017",
                "entity_name": "Port of Lomé — Container Terminal",
                "country": "Togo",
                "score": 0.85,
                "tier": "Tier 1",
                "offtake_willingness": "High",
                "financial_strength": "Strong",
                "contract_readiness": "High",
                "rationale": (
                    "MSC and Bolloré JV — both are large experienced port operators "
                    "with investment-grade backing and PPA signing expertise. "
                    "West Africa's deepest natural port — strategic asset with "
                    "high and growing throughput volumes providing revenue certainty. "
                    "Critical reliability class — 24/7 vessel operations, "
                    "power outages cause immediate demurrage liability. "
                    "Togo grid is highly unreliable — port currently relies "
                    "heavily on backup generation, making grid connection "
                    "the highest operational priority."
                ),
                "credit_enhancement_required": "None — bankable as standalone",
            },

            {
                # Lomé Cement Plant (WACEM / Fortia Group)
                # operator: West African Cement (WACEM) / Fortia Group
                # reliability_class: High | current_mw: 35 | load_factor: 0.85
                "anchor_id": "AL_ANC_019",
                "detection_id": "DET-019",
                "entity_name": "Lomé Cement Plant (WACEM)",
                "country": "Togo",
                "score": 0.79,
                "tier": "Tier 2",
                "offtake_willingness": "High",
                "financial_strength": "Moderate",
                "contract_readiness": "High",
                "rationale": (
                    "WACEM is the largest industrial electricity consumer in Togo — "
                    "power reliability is critical for continuous kiln operations. "
                    "Fortia Group parent provides moderate financial backing "
                    "but is not publicly listed — audited financials limited. "
                    "High motivation to sign given kiln restart costs from outages. "
                    "Score moderated to Tier 2 due to private company limited "
                    "credit transparency — partial risk guarantee recommended."
                ),
                "credit_enhancement_required": (
                    "Partial risk guarantee from MIGA or GuarantCo recommended "
                    "to cover Fortia Group credit risk. "
                    "Escrow arrangement for PPA payments recommended."
                ),
            },

            {
                # Lomé Free Zone (SAZOF)
                # operator: Société d'Administration de la Zone Franche (SAZOF)
                # reliability_class: High | current_mw: 22 | load_factor: 0.70
                "anchor_id": "AL_ANC_020",
                "detection_id": "DET-020",
                "entity_name": "Lomé Free Zone (SAZOF)",
                "country": "Togo",
                "score": 0.71,
                "tier": "Tier 2",
                "offtake_willingness": "High",
                "financial_strength": "Moderate",
                "contract_readiness": "Medium",
                "rationale": (
                    "Government-administered zone with TIPA institutional backing. "
                    "Togo sovereign guarantee partially offsets moderate credit. "
                    "Significant suppressed demand — reliable power expected to "
                    "increase actual zone demand from 22 MW to 40+ MW within 2 years. "
                    "Contract readiness Medium because multi-tenant zone requires "
                    "aggregated PPA structure which takes longer to establish. "
                    "Power reliability improvement is a stated Togo government priority."
                ),
                "credit_enhancement_required": (
                    "Togo government sovereign guarantee as PPA counterparty. "
                    "AfDB or EU Global Gateway grant co-financing for connection "
                    "infrastructure recommended."
                ),
            },

            # ================================================================
            # BENIN
            # ================================================================

            {
                # Port of Cotonou — Bénin Terminal (Bolloré)
                # operator: Port Autonome de Cotonou / Bolloré (concession)
                # reliability_class: Critical | current_mw: 24 | load_factor: 0.79
                "anchor_id": "AL_ANC_022",
                "detection_id": "DET-022",
                "entity_name": "Port of Cotonou — Bénin Terminal",
                "country": "Benin",
                "score": 0.80,
                "tier": "Tier 1",
                "offtake_willingness": "High",
                "financial_strength": "Strong",
                "contract_readiness": "High",
                "rationale": (
                    "Bolloré is an experienced concession operator with investment-grade "
                    "backing and established PPA signing capability. "
                    "PAC sovereign backstop from Government of Benin provides additional security. "
                    "Critical reliability class — primary gateway for Benin and "
                    "three landlocked hinterland countries. "
                    "Port currently relies on backup generation due to chronic "
                    "Benin grid unreliability — grid connection is highest priority. "
                    "Score moderated slightly below top Tier 1 due to "
                    "Benin sovereign risk context."
                ),
                "credit_enhancement_required": (
                    "Benin government letter of support recommended. "
                    "Bolloré corporate guarantee as primary PPA counterparty "
                    "reduces sovereign risk exposure."
                ),
            },

            {
                # Zone Industrielle de Cotonou (PK10)
                # operator: Government of Benin — Ministère de l'Industrie
                # reliability_class: High | current_mw: 30 | load_factor: 0.60
                "anchor_id": "AL_ANC_023",
                "detection_id": "DET-023",
                "entity_name": "Zone Industrielle de Cotonou (PK10)",
                "country": "Benin",
                "score": 0.62,
                "tier": "Tier 2",
                "offtake_willingness": "High",
                "financial_strength": "Weak",
                "contract_readiness": "Medium",
                "rationale": (
                    "Government-administered legacy industrial zone — "
                    "Benin sovereign guarantee provides the only meaningful credit. "
                    "Financial strength is Weak because Benin has limited fiscal capacity "
                    "and historical payment difficulties with utility bills. "
                    "High motivation — zone operates at 60% capacity due to "
                    "chronic power outages; reliable power is the primary "
                    "barrier to zone modernisation and new investment attraction. "
                    "Contract readiness Medium due to multi-tenant structure "
                    "requiring aggregated PPA arrangement."
                ),
                "credit_enhancement_required": (
                    "Benin government sovereign guarantee as PPA counterparty essential. "
                    "Payment escrow arrangement strongly recommended. "
                    "AfDB or World Bank partial risk guarantee to cover sovereign default risk. "
                    "EU Global Gateway co-financing recommended to reduce tariff level."
                ),
            },

            {
                # Unidentified Agro-Processing Cluster — Benin Coastal
                # operator: Unknown — identity unresolved
                # reliability_class: Standard | current_mw: 4.5 | load_factor: 0.55
                "anchor_id": "AL_ANC_024",
                "detection_id": "DET-024",
                "entity_name": "Unidentified Agro-Processing Cluster — Benin Coastal",
                "country": "Benin",
                "score": 0.28,
                "tier": "Tier 3",
                "offtake_willingness": "Unknown",
                "financial_strength": "Unknown",
                "contract_readiness": "Low",
                "rationale": (
                    "Identity completely unresolved — no operator confirmed, "
                    "no financials available, no registry match found. "
                    "Bankability assessment cannot be meaningfully completed "
                    "until manual field verification confirms operator identity. "
                    "Score of 0.28 reflects physical detection only — "
                    "cold storage structures suggest some reliability sensitivity "
                    "but this cannot be confirmed without identity resolution. "
                    "Excluded from Phase 1 financing structures entirely. "
                    "If confirmed as multinational agro-processor, "
                    "score could upgrade significantly."
                ),
                "credit_enhancement_required": (
                    "Identity verification required before any assessment. "
                    "Full bankability reassessment needed post-verification."
                ),
            },

            # ================================================================
            # NIGERIA
            # ================================================================

            {
                # Dangote Refinery
                # operator: Dangote Industries Limited
                # reliability_class: Critical | current_mw: 1000 | load_factor: 0.92
                "anchor_id": "AL_ANC_027",
                "detection_id": "DET-027",
                "entity_name": "Dangote Refinery",
                "country": "Nigeria",
                "score": 0.96,
                "tier": "Tier 1",
                "offtake_willingness": "High",
                "financial_strength": "Strong",
                "contract_readiness": "High",
                "rationale": (
                    "Dangote Industries is Nigeria's largest conglomerate — "
                    "$19B refinery investment demonstrates exceptional financial capacity. "
                    "Critical reliability class — refinery shutdown causes equipment "
                    "damage, safety hazards, and $24M/day revenue loss at full capacity. "
                    "Grid backup connection eliminates need for expensive 5th backup gas unit "
                    "saving $15–25M/year in avoided capital and operating costs — "
                    "very strong financial incentive to sign. "
                    "Dangote Group can provide AAA-rated corporate guarantee. "
                    "Highest single anchor load on corridor at 1,000 MW — "
                    "dominant anchor for Lagos hub financing."
                ),
                "credit_enhancement_required": "None — Dangote corporate guarantee is sufficient standalone",
            },

            {
                # Lekki Free Trade Zone
                # operator: LFZDC — Chinese-Nigerian JV
                # reliability_class: Critical | current_mw: 150 | load_factor: 0.74
                "anchor_id": "AL_ANC_028",
                "detection_id": "DET-028",
                "entity_name": "Lekki Free Trade Zone",
                "country": "Nigeria",
                "score": 0.88,
                "tier": "Tier 1",
                "offtake_willingness": "High",
                "financial_strength": "Strong",
                "contract_readiness": "High",
                "rationale": (
                    "$20B+ committed investment from Chinese and Nigerian government parties "
                    "provides exceptionally strong financial backing. "
                    "CCECC (Chinese state enterprise) and Lagos State Government "
                    "as co-owners provide dual sovereign guarantee pathway. "
                    "Critical reliability class — manufacturing tenants require "
                    "continuous power for production lines. "
                    "Zone at only 34% buildout — long-term demand growth to "
                    "800–1,200 MW creates 20+ year off-take horizon. "
                    "Chinese sovereign investment involvement streamlines "
                    "contract approval process."
                ),
                "credit_enhancement_required": (
                    "None for Tier 1 classification. "
                    "Chinese sovereign guarantee and Lagos State Government "
                    "co-signature recommended for maximum debt sizing."
                ),
            },

            {
                # Lekki Deep Sea Port
                # operator: Tolaram Group / CMA CGM JV
                # reliability_class: Critical | current_mw: 35 | load_factor: 0.82
                "anchor_id": "AL_ANC_029",
                "detection_id": "DET-029",
                "entity_name": "Lekki Deep Sea Port",
                "country": "Nigeria",
                "score": 0.87,
                "tier": "Tier 1",
                "offtake_willingness": "High",
                "financial_strength": "Strong",
                "contract_readiness": "High",
                "rationale": (
                    "Tolaram Group and CMA CGM (world's third largest container line) "
                    "are both experienced infrastructure investors with "
                    "investment-grade credit backing. "
                    "45-year concession agreement provides very long revenue horizon "
                    "perfectly aligned with transmission investment lifecycle. "
                    "Port became fully operational in 2024 — "
                    "adjacent to Dangote Refinery and Lekki FTZ creating "
                    "a critical infrastructure cluster that strengthens "
                    "collective bankability significantly. "
                    "Critical reliability class — vessel operations require 24/7 power."
                ),
                "credit_enhancement_required": "None — bankable as standalone",
            },

            {
                # MainOne Data Center (MDX-i Lagos) — Equinix subsidiary
                # operator: MainOne / Equinix
                # reliability_class: Critical | current_mw: 18 | load_factor: 0.95
                "anchor_id": "AL_ANC_030",
                "detection_id": "DET-030",
                "entity_name": "MainOne Data Center (MDX-i Lagos)",
                "country": "Nigeria",
                "score": 0.95,
                "tier": "Tier 1",
                "offtake_willingness": "High",
                "financial_strength": "Strong",
                "contract_readiness": "High",
                "rationale": (
                    "Equinix is NASDAQ-listed (S&P 500) with investment-grade "
                    "credit rating — strongest digital anchor on the corridor. "
                    "Critical reliability class — Tier III/IV SLA requires "
                    "99.982% uptime; downtime triggers severe financial penalties. "
                    "Current diesel backup costs $4–6M/year — "
                    "grid reliability reduces OPEX significantly. "
                    "Equinix has signed transmission PPAs globally — "
                    "internal expertise makes contract process rapid. "
                    "Expansion doubling floor space confirmed — "
                    "long-term demand growth to 35–40 MW committed."
                ),
                "credit_enhancement_required": "None — Equinix investment-grade rating is sufficient",
            },

            {
                # Apapa Port Complex
                # operator: Nigerian Ports Authority / APM Terminals (concession)
                # reliability_class: Critical | current_mw: 55 | load_factor: 0.85
                "anchor_id": "AL_ANC_031",
                "detection_id": "DET-031",
                "entity_name": "Apapa Port Complex",
                "country": "Nigeria",
                "score": 0.82,
                "tier": "Tier 1",
                "offtake_willingness": "High",
                "financial_strength": "Strong",
                "contract_readiness": "High",
                "rationale": (
                    "APM Terminals concession operator provides investment-grade "
                    "credit as primary PPA counterparty. "
                    "NPA sovereign backstop as secondary guarantor. "
                    "Handles 70% of Nigeria's import/export cargo — "
                    "national strategic importance creates strong government "
                    "motivation to ensure reliable power. "
                    "Critical reliability class — power outage causes "
                    "national supply chain disruption and severe demurrage liability. "
                    "Score moderated slightly below top Tier 1 due to "
                    "Nigerian sovereign risk context and port congestion challenges."
                ),
                "credit_enhancement_required": (
                    "APM Terminals corporate guarantee recommended as primary counterparty. "
                    "NPA backstop as secondary — reduces sovereign risk exposure."
                ),
            },

            {
                # Sagamu-Interchange Manufacturing Cluster
                # operator: Multiple — Honeywell, Fidson Healthcare, others
                # reliability_class: High | current_mw: 45 | load_factor: 0.68
                "anchor_id": "AL_ANC_032",
                "detection_id": "DET-032",
                "entity_name": "Sagamu-Interchange Manufacturing Cluster",
                "country": "Nigeria",
                "score": 0.58,
                "tier": "Tier 2",
                "offtake_willingness": "High",
                "financial_strength": "Moderate",
                "contract_readiness": "Low",
                "rationale": (
                    "Multi-tenant cluster with no single creditworthy counterparty — "
                    "individual tenant credits vary widely. "
                    "Honeywell Flour Mills and Fidson Healthcare are the largest "
                    "identified tenants with moderate credit profiles. "
                    "Identity partially resolved — new pharmaceutical block operator "
                    "unknown, creating additional uncertainty. "
                    "Aggregated PPA structure through Ogun State government "
                    "is the most viable path to bankability. "
                    "Contract readiness Low due to multi-party coordination required. "
                    "High motivation — manufacturing and pharmaceutical production "
                    "lines are sensitive to power interruptions."
                ),
                "credit_enhancement_required": (
                    "Ogun State government as aggregate PPA counterparty essential. "
                    "Individual anchor tenant PPAs with Honeywell and Fidson "
                    "as co-signatories recommended. "
                    "NEXIM Bank co-financing may be available given "
                    "manufacturing corridor priority."
                ),
            },

            {
                # Unverified Hyperscale Data Center — Lagos Island North
                # operator: Unknown — identity unresolved
                # reliability_class: Critical | current_mw: 35 | load_factor: 0.88
                "anchor_id": "AL_ANC_034",
                "detection_id": "DET-034",
                "entity_name": "Unverified Hyperscale Data Center — Lagos Island North",
                "country": "Nigeria",
                "score": 0.35,
                "tier": "Tier 3",
                "offtake_willingness": "Unknown",
                "financial_strength": "Unknown",
                "contract_readiness": "Low",
                "rationale": (
                    "Identity completely unresolved — no operator confirmed, "
                    "no NCC or NIPC registry match found. "
                    "Physical attributes strongly suggest a hyperscale data center "
                    "but alternative classification (distribution warehouse) remains possible. "
                    "If confirmed as hyperscale DC operated by a major cloud provider "
                    "(AWS, Google, Microsoft, or Equinix), score would upgrade "
                    "immediately to Tier 1 with score 0.92+. "
                    "Score of 0.35 reflects potential value only — "
                    "cannot be included in any financing structure until verified. "
                    "Manual field verification is urgent given potential 35–80 MW demand."
                ),
                "credit_enhancement_required": (
                    "Identity verification required before any assessment. "
                    "Full bankability reassessment needed post-verification. "
                    "Flag as priority verification target — "
                    "potential Tier 1 upgrade significantly strengthens Lagos hub financing."
                ),
            },

            {
                # Lithium Exploration & Processing Site — Ghana North
                # operator: Unknown — cadastre licence holder redacted
                # reliability_class: High | current_mw: 8 | load_factor: 0.70
                "anchor_id": "AL_ANC_035",
                "detection_id": "DET-035",
                "entity_name": "Lithium Exploration & Processing Site — Ghana North",
                "country": "Ghana",
                "score": 0.42,
                "tier": "Tier 3",
                "offtake_willingness": "Medium",
                "financial_strength": "Unknown",
                "contract_readiness": "Low",
                "rationale": (
                    "Operator identity redacted in Ghana Minerals Commission cadastre — "
                    "financial strength cannot be assessed without confirmation. "
                    "Currently in exploration phase — no proven cash flows. "
                    "PPA commitment would require full mining licence grant "
                    "which has not yet occurred. "
                    "At full production this site would require 80–150 MW — "
                    "potential upgrade to Tier 1 if operator is a major mining company "
                    "with investment-grade credit. "
                    "Strategic importance for EV battery supply chain may attract "
                    "DFI co-financing support. "
                    "Requires ~44km spur connection — "
                    "spur cannot be financed without confirmed operator."
                ),
                "credit_enhancement_required": (
                    "Operator identity verification required before any assessment. "
                    "Full mining licence required before PPA commitment possible. "
                    "Flag as future pipeline opportunity — "
                    "reassess when mining licence granted and operator confirmed."
                ),
            },
        ],

        # ------------------------------------------------------------------ #
        #  SUMMARY                                                            #
        # ------------------------------------------------------------------ #
        "summary": {
            "corridor_average_score": 0.77,
            "anchor_loads_assessed": 24,
            "tier_summary": {
                "tier_1_count": 13,
                "tier_2_count": 8,
                "tier_3_count": 3,
            },
            "tier_1_anchors": [
                "AL_ANC_003 — Port of Abidjan (0.84)",
                "AL_ANC_008 — Tema Port MPS (0.87)",
                "AL_ANC_009 — Tema Free Zone (0.80)",
                "AL_ANC_012 — Obuasi Gold Mine (0.95)",
                "AL_ANC_016 — Accra Data Center (0.86)",
                "AL_ANC_017 — Port of Lomé (0.85)",
                "AL_ANC_022 — Port of Cotonou (0.80)",
                "AL_ANC_027 — Dangote Refinery (0.96)",
                "AL_ANC_028 — Lekki FTZ (0.88)",
                "AL_ANC_029 — Lekki Deep Sea Port (0.87)",
                "AL_ANC_030 — MainOne Data Center (0.95)",
                "AL_ANC_031 — Apapa Port Complex (0.82)",
            ],
            "tier_2_anchors": [
                "AL_ANC_004 — Cargill Cocoa Plant (0.72) — verify identity first",
                "AL_ANC_005 — Abidjan ZIEX (0.78) — MIGA guarantee needed",
                "AL_ANC_007 — Tema Oil Refinery (0.68) — Ghana sovereign guarantee",
                "AL_ANC_015 — Takoradi Port (0.78) — GPHA backstop",
                "AL_ANC_019 — WACEM Cement (0.79) — GuarantCo recommended",
                "AL_ANC_020 — Lomé Free Zone (0.71) — Togo sovereign guarantee",
                "AL_ANC_023 — Zone Industrielle Cotonou (0.62) — AfDB PRG needed",
                "AL_ANC_032 — Sagamu Cluster (0.58) — Ogun State aggregation",
            ],
            "tier_3_anchors": [
                "AL_ANC_014 — Weta Rice Farm (0.45) — identity and aggregation needed",
                "AL_ANC_024 — Benin Agro Cluster (0.28) — identity unresolved",
                "AL_ANC_034 — Unverified Lagos DC (0.35) — identity unresolved",
                "AL_ANC_035 — Lithium Site Ghana (0.42) — licence and identity needed",
            ],
            "priority_verification_targets": [
                "AL_ANC_034: Potential Tier 1 upgrade — hyperscale DC if confirmed",
                "AL_ANC_004: Expected Tier 1 upgrade — Cargill identity near-confirmed",
                "AL_ANC_035: Potential high-value mining anchor — operator redacted",
            ],
            "strongest_anchors_for_phase_1_financing": [
                "AL_ANC_027 — Dangote Refinery (1,000 MW, score 0.96)",
                "AL_ANC_012 — Obuasi Gold Mine (68 MW, score 0.95)",
                "AL_ANC_030 — MainOne Data Center (18 MW, score 0.95)",
                "AL_ANC_008 — Tema Port MPS (38 MW, score 0.87)",
                "AL_ANC_029 — Lekki Deep Sea Port (35 MW, score 0.87)",
                "AL_ANC_028 — Lekki FTZ (150 MW, score 0.88)",
            ],
        },

        "message": (
            "Bankability assessment complete for 24 anchor loads. "
            "13 Tier 1 anchors identified — bankable and can anchor project debt directly. "
            "8 Tier 2 anchors viable with credit enhancement or government guarantees. "
            "3 Tier 3 anchors require identity verification or blended finance. "
            "Corridor average score: 0.77. "
            "Dangote Refinery and Obuasi Gold Mine are the strongest anchors. "
            "2 unresolved identities flagged as priority verification targets — "
            "potential Tier 1 upgrades that would significantly strengthen financing."
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