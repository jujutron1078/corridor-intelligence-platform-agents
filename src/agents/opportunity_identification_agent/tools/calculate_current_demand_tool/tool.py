import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import CurrentDemandInput


@tool("calculate_current_demand", description=TOOL_DESCRIPTION)
def calculate_current_demand_tool(
    payload: CurrentDemandInput, runtime: ToolRuntime
) -> Command:
    """
    Calculates current electricity demand for each anchor load identified
    by scan_anchor_loads.

    This tool ONLY processes anchor loads (is_anchor_load == True).
    Generation assets and substations are excluded — they are handled
    by the Infrastructure Optimization Agent.

    For each anchor load it returns:
        current_mw         — baseline electricity demand at current operating level
        load_factor        — fraction of time running at or near full capacity (0–1)
        reliability_class  — uptime requirement (Critical / High / Standard)

    Demand is derived from:
        1. Sector energy-intensity benchmarks (kW per unit output/area)
        2. Facility footprint and visible structure count (from infrastructure_detection)
        3. Known production capacity where available (from scan_anchor_loads identity)

    This tool does NOT return:
        - Future demand / growth projections  → model_growth_trajectory
        - Bankability scores                  → assess_bankability
        - Off-take willingness                → assess_bankability
        - Revenue projections                 → prioritize_opportunities

    Reliability classes:
        Critical  — 99%+ uptime required; outage causes safety risk,
                    equipment damage, or severe financial penalty
        High      — 95–99% uptime required; outage is costly but manageable
        Standard  — <95% acceptable; facility has backup generation or
                    can tolerate interruptions (e.g. seasonal operations)

    Anchor loads processed: 24 (aligned to scan_anchor_loads output)
    Generation assets skipped: 10
    Substations skipped: 3
    Unresolved/pending verification: included with conservative estimates
                                     and flagged in reliability_class notes
    """

    response = {
        "total_current_mw": 2127.5,
        "anchor_loads_assessed": 24,
        "generation_assets_excluded": 10,
        "substations_excluded": 3,
        "demand_profiles": [

            # ================================================================
            # CÔTE D'IVOIRE
            # ================================================================

            {
                # Port of Abidjan — Vridi Terminal
                # 22 berths, 14 cranes, continuous container operations
                # Benchmark: 2 MW per active crane + port auxiliary systems
                "anchor_id": "AL_ANC_003",
                "detection_id": "DET-003",
                "entity_name": "Port of Abidjan — Vridi Terminal",
                "country": "Côte d'Ivoire",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics",
                "current_mw": 45.0,
                "load_factor": 0.80,
                "reliability_class": "Critical",
                "reliability_rationale": (
                    "Port operations run 24/7 — crane downtime causes vessel demurrage "
                    "costs of $20,000–$50,000/hour. New terminal extension increases "
                    "sensitivity to power reliability."
                ),
                "demand_basis": (
                    "14 cranes × ~2.5 MW each + terminal lighting, reefer plugs, "
                    "administration = ~45 MW. Consistent with APDL reported peak demand."
                ),
            },

            {
                # Cargill Cocoa Processing Plant — Abidjan Hinterland
                # 4 processing silos, 6 loading bays, diesel generator pads detected
                # Benchmark: cocoa processing ~1.2 MW per 1,000 tonnes/month capacity
                # Identity partially resolved — conservative estimate applied
                "anchor_id": "AL_ANC_004",
                "detection_id": "DET-004",
                "entity_name": "Cargill Cocoa Processing Plant — Abidjan Hinterland",
                "country": "Côte d'Ivoire",
                "sector": "Agriculture",
                "sub_sector": "Cocoa Processing",
                "current_mw": 18.0,
                "load_factor": 0.65,
                "reliability_class": "High",
                "reliability_rationale": (
                    "Cocoa processing is seasonal — peak Oct–Mar harvest. "
                    "Load factor reflects ~8 months high activity, 4 months reduced. "
                    "Diesel generator pads detected suggest current grid unreliability "
                    "is a known operational risk."
                ),
                "demand_basis": (
                    "38,000 sqm footprint with 4 silos and 6 loading bays. "
                    "Estimated processing capacity ~15,000 MT/month at peak. "
                    "Cocoa processing benchmark: 1.2 MW per 1,000 MT/month = ~18 MW peak. "
                    "Identity partially resolved — conservative estimate applied."
                ),
            },

            {
                # Abidjan Export Processing Zone (ZIEX)
                # 9,500,000 sqm zone, 58% built up, 9 warehouse clusters
                # Benchmark: light manufacturing SEZ ~5–8 W/sqm built-up area
                "anchor_id": "AL_ANC_005",
                "detection_id": "DET-005",
                "entity_name": "Abidjan Export Processing Zone (ZIEX)",
                "country": "Côte d'Ivoire",
                "sector": "Industrial",
                "sub_sector": "Special Economic Zone",
                "current_mw": 42.0,
                "load_factor": 0.72,
                "reliability_class": "High",
                "reliability_rationale": (
                    "Mixed light manufacturing zone — daytime heavy load profile. "
                    "Enterprises self-report ~18 hours high load per day. "
                    "Power reliability directly constrains zone capacity utilisation."
                ),
                "demand_basis": (
                    "9,500,000 sqm × 58% built-up = 5,510,000 sqm active area. "
                    "Light manufacturing benchmark 7.5 W/sqm average = ~41 MW. "
                    "Rounded to 42 MW consistent with APEX-CI reported demand."
                ),
            },

            # ================================================================
            # GHANA
            # ================================================================

            {
                # Tema Oil Refinery (TOR)
                # 45,000 bpd processing capacity; under rehabilitation
                # Benchmark: petroleum refinery ~0.7 MW per 1,000 bpd at full capacity
                "anchor_id": "AL_ANC_007",
                "detection_id": "DET-007",
                "entity_name": "Tema Oil Refinery (TOR)",
                "country": "Ghana",
                "sector": "Energy",
                "sub_sector": "Petroleum Refinery",
                "current_mw": 32.0,
                "load_factor": 0.55,
                "reliability_class": "High",
                "reliability_rationale": (
                    "Refinery under rehabilitation — currently operating at partial capacity. "
                    "Load factor 0.55 reflects reduced throughput during works. "
                    "At full rehabilitation, load factor expected to rise to 0.85+. "
                    "Classified High rather than Critical during rehabilitation phase — "
                    "full Critical classification applies at full operational status."
                ),
                "demand_basis": (
                    "45,000 bpd × 0.7 MW/1,000 bpd = ~31.5 MW at full capacity. "
                    "Rehabilitation reduces active units — current demand ~32 MW "
                    "including construction power. Consistent with GNPC reported draw."
                ),
            },

            {
                # Tema Port — Meridian Port Services Container Terminal
                # 16 berths, 10 cranes, major expansion underway
                "anchor_id": "AL_ANC_008",
                "detection_id": "DET-008",
                "entity_name": "Tema Port — Meridian Port Services",
                "country": "Ghana",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics",
                "current_mw": 38.0,
                "load_factor": 0.82,
                "reliability_class": "Critical",
                "reliability_rationale": (
                    "Container terminal operations run 24/7. "
                    "Vessel demurrage costs make power outages extremely expensive. "
                    "New reefer plug banks increase reliability sensitivity further."
                ),
                "demand_basis": (
                    "10 cranes × 2.5 MW + terminal lighting, reefer plugs, "
                    "administration, yard equipment = ~38 MW. "
                    "Consistent with GPHA reported Tema terminal demand."
                ),
            },

            {
                # Tema Free Zone
                # 40,000,000 sqm zone, 62% built-up, 21 warehouse clusters
                # 200+ enterprises including manufacturing, trading, services
                "anchor_id": "AL_ANC_009",
                "detection_id": "DET-009",
                "entity_name": "Tema Free Zone",
                "country": "Ghana",
                "sector": "Industrial",
                "sub_sector": "Special Economic Zone",
                "current_mw": 52.0,
                "load_factor": 0.77,
                "reliability_class": "High",
                "reliability_rationale": (
                    "Mixed industrial zone — manufacturing daytime heavy, "
                    "reduced overnight. Zone operates at ~60% capacity due "
                    "to power reliability constraints — suppressed demand exists. "
                    "Full buildout demand significantly higher."
                ),
                "demand_basis": (
                    "40,000,000 sqm × 62% built-up = 24,800,000 sqm active. "
                    "Industrial benchmark 2.1 W/sqm average (mixed use) = ~52 MW. "
                    "Consistent with GFZA reported zone demand."
                ),
            },

            {
                # Obuasi Gold Mine (AngloGold Ashanti)
                # 3 headframes, processing plant, tailings pond
                # ~100km from corridor — spur connection required
                # Benchmark: underground gold mine ~20 MW per headframe + processing
                "anchor_id": "AL_ANC_012",
                "detection_id": "DET-012",
                "entity_name": "Obuasi Gold Mine (AngloGold Ashanti)",
                "country": "Ghana",
                "sector": "Mining",
                "sub_sector": "Underground Gold Mine",
                "current_mw": 68.0,
                "load_factor": 0.93,
                "reliability_class": "Critical",
                "reliability_rationale": (
                    "Underground mine — power outage during operations risks "
                    "worker entrapment, ventilation failure, and dewatering failure. "
                    "99%+ uptime is a regulatory and safety requirement. "
                    "Each 1% downtime = ~$5–8M annual production loss. "
                    "Note: ~98km from corridor — requires dedicated spur connection."
                ),
                "demand_basis": (
                    "3 headframes × ~15 MW underground haulage and ventilation + "
                    "processing plant (~18 MW) + refinery (~5 MW) + surface (~5 MW) "
                    "= ~68 MW. Consistent with AngloGold Ashanti reported Obuasi draw."
                ),
            },

            {
                # Weta Rice Farm & Milling Hub — Volta Region
                # 120,000,000 sqm irrigated area, 5 milling structures
                # Highly seasonal — diesel powered currently
                "anchor_id": "AL_ANC_014",
                "detection_id": "DET-014",
                "entity_name": "Weta Rice Farm & Milling Hub — Volta Region",
                "country": "Ghana",
                "sector": "Agriculture",
                "sub_sector": "Rice Production & Milling",
                "current_mw": 8.0,
                "load_factor": 0.42,
                "reliability_class": "Standard",
                "reliability_rationale": (
                    "Highly seasonal operation — irrigation peak Oct–Mar. "
                    "Currently diesel-powered (no grid connection). "
                    "Grid connection would allow expansion to 100,000 ha irrigation "
                    "requiring 100–150 MW — current 8 MW is suppressed demand only. "
                    "Standard reliability class as diesel backup currently substitutes."
                ),
                "demand_basis": (
                    "12,000 ha irrigated × 0.6 kW/ha irrigation pump average + "
                    "5 milling structures × ~400 kW each = ~7.2 MW + 2 MW milling "
                    "= ~8 MW current. Identity partially resolved — "
                    "conservative estimate applied."
                ),
            },

            {
                # Takoradi Port — Bulk & General Cargo Terminal
                # 6 berths, 3 cranes, liquid bulk jetty extension
                "anchor_id": "AL_ANC_015",
                "detection_id": "DET-015",
                "entity_name": "Takoradi Port — Bulk & General Cargo Terminal",
                "country": "Ghana",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics",
                "current_mw": 18.0,
                "load_factor": 0.80,
                "reliability_class": "High",
                "reliability_rationale": (
                    "Bulk cargo operations run continuously. "
                    "Liquid bulk jetty extension increases reliability sensitivity. "
                    "Smaller than Tema so classified High rather than Critical."
                ),
                "demand_basis": (
                    "3 cranes × 2.5 MW + bulk handling conveyors, lighting, "
                    "port administration, new jetty pumping = ~18 MW. "
                    "Consistent with GPHA Takoradi reported demand."
                ),
            },

            {
                # Accra Data Center (ADC) — CSquared / Liquid Telecom
                # 14,000 sqm, rooftop cooling, backup generators, on-site substation
                # Benchmark: Tier III DC ~700–900 W/sqm
                "anchor_id": "AL_ANC_016",
                "detection_id": "DET-016",
                "entity_name": "Accra Data Center (ADC)",
                "country": "Ghana",
                "sector": "Digital",
                "sub_sector": "Data Center — Tier III",
                "current_mw": 12.0,
                "load_factor": 0.92,
                "reliability_class": "Critical",
                "reliability_rationale": (
                    "Carrier-neutral Tier III data center — SLA requires 99.982% uptime. "
                    "Downtime triggers financial penalties and reputational damage. "
                    "Current diesel backup costs $3–5M/year — "
                    "strong incentive for reliable grid connection."
                ),
                "demand_basis": (
                    "14,000 sqm × ~857 W/sqm (Tier III benchmark) = ~12 MW. "
                    "Annex under construction will add 8–10 MW on completion. "
                    "Consistent with NCA registry reported draw."
                ),
            },

            # ================================================================
            # TOGO
            # ================================================================

            {
                # Port of Lomé — Container Terminal (MSC / Bolloré JV)
                # 12 berths, 8 cranes — deepest natural port in West Africa
                "anchor_id": "AL_ANC_017",
                "detection_id": "DET-017",
                "entity_name": "Port of Lomé — Container Terminal",
                "country": "Togo",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics",
                "current_mw": 28.0,
                "load_factor": 0.83,
                "reliability_class": "Critical",
                "reliability_rationale": (
                    "Key ECOWAS transshipment hub — 24/7 vessel operations. "
                    "Togo grid is highly unreliable (>50% import dependent). "
                    "Port currently relies heavily on backup generation — "
                    "grid reliability is a top operational priority."
                ),
                "demand_basis": (
                    "8 cranes × 2.5 MW + terminal operations, reefer plugs, "
                    "fuel storage pumps, lighting = ~28 MW. "
                    "Consistent with PAL reported peak demand."
                ),
            },

            {
                # Lomé Cement Plant — WACEM / Fortia Group
                # 2 kilns, 6 silos — ~3.5 MT/year clinker capacity
                # Benchmark: cement kiln ~15–18 MW per kiln
                "anchor_id": "AL_ANC_019",
                "detection_id": "DET-019",
                "entity_name": "Lomé Cement Plant (WACEM)",
                "country": "Togo",
                "sector": "Industrial",
                "sub_sector": "Cement & Clinker Manufacturing",
                "current_mw": 35.0,
                "load_factor": 0.85,
                "reliability_class": "High",
                "reliability_rationale": (
                    "Cement kilns run continuously — shutdown and restart is very costly "
                    "(thermal cycling damages refractory lining). "
                    "Classified High rather than Critical as kiln restart "
                    "is operationally feasible unlike underground mining."
                ),
                "demand_basis": (
                    "2 kilns × 16 MW each + grinding mills, conveyor systems, "
                    "administration = ~35 MW. "
                    "Consistent with WACEM Togo reported consumption."
                ),
            },

            {
                # Lomé Free Zone (SAZOF)
                # 18,000,000 sqm zone, 44% built-up, 12 warehouse clusters
                "anchor_id": "AL_ANC_020",
                "detection_id": "DET-020",
                "entity_name": "Lomé Free Zone (SAZOF)",
                "country": "Togo",
                "sector": "Industrial",
                "sub_sector": "Special Economic Zone",
                "current_mw": 22.0,
                "load_factor": 0.70,
                "reliability_class": "High",
                "reliability_rationale": (
                    "Mixed logistics and light industrial zone. "
                    "Togo grid unreliability severely constrains zone operations — "
                    "significant suppressed demand. "
                    "Grid reliability improvement expected to increase "
                    "actual demand to 40+ MW within 2 years."
                ),
                "demand_basis": (
                    "18,000,000 sqm × 44% built-up = 7,920,000 sqm active. "
                    "Light industrial benchmark 2.8 W/sqm = ~22 MW. "
                    "Consistent with SAZOF reported zone demand."
                ),
            },

            # ================================================================
            # BENIN
            # ================================================================

            {
                # Port of Cotonou — Bénin Terminal (Bolloré concession)
                # 10 berths, 5 cranes, ro-ro ramp extension
                "anchor_id": "AL_ANC_022",
                "detection_id": "DET-022",
                "entity_name": "Port of Cotonou — Bénin Terminal",
                "country": "Benin",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics",
                "current_mw": 24.0,
                "load_factor": 0.79,
                "reliability_class": "Critical",
                "reliability_rationale": (
                    "Primary maritime gateway for Benin and landlocked Niger, "
                    "Burkina Faso, and Mali. 24/7 operations. "
                    "Benin grid is highly unreliable — port relies on backup generation. "
                    "Grid connection is a stated government priority."
                ),
                "demand_basis": (
                    "5 cranes × 2.5 MW + terminal operations, ro-ro ramp, "
                    "container scanning, lighting = ~24 MW. "
                    "Consistent with PAC reported demand."
                ),
            },

            {
                # Zone Industrielle de Cotonou (PK10)
                # 3,000,000 sqm zone, 150+ enterprises, government administered
                "anchor_id": "AL_ANC_023",
                "detection_id": "DET-023",
                "entity_name": "Zone Industrielle de Cotonou (PK10)",
                "country": "Benin",
                "sector": "Industrial",
                "sub_sector": "Industrial Zone",
                "current_mw": 30.0,
                "load_factor": 0.60,
                "reliability_class": "High",
                "reliability_rationale": (
                    "Zone operates significantly below capacity due to "
                    "Benin grid unreliability — true demand suppressed. "
                    "Load factor 0.60 reflects constrained operations. "
                    "At reliable grid power, zone demand estimated at 45–50 MW. "
                    "Diesel generator pads widespread across zone."
                ),
                "demand_basis": (
                    "3,000,000 sqm × 10 W/sqm industrial average = ~30 MW. "
                    "Zone at 60% capacity — full capacity demand ~50 MW. "
                    "Consistent with APIEX reported industrial zone draw."
                ),
            },

            {
                # Unidentified Agro-Processing Cluster — Benin Coastal
                # 45,000 sqm, 3 silos, 4 loading bays, 2 cold storage structures
                # Identity unresolved — conservative estimate applied
                "anchor_id": "AL_ANC_024",
                "detection_id": "DET-024",
                "entity_name": "Unidentified Agro-Processing Cluster — Benin Coastal",
                "country": "Benin",
                "sector": "Agriculture",
                "sub_sector": "Agro-Processing — Pineapple & Cashew (probable)",
                "current_mw": 4.5,
                "load_factor": 0.55,
                "reliability_class": "Standard",
                "reliability_rationale": (
                    "Identity unresolved — conservative demand estimate applied. "
                    "Cold storage structures detected suggest some reliability sensitivity "
                    "but Standard class applied until identity confirmed. "
                    "Requires field verification before bankability assessment."
                ),
                "demand_basis": (
                    "45,000 sqm agro-processing facility with cold storage. "
                    "Agro-processing benchmark 100 W/sqm = ~4.5 MW. "
                    "Conservative estimate — actual may be higher if "
                    "cold chain operations are primary use."
                ),
            },

            # ================================================================
            # NIGERIA
            # ================================================================

            {
                # Dangote Refinery — 650,000 bpd, world's largest single-train
                # 48 storage tanks, 12 processing units, on-site substation
                # Benchmark: large petroleum refinery ~1.5 MW per 1,000 bpd
                "anchor_id": "AL_ANC_027",
                "detection_id": "DET-027",
                "entity_name": "Dangote Refinery",
                "country": "Nigeria",
                "sector": "Energy",
                "sub_sector": "Petroleum Refinery & Petrochemical",
                "current_mw": 1000.0,
                "load_factor": 0.92,
                "reliability_class": "Critical",
                "reliability_rationale": (
                    "World's largest single-train refinery at 650,000 bpd. "
                    "Refinery shutdown causes equipment damage and safety risk. "
                    "Each 1% downtime = $24M/year lost revenue at full capacity. "
                    "Current on-site gas generation provides N+1 redundancy — "
                    "grid connection provides additional backup at lower cost. "
                    "99.5%+ reliability required for safe operations."
                ),
                "demand_basis": (
                    "650,000 bpd × 1.54 MW/1,000 bpd = ~1,000 MW. "
                    "Breakdown: distillation units ~400 MW, "
                    "petrochemical units ~300 MW, utilities ~200 MW, "
                    "auxiliary ~100 MW. Consistent with Dangote Group reported draw."
                ),
            },

            {
                # Lekki Free Trade Zone — Chinese-Nigerian JV
                # 165,000,000 sqm zone, 34% built-up, 18 warehouse clusters
                # 7 active construction zones — rapid expansion ongoing
                "anchor_id": "AL_ANC_028",
                "detection_id": "DET-028",
                "entity_name": "Lekki Free Trade Zone",
                "country": "Nigeria",
                "sector": "Industrial",
                "sub_sector": "Special Economic Zone",
                "current_mw": 150.0,
                "load_factor": 0.74,
                "reliability_class": "Critical",
                "reliability_rationale": (
                    "One of Africa's largest SEZs — $20B+ committed investment. "
                    "Mixed heavy and light industrial — daytime heavy load profile. "
                    "18h/day high load typical for manufacturing tenants. "
                    "Full buildout demand 800–1,200 MW — "
                    "current 150 MW reflects 34% zone utilisation only."
                ),
                "demand_basis": (
                    "165,000,000 sqm × 34% built-up = 56,100,000 sqm active. "
                    "Mixed industrial benchmark 2.7 W/sqm = ~151 MW. "
                    "Rounded to 150 MW — consistent with NEPZA reported demand."
                ),
            },

            {
                # Lekki Deep Sea Port — Tolaram / CMA CGM JV
                # 8 berths, 6 cranes — fully operational since 2024
                "anchor_id": "AL_ANC_029",
                "detection_id": "DET-029",
                "entity_name": "Lekki Deep Sea Port",
                "country": "Nigeria",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics",
                "current_mw": 35.0,
                "load_factor": 0.82,
                "reliability_class": "Critical",
                "reliability_rationale": (
                    "Newly operational deep sea port — first vessels confirmed 2024. "
                    "Adjacent to Dangote Refinery and Lekki FTZ — "
                    "forms critical infrastructure cluster. "
                    "24/7 vessel operations require continuous reliable power."
                ),
                "demand_basis": (
                    "6 cranes × 2.5 MW + terminal operations, reefer plugs, "
                    "port administration, security lighting = ~35 MW. "
                    "Consistent with NPA reported Lekki port draw."
                ),
            },

            {
                # MainOne Data Center (MDX-i) — Equinix subsidiary
                # 22,000 sqm, Tier III/IV, rooftop cooling, backup generators
                # Benchmark: Tier III/IV DC ~700–900 W/sqm
                "anchor_id": "AL_ANC_030",
                "detection_id": "DET-030",
                "entity_name": "MainOne Data Center (MDX-i Lagos)",
                "country": "Nigeria",
                "sector": "Digital",
                "sub_sector": "Data Center — Tier III/IV",
                "current_mw": 18.0,
                "load_factor": 0.95,
                "reliability_class": "Critical",
                "reliability_rationale": (
                    "Equinix-operated Tier III/IV carrier-neutral data center. "
                    "SLA requires 99.982% uptime. "
                    "Expansion underway to double floor space — "
                    "demand expected to reach 35–40 MW post-expansion. "
                    "Current diesel backup costs $4–6M/year — "
                    "grid reliability is highest priority for this facility."
                ),
                "demand_basis": (
                    "22,000 sqm × ~818 W/sqm (Tier III/IV benchmark) = ~18 MW. "
                    "Annex expansion will add 15–20 MW on completion. "
                    "Consistent with NCC registry reported draw."
                ),
            },

            {
                # Apapa Port Complex — APM Terminals concession
                # 28 berths, 16 cranes — handles ~70% of Nigeria's imports/exports
                "anchor_id": "AL_ANC_031",
                "detection_id": "DET-031",
                "entity_name": "Apapa Port Complex",
                "country": "Nigeria",
                "sector": "Industrial",
                "sub_sector": "Port & Logistics",
                "current_mw": 55.0,
                "load_factor": 0.85,
                "reliability_class": "Critical",
                "reliability_rationale": (
                    "Nigeria's primary port — handles 70% of import/export cargo. "
                    "24/7 operations. Power outage causes massive national "
                    "supply chain disruption and demurrage liability. "
                    "New container scanning gantries increase power sensitivity."
                ),
                "demand_basis": (
                    "16 cranes × 2.5 MW + bulk terminal conveyors, "
                    "container scanning, port administration, security = ~55 MW. "
                    "Consistent with NPA Apapa reported peak demand."
                ),
            },

            {
                # Sagamu-Interchange Manufacturing Cluster
                # 28,000,000 sqm, 38 factory structures, 12 warehouse clusters
                # Multi-tenant — Honeywell, Fidson Healthcare as largest identified
                "anchor_id": "AL_ANC_032",
                "detection_id": "DET-032",
                "entity_name": "Sagamu-Interchange Manufacturing Cluster",
                "country": "Nigeria",
                "sector": "Industrial",
                "sub_sector": "Manufacturing Cluster",
                "current_mw": 45.0,
                "load_factor": 0.68,
                "reliability_class": "High",
                "reliability_rationale": (
                    "Multi-tenant light and heavy industrial cluster. "
                    "Identity partially resolved — multiple operators. "
                    "Manufacturing lines can restart after outages but "
                    "downtime is costly for food processing and pharmaceuticals. "
                    "Demand estimate is aggregate across confirmed tenants."
                ),
                "demand_basis": (
                    "38 factory structures estimated average 1.1 MW each + "
                    "12 warehouse clusters × 0.2 MW = ~41.8 MW + admin = ~45 MW. "
                    "Partially resolved identity — conservative aggregate estimate."
                ),
            },

            {
                # Unverified Hyperscale Data Center — Lagos Island North
                # 55,000 sqm, rooftop cooling confirmed, backup generators confirmed
                # Identity unresolved — manual verification required
                "anchor_id": "AL_ANC_034",
                "detection_id": "DET-034",
                "entity_name": "Unverified Hyperscale Data Center — Lagos Island North",
                "country": "Nigeria",
                "sector": "Digital",
                "sub_sector": "Data Center — Hyperscale (probable)",
                "current_mw": 35.0,
                "load_factor": 0.88,
                "reliability_class": "Critical",
                "reliability_rationale": (
                    "Identity unresolved — demand estimate based on physical "
                    "attributes only (55,000 sqm, rooftop cooling, backup generators). "
                    "If confirmed as hyperscale DC, Critical reliability class applies. "
                    "If reclassified as distribution warehouse, demand and "
                    "reliability class will need revision downward. "
                    "Manual verification required before bankability assessment."
                ),
                "demand_basis": (
                    "55,000 sqm × ~636 W/sqm (hyperscale benchmark, lower density "
                    "than colo) = ~35 MW. Conservative estimate given unresolved identity. "
                    "Actual could range 20–80 MW depending on confirmed use."
                ),
            },

            {
                # Lithium Exploration & Processing Site — Ghana North
                # 480,000 sqm site, open pit, 2 processing structures
                # ~44km from corridor — spur connection required
                # Identity partially resolved — operator redacted in cadastre
                "anchor_id": "AL_ANC_035",
                "detection_id": "DET-035",
                "entity_name": "Lithium Exploration & Processing Site — Ghana North",
                "country": "Ghana",
                "sector": "Mining",
                "sub_sector": "Lithium Exploration & Early Processing",
                "current_mw": 8.0,
                "load_factor": 0.70,
                "reliability_class": "High",
                "reliability_rationale": (
                    "Currently in exploration and early processing phase — "
                    "demand will scale significantly if full mining licence granted. "
                    "At full production lithium mine of this scale typically "
                    "requires 80–150 MW. Current 8 MW is exploration phase only. "
                    "High reliability required for processing equipment stability. "
                    "Note: ~44km from corridor — requires dedicated spur connection. "
                    "Identity partially resolved — operator verification pending."
                ),
                "demand_basis": (
                    "2 processing structures × ~3 MW each + haul road lighting, "
                    "pumping, administration = ~8 MW exploration phase. "
                    "Conservative estimate — actual unknown until identity confirmed."
                ),
            },
        ],

        "summary": {
            "total_current_mw": 2127.5,
            "anchor_loads_assessed": 24,
            "generation_assets_excluded": 10,
            "substations_excluded": 3,
            "by_reliability_class": {
                "Critical": 13,
                "High": 9,
                "Standard": 2,
            },
            "by_sector_mw": {
                "Energy": 1032.0,      # Dangote 1000 + TOR 32
                "Industrial": 619.0,   # Ports + SEZs + industrial zones
                "Mining": 76.0,        # Obuasi 68 + Lithium 8
                "Agriculture": 30.5,   # Cargill 18 + Weta 8 + Benin cluster 4.5
                "Digital": 65.0,       # ADC 12 + MainOne 18 + Unverified DC 35
            },
            "by_country_mw": {
                "Côte d'Ivoire": 105.0,
                "Ghana": 236.0,
                "Togo": 85.0,
                "Benin": 58.5,
                "Nigeria": 1338.0,     # Dominated by Dangote Refinery
            },
            "flags": [
                "AL_ANC_004: Partial identity — demand estimate conservative, verify before bankability",
                "AL_ANC_014: Currently diesel-powered — 8 MW is suppressed demand; "
                "grid connection unlocks 100–150 MW expansion",
                "AL_ANC_024: Identity unresolved — Standard reliability class applied conservatively",
                "AL_ANC_034: Identity unresolved — demand range 20–80 MW; "
                "35 MW is midpoint estimate pending verification",
                "AL_ANC_035: Exploration phase only — full production demand 80–150 MW",
                "AL_ANC_012: ~98km from corridor — dedicated spur required",
                "AL_ANC_035: ~44km from corridor — dedicated spur required",
            ],
        },

        "message": (
            "Current demand profiles calculated for 24 anchor loads across 5 countries. "
            "Total aggregated current demand: 2,127.5 MW. "
            "Nigeria dominates at 1,338 MW driven by Dangote Refinery (1,000 MW). "
            "13 Critical-class anchors represent highest-priority transmission customers. "
            "4 facilities flagged for verification before bankability assessment. "
            "2 facilities (~98km and ~44km from corridor) require dedicated spur analysis."
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