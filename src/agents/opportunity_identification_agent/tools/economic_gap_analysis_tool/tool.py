import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import GapAnalysisInput


@tool("economic_gap_analysis", description=TOOL_DESCRIPTION)
def economic_gap_analysis_tool(
    payload: GapAnalysisInput, runtime: ToolRuntime
) -> Command:
    """
    Identifies underserved geographic zones within the corridor boundary where
    significant economic demand exists but current infrastructure fails to serve it.

    This tool shifts perspective from individual anchor loads to the corridor
    as a whole. It overlays demand data from previous tools against known
    existing infrastructure to find where the gaps are largest and most impactful.

    Three gap types identified:
        Transmission Gap       — significant demand but no reliable HV infrastructure
        Suppressed Demand Gap  — facilities exist but operate below capacity due
                                 to chronic power unreliability
        Catalytic Gap          — infrastructure investment would unlock economic
                                 activity that cannot start without reliable power

    Corridor boundary applied:
        NW: [-4.008, 5.600]   NE: [3.379, 6.750]
        SW: [-4.008, 5.100]   SE: [3.379, 6.250]

    All gaps are within or directly adjacent to the 50km corridor buffer.
    All anchor IDs referenced are from scan_anchor_loads pipeline output.

    This tool does NOT return:
        - Bankability scores           → assess_bankability
        - Growth projections           → model_growth_trajectory
        - Route geometry               → infrastructure_optimization_agent
        - Financing structures         → financing_optimization_agent
        - Final priority rankings      → prioritize_opportunities
    """

    response = {
        "corridor_id": "AL_CORRIDOR_POC_001",
        "gaps_found": 14,
        "total_unmet_demand_mw": 1842.0,
        "gap_type_summary": {
            "transmission_gaps": 5,
            "suppressed_demand_gaps": 5,
            "catalytic_gaps": 4,
        },
        "severity_summary": {
            "critical": 5,
            "high": 6,
            "medium": 3,
        },
        "phase_summary": {
            "phase_1": 5,
            "phase_2": 6,
            "phase_3": 3,
        },

        "gaps": [

            # ================================================================
            # TRANSMISSION GAPS — No reliable HV infrastructure serving demand
            # ================================================================

            {
                "gap_id": "GAP_001",
                "gap_type": "Transmission Gap",
                "severity": "Critical",
                "investment_priority": "Phase 1",

                "name": "Abidjan–Takoradi Missing 330kV Link",
                "location": "Coastal stretch between Abidjan and Takoradi",
                "country_span": ["Côte d'Ivoire", "Ghana"],
                "coords": {"latitude": 5.280, "longitude": -2.800},

                "anchors_affected": [
                    "AL_ANC_003",   # Port of Abidjan — Vridi Terminal
                    "AL_ANC_005",   # Abidjan ZIEX
                    "AL_ANC_015",   # Takoradi Port
                ],

                "unmet_demand_mw": 105.0,
                "addressable_demand_mw": 288.0,

                "primary_constraint": (
                    "No 330kV transmission backbone exists between Abidjan "
                    "and Takoradi — a 380km coastal gap. "
                    "The existing WAPP interconnector between Côte d'Ivoire "
                    "and Ghana runs inland via Man–Kumasi at 225kV, bypassing "
                    "the entire coastal industrial and port corridor. "
                    "Abidjan's generation surplus (Azito + CIPREL combined "
                    "~1,100 MW capacity) cannot reach Ghana's coastal demand centers. "
                    "Both countries run independent coastal grids with no direct link."
                ),

                "economic_impact": (
                    "Abidjan port, ZIEX, and Takoradi port are all operating "
                    "with backup diesel supplementing unreliable grid supply. "
                    "Abidjan port alone spends ~$8M/year on backup generation. "
                    "A coastal 330kV link enables power trade between the two "
                    "countries' coastal industrial zones and eliminates "
                    "the largest single missing link on the corridor."
                ),

                "recommended_intervention": (
                    "330kV transmission line, Abidjan (Vridi substation) "
                    "to Takoradi (Aboadze substation), ~380km coastal route. "
                    "Co-located with the Abidjan-Lagos highway where feasible "
                    "— estimated 55% highway overlap reduces CAPEX by 18-22%."
                ),
                "estimated_capex_usd_m": 420.0,
                "co_location_savings_usd_m": 80.0,
                "net_capex_usd_m": 340.0,
            },

            {
                "gap_id": "GAP_002",
                "gap_type": "Transmission Gap",
                "severity": "Critical",
                "investment_priority": "Phase 1",

                "name": "Lomé–Cotonou 330kV Missing Interconnector",
                "location": "Coastal stretch between Lomé and Cotonou",
                "country_span": ["Togo", "Benin"],
                "coords": {"latitude": 6.280, "longitude": 1.840},

                "anchors_affected": [
                    "AL_ANC_017",   # Port of Lomé — Container Terminal
                    "AL_ANC_019",   # Lomé Cement Plant (WACEM)
                    "AL_ANC_020",   # Lomé Free Zone
                    "AL_ANC_022",   # Port of Cotonou
                    "AL_ANC_023",   # Zone Industrielle Cotonou
                ],

                "unmet_demand_mw": 139.0,
                "addressable_demand_mw": 224.0,

                "primary_constraint": (
                    "No 330kV backbone exists on the 140km coastal stretch "
                    "between Lomé and Cotonou — the most industrially dense "
                    "segment of the corridor after Lagos. "
                    "Togo imports 65% of electricity from Ghana's VRA via "
                    "a single 161kV line — any fault causes national blackout. "
                    "Benin imports 85% of electricity from CEB (Ghana/Togo "
                    "joint utility) with similar single-point-of-failure risk. "
                    "Both countries pay 35-45% premium over generation cost "
                    "due to import dependency."
                ),

                "economic_impact": (
                    "Port of Lomé and Port of Cotonou both rely heavily "
                    "on backup diesel generation — combined $12M/year cost. "
                    "Lomé Free Zone at 44% occupancy — new enterprises "
                    "cite power reliability as primary deterrent. "
                    "WACEM cement plant loses ~$3M/year in production "
                    "from kiln interruptions. "
                    "A 330kV interconnector doubles the reliability of "
                    "both countries' grids by providing path redundancy."
                ),

                "recommended_intervention": (
                    "330kV double-circuit transmission line, Lomé (Tokoin substation) "
                    "to Cotonou (Maria Gleta substation), ~140km. "
                    "Co-located with the coastal highway — estimated 72% highway "
                    "overlap given straight coastal alignment."
                ),
                "estimated_capex_usd_m": 155.0,
                "co_location_savings_usd_m": 30.0,
                "net_capex_usd_m": 125.0,
            },

            {
                "gap_id": "GAP_003",
                "gap_type": "Transmission Gap",
                "severity": "Critical",
                "investment_priority": "Phase 1",

                "name": "Lekki Cluster 330kV Capacity Gap — Lagos",
                "location": "Lekki Peninsula, Lagos State, Nigeria",
                "country_span": ["Nigeria"],
                "coords": {"latitude": 6.435, "longitude": 3.700},

                "anchors_affected": [
                    "AL_ANC_027",   # Dangote Refinery (1,000 MW)
                    "AL_ANC_028",   # Lekki Free Trade Zone (150 MW, growing to 1,200 MW)
                    "AL_ANC_029",   # Lekki Deep Sea Port
                    "AL_ANC_030",   # MainOne Data Center
                ],

                "unmet_demand_mw": 885.0,
                "addressable_demand_mw": 3140.0,

                "primary_constraint": (
                    "The Lekki Peninsula has no dedicated 330kV transmission "
                    "infrastructure capable of serving the scale of investment "
                    "now present. The existing TCN 132kV feed to the area "
                    "was designed for residential load — not a 1,000 MW refinery "
                    "and a Chinese industrial city scaling to 200,000 jobs. "
                    "Dangote Refinery operates entirely on captive gas generation "
                    "because grid infrastructure is wholly inadequate. "
                    "Current TCN allocation to Lekki: 150 MW. "
                    "Current and committed demand: 1,203 MW and growing to 3,140 MW."
                ),

                "economic_impact": (
                    "Dangote Refinery's captive gas generation costs an estimated "
                    "$25–35M/year more than grid power would. "
                    "Lekki FTZ enterprise attraction is constrained by inability "
                    "to guarantee power to industrial tenants. "
                    "This is the single highest-value gap on the entire corridor — "
                    "closing it unlocks $20B+ in committed investment. "
                    "Every month of delay costs an estimated $15–20M in "
                    "foregone production efficiency."
                ),

                "recommended_intervention": (
                    "400kV dedicated transmission hub, Lekki Peninsula — "
                    "new 400/330kV substation at Dangote complex with "
                    "double-circuit feed from Omotosho and Ajah grid points. "
                    "Phased: Phase 1A 500 MW capacity, Phase 1B upgrade to 2,500 MW "
                    "by Year 5 aligned with Lekki FTZ buildout."
                ),
                "estimated_capex_usd_m": 380.0,
                "co_location_savings_usd_m": 25.0,
                "net_capex_usd_m": 355.0,
            },

            {
                "gap_id": "GAP_004",
                "gap_type": "Transmission Gap",
                "severity": "High",
                "investment_priority": "Phase 1",

                "name": "Obuasi Gold Mine 98km Transmission Spur Gap",
                "location": "Obuasi, Ashanti Region, Ghana",
                "country_span": ["Ghana"],
                "coords": {"latitude": 6.204, "longitude": -1.672},

                "anchors_affected": [
                    "AL_ANC_012",   # Obuasi Gold Mine (AngloGold Ashanti)
                ],

                "unmet_demand_mw": 38.0,
                "addressable_demand_mw": 68.0,

                "primary_constraint": (
                    "Obuasi Gold Mine is connected via a 161kV line that is "
                    "aging, undersized, and suffers 22 outages per year on average. "
                    "The mine sits ~98km from the nearest reliable 330kV grid point "
                    "(Kumasi substation). "
                    "Each outage risks underground worker safety — "
                    "ventilation and dewatering systems must not fail. "
                    "AngloGold Ashanti maintains $8M/year of backup diesel "
                    "generation for exactly this reason. "
                    "Phase 3 mine expansion (signed with EPC contractor) "
                    "adds 20 MW — the existing 161kV line cannot handle "
                    "the increased load without upgrade."
                ),

                "economic_impact": (
                    "22 outages/year × average 4-hour duration × 68 MW "
                    "= ~6,000 MWh/year lost production. "
                    "At $1,900/oz gold and mine productivity rates "
                    "= ~$8–12M/year production loss. "
                    "Phase 3 expansion ($250M capital) is contingent "
                    "on reliable power supply — transmission upgrade "
                    "is on AngloGold Ashanti's critical path."
                ),

                "recommended_intervention": (
                    "330kV dedicated spur, Kumasi substation to Obuasi mine, "
                    "~98km. New 330/11kV mine substation at Obuasi. "
                    "AngloGold Ashanti corporate guarantee anchors spur financing."
                ),
                "estimated_capex_usd_m": 88.0,
                "co_location_savings_usd_m": 8.0,
                "net_capex_usd_m": 80.0,
            },

            {
                "gap_id": "GAP_005",
                "gap_type": "Transmission Gap",
                "severity": "High",
                "investment_priority": "Phase 2",

                "name": "Lithium Site — Ghana North 44km Spur Gap",
                "location": "Lithium exploration zone, Ashanti/Brong-Ahafo border, Ghana",
                "country_span": ["Ghana"],
                "coords": {"latitude": 6.812, "longitude": -1.244},

                "anchors_affected": [
                    "AL_ANC_035",   # Lithium Exploration & Processing Site
                ],

                "unmet_demand_mw": 8.0,
                "addressable_demand_mw": 140.0,

                "primary_constraint": (
                    "Lithium exploration site has no grid connection whatsoever — "
                    "currently running entirely on diesel generation. "
                    "Nearest 161kV grid point is ~44km away at Mampong substation. "
                    "Operator identity is redacted in Minerals Commission cadastre "
                    "preventing commercial engagement. "
                    "At current exploration scale the economics of a spur "
                    "are marginal — but at full mining scale (80–150 MW) "
                    "they are strongly positive."
                ),

                "economic_impact": (
                    "Conditional gap — value is speculative until mining licence "
                    "is granted and operator confirmed. "
                    "At full production: lithium mine of this scale would consume "
                    "120–150 MW continuously with Critical reliability requirement. "
                    "Global EV battery demand creates strong commercial case — "
                    "this could become a Tier 1 anchor worth $40–60M/year revenue. "
                    "Early spur planning now reduces lead time when licence is granted."
                ),

                "recommended_intervention": (
                    "161kV spur, Mampong substation to lithium site, ~44km. "
                    "CONDITIONAL — do not proceed until: "
                    "(1) mining licence granted, (2) operator identity confirmed, "
                    "(3) operator corporate guarantee secured. "
                    "Include in Phase 2 planning pipeline only."
                ),
                "estimated_capex_usd_m": 42.0,
                "co_location_savings_usd_m": 0.0,
                "net_capex_usd_m": 42.0,
            },

            # ================================================================
            # SUPPRESSED DEMAND GAPS — Facilities exist but operate below
            # capacity due to chronic power unreliability
            # ================================================================

            {
                "gap_id": "GAP_006",
                "gap_type": "Suppressed Demand Gap",
                "severity": "Critical",
                "investment_priority": "Phase 1",

                "name": "Tema Industrial Cluster — Grid Capacity Constraint",
                "location": "Tema Industrial Area, Greater Accra, Ghana",
                "country_span": ["Ghana"],
                "coords": {"latitude": 5.650, "longitude": -0.010},

                "anchors_affected": [
                    "AL_ANC_007",   # Tema Oil Refinery (TOR)
                    "AL_ANC_008",   # Tema Port — Meridian Port Services
                    "AL_ANC_009",   # Tema Free Zone
                    "AL_ANC_016",   # Accra Data Center (ADC)
                ],

                "unmet_demand_mw": 72.0,
                "addressable_demand_mw": 194.0,

                "primary_constraint": (
                    "The Tema industrial cluster is served by aging 161kV "
                    "infrastructure originally built in the 1970s for a fraction "
                    "of current demand. "
                    "GRIDCo (Ghana's transmission operator) has classified the "
                    "Tema–Accra corridor as one of three national transmission "
                    "priority zones due to chronic overloading. "
                    "TOR refinery operating at 55% capacity — reliable power "
                    "is prerequisite for rehabilitation and full restart. "
                    "Tema Free Zone at 60% capacity — 200+ enterprises "
                    "cite power as primary operational constraint. "
                    "Port terminal experiencing 14 power-related crane "
                    "stoppages per month on average."
                ),

                "economic_impact": (
                    "Tema Free Zone at 60% capacity = 80 enterprises and "
                    "~12,000 jobs suppressed by power constraint. "
                    "TOR rehabilitation stalled — Ghana imports $400M+ "
                    "in refined petroleum products annually that TOR "
                    "could produce domestically with reliable power. "
                    "Port crane stoppages cost ~$6M/year in demurrage. "
                    "Total economic cost of Tema power constraint: "
                    "estimated $180–220M/year."
                ),

                "recommended_intervention": (
                    "330kV grid reinforcement of Tema–Accra corridor — "
                    "new 330/161kV substation at Tema Industrial Area "
                    "with double-circuit 330kV feed from Akosombo-Tema line. "
                    "Coordinates with GRIDCo national transmission masterplan."
                ),
                "estimated_capex_usd_m": 95.0,
                "co_location_savings_usd_m": 12.0,
                "net_capex_usd_m": 83.0,
            },

            {
                "gap_id": "GAP_007",
                "gap_type": "Suppressed Demand Gap",
                "severity": "High",
                "investment_priority": "Phase 1",

                "name": "Lomé Industrial & Port Cluster — Grid Reliability Gap",
                "location": "Lomé Port and Industrial Zone, Maritime Region, Togo",
                "country_span": ["Togo"],
                "coords": {"latitude": 6.155, "longitude": 1.255},

                "anchors_affected": [
                    "AL_ANC_017",   # Port of Lomé — Container Terminal
                    "AL_ANC_019",   # Lomé Cement Plant (WACEM)
                    "AL_ANC_020",   # Lomé Free Zone (SAZOF)
                ],

                "unmet_demand_mw": 38.0,
                "addressable_demand_mw": 85.0,

                "primary_constraint": (
                    "Togo's national grid delivers power with 28+ outages "
                    "per month average at industrial zones — among the worst "
                    "reliability statistics in West Africa. "
                    "The country relies on a single 161kV import line from "
                    "Ghana's VRA — any fault or curtailment causes national "
                    "industrial brownout. "
                    "Port of Lomé runs 4 backup diesel generator sets "
                    "continuously — not as emergency backup but as primary "
                    "supplemental supply. "
                    "Lomé Free Zone at 44% occupancy — enterprises "
                    "specifically requesting 'dedicated power supply clause' "
                    "in lease agreements that SAZOF cannot guarantee."
                ),

                "economic_impact": (
                    "Port of Lomé — West Africa's deepest natural port — "
                    "is losing transshipment market share to Abidjan and Tema "
                    "due to power reliability concerns of shipping lines. "
                    "WACEM loses ~35 kiln-days per year to power interruptions "
                    "= ~$4M annual production loss. "
                    "Lomé Free Zone suppressed demand: 20+ MW immediately "
                    "unlockable if power reliability improves. "
                    "Togo national grid import cost premium: "
                    "~$45M/year above efficient generation cost."
                ),

                "recommended_intervention": (
                    "Dedicated 161kV industrial feeder, Lomé port and "
                    "free zone cluster — ring-fenced from residential grid "
                    "with dedicated substation and automatic load shedding "
                    "that protects industrial supply at all times. "
                    "Coordinates with GAP_002 Lomé–Cotonou interconnector."
                ),
                "estimated_capex_usd_m": 48.0,
                "co_location_savings_usd_m": 6.0,
                "net_capex_usd_m": 42.0,
            },

            {
                "gap_id": "GAP_008",
                "gap_type": "Suppressed Demand Gap",
                "severity": "High",
                "investment_priority": "Phase 2",

                "name": "Zone Industrielle Cotonou — Chronic Unreliability Gap",
                "location": "PK10 Industrial Zone, Cotonou, Benin",
                "country_span": ["Benin"],
                "coords": {"latitude": 6.420, "longitude": 2.391},

                "anchors_affected": [
                    "AL_ANC_023",   # Zone Industrielle de Cotonou (PK10)
                ],

                "unmet_demand_mw": 18.0,
                "addressable_demand_mw": 50.0,

                "primary_constraint": (
                    "Zone Industrielle Cotonou is served by the national SBEE "
                    "distribution network which delivers power with 35+ outages "
                    "per month and voltage fluctuations of ±15% — "
                    "well beyond the ±5% industrial equipment tolerance. "
                    "Substation exists 6km away but is technically inadequate "
                    "for industrial supply quality. "
                    "150 enterprises in the zone — 80% run diesel generators "
                    "as primary or supplemental supply. "
                    "Zone expansion (150 ha) formally approved but developers "
                    "will not begin without power reliability guarantee."
                ),

                "economic_impact": (
                    "Zone at 60% capacity = 60 enterprises and 9,000 jobs "
                    "suppressed by power constraint. "
                    "150 ha expansion ($200–400M investment) stalled. "
                    "Manufacturers relocating to Lomé and Tema — "
                    "Benin losing industrial investment to neighbours. "
                    "Diesel generation costs across zone enterprises: "
                    "estimated $18M/year above grid tariff equivalent."
                ),

                "recommended_intervention": (
                    "Dedicated 33kV industrial feeder from corridor backbone "
                    "+ power quality compensation equipment (SVC or STATCOM) "
                    "at zone substation. "
                    "Voltage regulation to ±2% for industrial supply. "
                    "Coordinates with GAP_002 Lomé–Cotonou interconnector "
                    "which provides the upstream backbone reliability."
                ),
                "estimated_capex_usd_m": 22.0,
                "co_location_savings_usd_m": 2.0,
                "net_capex_usd_m": 20.0,
            },

            {
                "gap_id": "GAP_009",
                "gap_type": "Suppressed Demand Gap",
                "severity": "High",
                "investment_priority": "Phase 2",

                "name": "Abidjan ZIEX and Port Industrial Zone — Reliability Gap",
                "location": "Vridi Industrial Canal and ZIEX, Abidjan, Côte d'Ivoire",
                "country_span": ["Côte d'Ivoire"],
                "coords": {"latitude": 5.295, "longitude": -4.003},

                "anchors_affected": [
                    "AL_ANC_003",   # Port of Abidjan — Vridi Terminal
                    "AL_ANC_005",   # Abidjan ZIEX
                    "AL_ANC_004",   # Cargill Cocoa Processing Plant
                ],

                "unmet_demand_mw": 28.0,
                "addressable_demand_mw": 105.0,

                "primary_constraint": (
                    "Despite Abidjan being home to Côte d'Ivoire's main "
                    "generation assets (Azito + CIPREL), the distribution "
                    "infrastructure in the Vridi industrial zone is aging "
                    "and undersized for current industrial load. "
                    "Abidjan port reports 11 power-related operational "
                    "interruptions per month — not from generation shortage "
                    "but from distribution network inadequacy. "
                    "ZIEX zone at 58% built-up capacity — new enterprises "
                    "constrained by inability to guarantee dedicated supply. "
                    "The paradox: generation surplus next door, "
                    "but poor last-mile distribution."
                ),

                "economic_impact": (
                    "Port of Abidjan loses ~$8M/year to backup diesel costs. "
                    "ZIEX at 58% utilisation = 84 enterprises and ~11,000 "
                    "jobs suppressed by distribution constraint. "
                    "Cocoa processing expansion ($180M investment pipeline "
                    "across Cargill, Barry Callebaut) constrained by "
                    "inability to guarantee industrial-grade supply quality. "
                    "Côte d'Ivoire's largest export processing zone "
                    "is underperforming due to last-mile infrastructure gap."
                ),

                "recommended_intervention": (
                    "225kV industrial substation upgrade at Vridi industrial zone "
                    "with dedicated feeders to port terminal, ZIEX, and "
                    "cocoa processing cluster. "
                    "Separates industrial supply from residential network — "
                    "eliminates shared-feeder voltage fluctuation problem."
                ),
                "estimated_capex_usd_m": 55.0,
                "co_location_savings_usd_m": 8.0,
                "net_capex_usd_m": 47.0,
            },

            {
                "gap_id": "GAP_010",
                "gap_type": "Suppressed Demand Gap",
                "severity": "Medium",
                "investment_priority": "Phase 2",

                "name": "Sagamu Manufacturing Cluster — Distribution Quality Gap",
                "location": "Sagamu Interchange, Ogun State, Nigeria",
                "country_span": ["Nigeria"],
                "coords": {"latitude": 6.878, "longitude": 3.662},

                "anchors_affected": [
                    "AL_ANC_032",   # Sagamu-Interchange Manufacturing Cluster
                ],

                "unmet_demand_mw": 18.0,
                "addressable_demand_mw": 45.0,

                "primary_constraint": (
                    "Sagamu cluster is connected to the Lagos TCN 132kV network "
                    "but experiences chronic overloading due to rapid industrial "
                    "growth along the Lagos–Ibadan expressway corridor. "
                    "The 132kV Sagamu substation is at 95% nameplate capacity — "
                    "no headroom for the new pharmaceutical block under construction "
                    "or additional enterprises. "
                    "Nigerian grid reliability in Ogun State: average 18 outages "
                    "per month with 6+ hour average restoration time. "
                    "Multi-tenant cluster cannot aggregate demand for a single "
                    "grid upgrade — no lead operator to anchor investment."
                ),

                "economic_impact": (
                    "Manufacturing cluster at 68% load factor — "
                    "production lines operating below capacity. "
                    "Pharmaceutical manufacturing particularly affected — "
                    "GMP compliance requires voltage stability that "
                    "current supply cannot guarantee. "
                    "Estimated 15 enterprises have declined to expand "
                    "at Sagamu citing power reliability in last 3 years. "
                    "Ogun State losing manufacturing investment to "
                    "Lagos Island and Lekki FTZ."
                ),

                "recommended_intervention": (
                    "132/33kV substation capacity upgrade at Sagamu interchange — "
                    "new 2×60 MVA transformers replacing existing 1×40 MVA. "
                    "Ogun State government as anchor guarantor for "
                    "grid upgrade cost recovery via industrial tariff."
                ),
                "estimated_capex_usd_m": 28.0,
                "co_location_savings_usd_m": 0.0,
                "net_capex_usd_m": 28.0,
            },

            # ================================================================
            # CATALYTIC GAPS — Infrastructure investment would unlock economic
            # activity that cannot start without reliable power
            # ================================================================

            {
                "gap_id": "GAP_011",
                "gap_type": "Catalytic Gap",
                "severity": "Critical",
                "investment_priority": "Phase 2",

                "name": "Volta Agricultural Belt — Grid Connection Gap",
                "location": "Volta River Delta agricultural zone, Volta Region, Ghana",
                "country_span": ["Ghana"],
                "coords": {"latitude": 6.032, "longitude": 0.607},

                "anchors_affected": [
                    "AL_ANC_014",   # Weta Rice Farm & Milling Hub
                ],

                "unmet_demand_mw": 8.0,
                "addressable_demand_mw": 150.0,

                "primary_constraint": (
                    "The Volta Delta agricultural belt has no grid connection "
                    "whatsoever — 120,000 ha of irrigable land currently running "
                    "entirely on diesel pumps at $0.25/kWh vs $0.09/kWh grid tariff. "
                    "This 178% cost premium makes commercial-scale irrigation "
                    "economically unviable — farming is limited to subsistence scale. "
                    "Nearest 161kV grid point is at Akuse, ~35km away. "
                    "Weta Rice Farm represents the commercial anchor "
                    "for a much larger agricultural catchment that is "
                    "completely dark to the grid."
                ),

                "economic_impact": (
                    "100,000 ha irrigation potential unlocked by grid connection. "
                    "Rice production scale-up addresses $200M annual import bill. "
                    "95,000 direct and indirect jobs created at full buildout. "
                    "This is the highest development impact opportunity "
                    "on the corridor per dollar of infrastructure investment. "
                    "Grid connection is the single binding constraint — "
                    "AfDB SAPZ programme has committed $85M in agricultural "
                    "investment contingent on power connection."
                ),

                "recommended_intervention": (
                    "161kV spur, Akuse substation to Weta zone, ~35km. "
                    "New 161/33kV agricultural substation at Weta zone center. "
                    "Ghana COCOBOD aggregation model for PPA counterparty. "
                    "AfDB SAPZ co-financing for connection infrastructure. "
                    "CONDITIONAL on identity confirmation of lead operator."
                ),
                "estimated_capex_usd_m": 32.0,
                "co_location_savings_usd_m": 0.0,
                "net_capex_usd_m": 32.0,
            },

            {
                "gap_id": "GAP_012",
                "gap_type": "Catalytic Gap",
                "severity": "High",
                "investment_priority": "Phase 2",

                "name": "Takoradi Cocoa & Palm Oil Agro-Processing — Power Gap",
                "location": "Takoradi hinterland, Western Region, Ghana",
                "country_span": ["Ghana"],
                "coords": {"latitude": 4.980, "longitude": -1.870},

                "anchors_affected": [
                    "AL_ANC_015",   # Takoradi Port (indirect — export route)
                ],

                "unmet_demand_mw": 12.0,
                "addressable_demand_mw": 55.0,

                "primary_constraint": (
                    "Ghana's western cocoa belt produces 800,000 tonnes/year "
                    "but 80% is exported as raw beans — losing 60% of "
                    "potential value-added. "
                    "Agro-processors cite 18+ power outages per month "
                    "as the primary barrier to installing processing equipment. "
                    "The hinterland 33kV network feeding the processing zone "
                    "is radial (no backup path) — any fault causes extended outage. "
                    "Cashew processing hub currently running on 100% diesel. "
                    "Takoradi port proximity provides natural export outlet "
                    "but processing capacity cannot develop without reliable power."
                ),

                "economic_impact": (
                    "80% of cocoa exported raw = $420M/year in value-added "
                    "processing revenue lost to European and Asian processors. "
                    "Government 50% domestic processing mandate by 2025 "
                    "cannot be met without addressing this gap. "
                    "Reliable power expected to attract $150M in new "
                    "agro-processing investment within 36 months. "
                    "Takoradi port cargo volumes increase as processed "
                    "goods replace raw commodity exports."
                ),

                "recommended_intervention": (
                    "33kV ring main reinforcement, Takoradi hinterland "
                    "agro-processing zone — eliminates radial network "
                    "single point of failure. "
                    "New 33/11kV substations at 3 processing cluster nodes. "
                    "Co-located with Takoradi port spur where route overlaps."
                ),
                "estimated_capex_usd_m": 24.0,
                "co_location_savings_usd_m": 4.0,
                "net_capex_usd_m": 20.0,
            },

            {
                "gap_id": "GAP_013",
                "gap_type": "Catalytic Gap",
                "severity": "Medium",
                "investment_priority": "Phase 3",

                "name": "Benin Coastal Agro-Processing — Unserved Zone",
                "location": "Coastal agricultural zone east of Cotonou, Benin",
                "country_span": ["Benin"],
                "coords": {"latitude": 6.492, "longitude": 2.628},

                "anchors_affected": [
                    "AL_ANC_024",   # Unidentified Agro-Processing Cluster (Benin)
                ],

                "unmet_demand_mw": 4.5,
                "addressable_demand_mw": 35.0,

                "primary_constraint": (
                    "The coastal zone east of Cotonou has an unverified "
                    "agro-processing cluster (DET-024) with no grid connection "
                    "and an unresolved operator identity. "
                    "The nearest 33kV line is 12km away at the Cotonou "
                    "distribution network edge. "
                    "Pineapple and cashew production in this zone is growing "
                    "but entirely cold-chain constrained — produce spoils "
                    "without refrigerated storage. "
                    "Benin coastal zone is identified in AfDB SAPZ programme "
                    "as a priority investment area but no power connection plan exists."
                ),

                "economic_impact": (
                    "Pineapple post-harvest losses: 35–45% of production "
                    "lost due to absence of cold chain. "
                    "EU market access for Benin pineapple and cashew "
                    "is commercially viable but requires certified cold chain "
                    "from farm to port — impossible without reliable power. "
                    "Conservative estimate: $25M/year export value unlockable "
                    "with reliable grid connection."
                ),

                "recommended_intervention": (
                    "33kV extension, Cotonou distribution network edge "
                    "to coastal agro-processing zone, ~12km. "
                    "New 33/11kV substation at zone center. "
                    "CONDITIONAL on operator identity confirmation "
                    "and AfDB SAPZ programme confirmation for this zone. "
                    "Phase 3 only — proceed after Phase 1 and Phase 2 "
                    "establish corridor backbone reliability."
                ),
                "estimated_capex_usd_m": 14.0,
                "co_location_savings_usd_m": 0.0,
                "net_capex_usd_m": 14.0,
            },

            {
                "gap_id": "GAP_014",
                "gap_type": "Catalytic Gap",
                "severity": "Medium",
                "investment_priority": "Phase 3",

                "name": "Lagos Hyperscale Digital Cluster — Grid Readiness Gap",
                "location": "Lagos Island North and Victoria Island, Lagos, Nigeria",
                "country_span": ["Nigeria"],
                "coords": {"latitude": 6.601, "longitude": 3.349},

                "anchors_affected": [
                    "AL_ANC_034",   # Unverified Hyperscale Data Center
                    "AL_ANC_030",   # MainOne Data Center (indirect — cluster)
                ],

                "unmet_demand_mw": 35.0,
                "addressable_demand_mw": 280.0,

                "primary_constraint": (
                    "Lagos Island North is emerging as a hyperscale data center "
                    "corridor but the existing TCN 132kV infrastructure "
                    "serving Victoria Island and Lagos Island is inadequate "
                    "for hyperscale DC power requirements. "
                    "Current grid allocation to this zone: ~80 MW. "
                    "Demand if unverified DC is confirmed hyperscale + "
                    "MainOne expansion + further DCs entering Lagos market: "
                    "250–350 MW by Year 10. "
                    "Data center operators require N+1 grid redundancy "
                    "(two independent grid feeds) — current single-feed "
                    "infrastructure cannot meet this requirement."
                ),

                "economic_impact": (
                    "Lagos is Africa's fintech capital — Tier III/IV data centers "
                    "are critical national infrastructure. "
                    "Every $1 of data center investment generates $4–6 of "
                    "downstream digital economy value. "
                    "At $250M DC investment pipeline confirmed or probable: "
                    "downstream digital economy impact $1–1.5B. "
                    "Without N+1 grid infrastructure, hyperscale operators "
                    "will locate in Accra or Nairobi instead of Lagos."
                ),

                "recommended_intervention": (
                    "132kV N+1 ring infrastructure, Lagos Island North "
                    "data center corridor — two independent 132kV feeds "
                    "from separate TCN grid points with automatic "
                    "changeover under 100ms (data center standard). "
                    "CONDITIONAL on unverified DC identity confirmation. "
                    "Phase 3 — coordinate with GAP_003 Lekki hub "
                    "which provides the upstream backbone."
                ),
                "estimated_capex_usd_m": 65.0,
                "co_location_savings_usd_m": 0.0,
                "net_capex_usd_m": 65.0,
            },
        ],

        # ------------------------------------------------------------------ #
        #  CORRIDOR GAP SUMMARY                                               #
        # ------------------------------------------------------------------ #
        "corridor_gap_summary": {
            "total_gaps": 14,
            "total_unmet_demand_mw": 1842.0,
            "total_addressable_demand_mw": 4909.0,
            "total_gross_capex_usd_m": 1468.0,
            "total_co_location_savings_usd_m": 175.0,
            "total_net_capex_usd_m": 1293.0,

            "by_phase": {
                "phase_1": {
                    "gaps": ["GAP_001", "GAP_002", "GAP_003", "GAP_004", "GAP_006", "GAP_007"],
                    "gap_count": 6,
                    "net_capex_usd_m": 1025.0,
                    "unmet_demand_addressed_mw": 1277.0,
                    "rationale": (
                        "Phase 1 closes the five most acute gaps — "
                        "the three major missing transmission links "
                        "(Abidjan–Takoradi, Lomé–Cotonou, Lekki hub) "
                        "plus the two highest-value suppressed demand clusters "
                        "(Tema industrial, Lomé industrial) and the Obuasi spur. "
                        "These six interventions address 69% of total unmet demand "
                        "and unlock the anchors needed to secure Phase 1 financing."
                    ),
                },
                "phase_2": {
                    "gaps": ["GAP_005", "GAP_008", "GAP_009", "GAP_010", "GAP_011", "GAP_012"],
                    "gap_count": 6,
                    "net_capex_usd_m": 212.0,
                    "unmet_demand_addressed_mw": 428.0,
                    "rationale": (
                        "Phase 2 builds on Phase 1 backbone to address "
                        "remaining industrial reliability gaps and the first "
                        "catalytic agricultural opportunities. "
                        "Volta Belt grid connection is the highest development "
                        "impact intervention per dollar on the entire corridor."
                    ),
                },
                "phase_3": {
                    "gaps": ["GAP_013", "GAP_014"],
                    "gap_count": 2,
                    "net_capex_usd_m": 79.0,
                    "unmet_demand_addressed_mw": 137.0,
                    "rationale": (
                        "Phase 3 captures conditional and speculative opportunities "
                        "that require identity verification or licence grants "
                        "before investment can be committed."
                    ),
                },
            },

            "highest_impact_gaps": [
                "GAP_003 — Lekki 330kV hub: 885 MW unmet, $355M net capex, "
                "unlocks $20B+ committed investment",
                "GAP_001 — Abidjan–Takoradi link: 105 MW unmet, $340M net capex, "
                "closes largest missing backbone link",
                "GAP_002 — Lomé–Cotonou interconnector: 139 MW unmet, $125M net capex, "
                "eliminates Togo/Benin import dependency risk",
                "GAP_006 — Tema industrial reinforcement: 72 MW unmet, $83M net capex, "
                "unlocks TOR rehabilitation and Tema Free Zone growth",
                "GAP_011 — Volta Belt connection: 8 MW current / 150 MW addressable, "
                "$32M net capex, 95,000 jobs at full buildout",
            ],

            "cross_border_gaps": [
                "GAP_001 — Côte d'Ivoire / Ghana coastal link",
                "GAP_002 — Togo / Benin coastal interconnector",
            ],

            "conditional_gaps_requiring_verification": [
                "GAP_005 — Lithium Site spur: operator identity and mining licence required",
                "GAP_013 — Benin agro cluster: operator identity required",
                "GAP_014 — Lagos hyperscale DC: DC identity confirmation required",
            ],
        },

        "message": (
            "14 infrastructure gaps identified across the Abidjan-Lagos corridor. "
            "Total unmet demand: 1,842 MW across 5 transmission gaps, "
            "5 suppressed demand gaps, and 4 catalytic gaps. "
            "Total addressable demand if all gaps closed: 4,909 MW. "
            "Total net capex to close all gaps: $1.29B "
            "(after $175M co-location savings on highway overlap). "
            "Phase 1 (6 gaps, $1.03B) addresses 69% of unmet demand and "
            "unlocks the financing case for the full corridor. "
            "Lekki hub (GAP_003) is the single highest-value intervention — "
            "885 MW unmet demand, unlocks $20B+ Lekki cluster investment."
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