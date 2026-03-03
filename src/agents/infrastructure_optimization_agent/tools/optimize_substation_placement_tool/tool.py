import json
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .description import TOOL_DESCRIPTION
from .schema import SubstationPlacementInput


@tool("optimize_substation_placement", description=TOOL_DESCRIPTION)
def optimize_substation_placement_tool(
    payload: SubstationPlacementInput, runtime: ToolRuntime
) -> Command:
    """Determines optimal GPS locations for substations based on load proximity."""

    # In a real-world scenario, this tool would:
    # 1. Use 'K-means clustering' to find centers of gravity for anchor loads.
    # 2. Ensure substations are placed within 10km of major industrial clusters.
    # 3. Check for flat terrain and road access for the substation footprint.

    response = {
        "corridor_id": "AL_CORRIDOR_POC_001",
        "placement_philosophy": (
            "Substations are placed at the center of gravity of anchor load clusters, "
            "constrained to within 10km of the highest-demand anchor in each cluster. "
            "Priority is given to flat terrain, road access, and proximity to the "
            "highway right-of-way for construction logistics. Critical-class anchors "
            "receive dedicated substation bays rather than shared feeders."
        ),

        # ================================================================
        # PRIMARY HUBS — Major transformation nodes on the backbone
        # ================================================================
        "primary_hubs": [

            {
                # Abidjan: Western anchor of the corridor
                "id": "HUB_ABIDJAN_VRIDI",
                "name": "Abidjan Vridi 225kV Industrial Hub",
                "coords": [5.302, -4.025],
                "voltage_levels": ["225kV", "33kV", "11kV"],
                "phase": "Phase 1",
                "segment_ref": "SEG_DR_003",
                "serves": [
                    "AL_ANC_003",   # Azito Thermal Power Plant
                    "AL_ANC_004",   # CIPREL Power Plant
                    "AL_ANC_005",   # Port of Abidjan Industrial Zone
                ],
                "capacity_mw": 180.0,
                "terrain": "Flat coastal industrial land — minimal civil works required",
                "road_access": "Direct access via Boulevard du Canal",
                "distance_to_highway_m": 320.0,
                "land_status": "State-owned industrial land — no acquisition required",
                "rationale": (
                    "Vridi peninsula is the natural hub for western Abidjan anchors. "
                    "Azito and CIPREL are both within 3km — shared substation "
                    "eliminates two separate connection points and reduces CAPEX by $18M. "
                    "Port of Abidjan industrial zone is 2.1km east on same peninsula."
                ),
            },

            {
                # Takoradi: First major Ghana hub
                "id": "HUB_TAKORADI_ABOADZE",
                "name": "Aboadze 330kV Transmission Hub, Takoradi",
                "coords": [4.926, -1.980],
                "voltage_levels": ["330kV", "161kV", "33kV"],
                "phase": "Phase 1",
                "segment_ref": "SEG_BB_001",
                "serves": [
                    "AL_ANC_015",   # Takoradi Port
                    "AL_ANC_016",   # Tema Oil Refinery (TOR)
                ],
                "capacity_mw": 520.0,
                "terrain": "Flat coastal plain — existing Aboadze substation footprint available",
                "road_access": "N1 coastal highway adjacent",
                "distance_to_highway_m": 180.0,
                "land_status": "Existing GRIDCo substation — expansion of current footprint",
                "rationale": (
                    "Existing Aboadze 330kV substation is the natural termination point "
                    "for SEG_BB_001 from Abidjan. Expansion of existing GRIDCo facility "
                    "avoids greenfield land acquisition and saves $12M in civil works. "
                    "Takoradi Port (AL_ANC_015) is 4.2km — dedicated 33kV feeder from hub."
                ),
            },

            {
                # Tema/Accra: Largest Ghana hub — Critical anchors
                "id": "HUB_TEMA_INDUSTRIAL",
                "name": "Tema Industrial 330kV Hub, Greater Accra",
                "coords": [5.650, -0.018],
                "voltage_levels": ["330kV", "161kV", "33kV"],
                "phase": "Phase 1",
                "segment_ref": "SEG_BB_002",
                "serves": [
                    "AL_ANC_007",   # Akosombo Dam (generation interconnect)
                    "AL_ANC_008",   # Tema Port MPS (Critical class)
                    "AL_ANC_009",   # Tema Free Zone (Critical class)
                    "AL_ANC_016",   # Nzema Solar Power Station feed-in
                ],
                "capacity_mw": 800.0,
                "terrain": "Flat industrial zone — Tema port authority land",
                "road_access": "Tema Motorway and port access roads",
                "distance_to_highway_m": 210.0,
                "land_status": "Partial GRIDCo ownership — 2.4ha additional land required",
                "rationale": (
                    "Tema Industrial hub is the largest capacity node between Abidjan and Lagos. "
                    "Tema Port (Critical class) and Tema Free Zone (Critical class) require "
                    "N-1-1 feeds — both served from dedicated bays on separate busbars. "
                    "Hub also receives Akosombo hydro power (330kV interconnect) "
                    "providing generation diversity for the corridor."
                ),
            },

            {
                # Lomé: Togo hub serving port and industrial zone
                "id": "HUB_LOME_TOKOIN",
                "name": "Tokoin 330kV Hub, Lomé, Togo",
                "coords": [6.137, 1.223],
                "voltage_levels": ["330kV", "161kV", "33kV"],
                "phase": "Phase 1",
                "segment_ref": "SEG_BB_003",
                "serves": [
                    "AL_ANC_017",   # Port of Lomé (Critical class)
                    "AL_ANC_019",   # Lomé Cement Plant
                    "AL_ANC_020",   # Lomé Free Zone
                ],
                "capacity_mw": 300.0,
                "terrain": "Flat coastal plain north of Lomé city center",
                "road_access": "Route Nationale 1 — 400m from hub site",
                "distance_to_highway_m": 400.0,
                "land_status": "CEET (Togo utility) land — interutility agreement required",
                "rationale": (
                    "Tokoin is the existing CEET 161kV substation location. "
                    "Upgrading to 330kV at existing site avoids greenfield development "
                    "in congested Lomé peri-urban area. "
                    "Port of Lomé (Critical class) receives dedicated 161kV ring feeder "
                    "from this hub (SEG_DR_001). "
                    "Hub is midpoint between SEG_BB_003 (from Tema) and SEG_BB_004 (to Cotonou)."
                ),
            },

            {
                # Cotonou: Benin hub — import replacement node
                "id": "HUB_COTONOU_MARIA_GLETA",
                "name": "Maria Gleta 330kV Hub, Cotonou, Benin",
                "coords": [6.425, 2.406],
                "voltage_levels": ["330kV", "33kV"],
                "phase": "Phase 2",
                "segment_ref": "SEG_BB_004",
                "serves": [
                    "AL_ANC_022",   # Port of Cotonou (Critical class)
                    "AL_ANC_023",   # Zone Industrielle Cotonou
                ],
                "capacity_mw": 200.0,
                "terrain": "Flat coastal plain — existing TEC Maria Gleta plant site",
                "road_access": "Route Inter-États N1 adjacent",
                "distance_to_highway_m": 150.0,
                "land_status": "Co-located with TEC thermal plant — land-sharing agreement",
                "rationale": (
                    "Maria Gleta thermal plant site (AL_ANC_024) provides co-location "
                    "opportunity — new 330kV substation shares land and security with "
                    "existing plant, reducing CAPEX by $9M. "
                    "Also serves as 400/330kV interface point for SEG_BB_005 "
                    "arriving from Lagos at 400kV."
                ),
            },

            {
                # Lekki: Eastern anchor — most complex hub on corridor
                "id": "HUB_LEKKI_400KV",
                "name": "Lekki 400kV Transmission Hub, Lagos",
                "coords": [6.435, 3.820],
                "voltage_levels": ["400kV", "330kV", "132kV"],
                "phase": "Phase 1",
                "segment_ref": "SEG_BB_005",
                "serves": [
                    "AL_ANC_027",   # Dangote Refinery (Critical — 1,000 MW)
                    "AL_ANC_028",   # Lekki FTZ (150 MW → 1,200 MW)
                    "AL_ANC_029",   # Lekki Deep Sea Port
                    "AL_ANC_030",   # MainOne Data Center (Critical class)
                ],
                "capacity_mw": 4500.0,
                "phase_1a_capacity_mw": 500.0,
                "phase_1b_capacity_mw": 2500.0,
                "terrain": "Reclaimed coastal land — pile foundation required (12m depth)",
                "road_access": "Lekki–Epe Expressway — 600m from hub site",
                "distance_to_highway_m": 600.0,
                "land_status": "Lekki FTZ authority land — long-term lease agreement",
                "rationale": (
                    "Lekki hub is the most complex and highest-capacity asset on the corridor. "
                    "Dangote Refinery (1,000 MW, Critical class) receives two dedicated "
                    "330kV feeders on separate busbars — a fault on Lekki FTZ busbar "
                    "cannot interrupt refinery supply. "
                    "Hub designed for 4,500 MW ultimate capacity to accommodate "
                    "full Lekki FTZ buildout (1,200 MW) by Year 20. "
                    "Phase 1A ($145M) delivers 500 MW immediately for Dangote commissioning."
                ),
            },
        ],

        # ================================================================
        # SPUR SUBSTATIONS — Dedicated step-down points for anchor loads
        # ================================================================
        "spur_substations": [

            {
                "id": "SUB_KUMASI_330KV",
                "name": "Kumasi 330kV Switching Substation, Ashanti Region",
                "coords": [6.688, -1.624],
                "voltage_levels": ["330kV", "161kV"],
                "phase": "Phase 1",
                "segment_ref": "SEG_SP_001",
                "serves": ["AL_ANC_012"],  # Obuasi Gold Mine
                "capacity_mw": 160.0,
                "terrain": "Flat urban fringe — Kumasi industrial area",
                "road_access": "Accra–Kumasi N6 highway — 200m",
                "distance_to_highway_m": 200.0,
                "land_status": "GRIDCo existing Kumasi substation — 161kV bay addition",
                "rationale": (
                    "Kumasi is the natural off-take point for the Obuasi spur (SEG_SP_001). "
                    "GRIDCo Kumasi substation already has 330kV infrastructure — "
                    "adding a 161kV bay for the Obuasi spur costs only $8M "
                    "versus $35M for a new standalone substation. "
                    "Obuasi mine is 98km south on dedicated 161kV double-circuit."
                ),
            },

            {
                "id": "SUB_OBUASI_MINE",
                "name": "Obuasi Mine 330/11kV Receiving Substation",
                "coords": [6.204, -1.672],
                "voltage_levels": ["161kV", "11kV"],
                "phase": "Phase 1",
                "segment_ref": "SEG_SP_001",
                "serves": ["AL_ANC_012"],  # Obuasi Gold Mine (AngloGold Ashanti)
                "capacity_mw": 130.0,
                "terrain": "Mine site — AngloGold Ashanti controlled land",
                "road_access": "Mine haul roads — full heavy vehicle access",
                "distance_to_highway_m": 4200.0,
                "land_status": "AngloGold Ashanti land — no acquisition cost",
                "rationale": (
                    "On-site receiving substation at mine boundary. "
                    "AngloGold Ashanti owns the land — no acquisition required. "
                    "Substation steps 161kV down to 11kV for mine distribution. "
                    "N-1-1 double-circuit incoming (Critical class underground mine). "
                    "On-site diesel emergency backup covers fault restoration window."
                ),
            },

            {
                "id": "SUB_AKUSE_161KV",
                "name": "Akuse 161kV Switching Station, Volta Region",
                "coords": [6.093, 0.120],
                "voltage_levels": ["161kV", "33kV"],
                "phase": "Phase 2",
                "segment_ref": "SEG_SP_002",
                "serves": ["AL_ANC_014"],  # Weta Rice Farm / Volta Agricultural Belt
                "capacity_mw": 180.0,
                "terrain": "Flat Volta basin — minimal earthworks",
                "road_access": "Akuse–Sogakope road — 150m",
                "distance_to_highway_m": 2100.0,
                "land_status": "VRA (Volta River Authority) land — coordination required",
                "rationale": (
                    "Akuse is adjacent to the existing Akosombo–Tema 161kV line — "
                    "a T-off at this point avoids building new switching infrastructure. "
                    "VRA coordination required as Akuse is within VRA operational area. "
                    "CONDITIONAL — do not commit until AfDB SAPZ co-financing approved."
                ),
            },

            {
                "id": "SUB_WETA_ZONE",
                "name": "Weta Zone 161/33kV Agricultural Substation",
                "coords": [6.032, 0.607],
                "voltage_levels": ["161kV", "33kV"],
                "phase": "Phase 2",
                "segment_ref": "SEG_SP_002",
                "serves": ["AL_ANC_014"],  # Weta Rice Farm
                "capacity_mw": 100.0,
                "terrain": "Volta River floodplain — elevated platform required (+1.5m)",
                "road_access": "Seasonal farm tracks — temporary access road ($0.8M) needed",
                "distance_to_highway_m": 8500.0,
                "land_status": "Agricultural land — acquisition from Weta Farm operator",
                "rationale": (
                    "Terminal substation for Volta agricultural spur. "
                    "Steps 161kV down to 33kV for irrigation pump distribution. "
                    "Elevated platform required — Volta floodplain floods seasonally. "
                    "Sized for 100 MW current thermal rating with upgrade path to "
                    "200 MVA when irrigation expansion demand materialises."
                ),
            },

            {
                "id": "SUB_MAMPONG_161KV",
                "name": "Mampong 161kV Switching Station (Conditional)",
                "coords": [7.060, -1.401],
                "voltage_levels": ["161kV", "33kV"],
                "phase": "Phase 3",
                "segment_ref": "SEG_SP_003",
                "serves": ["AL_ANC_035"],  # Lithium Site (conditional)
                "capacity_mw": 168.0,
                "terrain": "Rolling Ashanti highlands — moderate civil works",
                "road_access": "Kumasi–Mampong road — 300m",
                "distance_to_highway_m": 3400.0,
                "land_status": "CONDITIONAL — land identification pending mine licence",
                "rationale": (
                    "CONDITIONAL substation — do not proceed until Ghana Minerals "
                    "Commission grants mining licence and operator identity confirmed. "
                    "Mampong is the nearest existing 161kV infrastructure to the "
                    "lithium site — T-off point for the 44km spur (SEG_SP_003)."
                ),
            },
        ],

        # ================================================================
        # DISTRIBUTION REINFORCEMENT SUBSTATIONS
        # ================================================================
        "distribution_substations": [

            {
                "id": "SUB_LOME_INDUSTRIAL_RING",
                "name": "Lomé Industrial 161kV Ring — Port, Cement, Free Zone",
                "coords": [6.149, 1.271],
                "voltage_levels": ["161kV", "33kV"],
                "phase": "Phase 1",
                "segment_ref": "SEG_DR_001",
                "serves": [
                    "AL_ANC_017",  # Port of Lomé
                    "AL_ANC_019",  # Lomé Cement Plant
                    "AL_ANC_020",  # Lomé Free Zone
                ],
                "configuration": "Ring main — 3 switching points",
                "capacity_mw": 200.0,
                "terrain": "Flat port area — XLPE underground in port zone, overhead elsewhere",
                "rationale": (
                    "Ring main topology isolates industrial supply from residential Togo grid. "
                    "Three switching points at port, cement plant, and free zone — "
                    "any section fault is isolated while the rest of the ring supplies normally."
                ),
            },

            {
                "id": "SUB_COTONOU_INDUSTRIAL",
                "name": "Zone Industrielle Cotonou 33kV Dedicated Substation",
                "coords": [6.420, 2.391],
                "voltage_levels": ["33kV", "11kV"],
                "phase": "Phase 2",
                "segment_ref": "SEG_DR_002",
                "serves": ["AL_ANC_023"],  # Zone Industrielle Cotonou
                "capacity_mw": 65.0,
                "terrain": "Existing industrial zone — substation within zone boundary",
                "distance_to_highway_m": 280.0,
                "land_status": "Industrial zone authority land — no acquisition required",
                "rationale": (
                    "Dedicated 33kV feeder from Maria Gleta hub (8km XLPE underground). "
                    "STATCOM 50 MVAr at substation provides ±1.5% voltage regulation — "
                    "isolates industrial loads from chronic Benin residential grid instability."
                ),
            },

            {
                "id": "SUB_ABIDJAN_VRIDI_UPGRADE",
                "name": "Abidjan Vridi 225/11kV Industrial Substation Upgrade",
                "coords": [5.296, -4.012],
                "voltage_levels": ["225kV", "11kV"],
                "phase": "Phase 2",
                "segment_ref": "SEG_DR_003",
                "serves": [
                    "AL_ANC_003",  # Azito Thermal
                    "AL_ANC_004",  # CIPREL
                    "AL_ANC_005",  # Port of Abidjan Zone
                ],
                "capacity_mw": 180.0,
                "terrain": "Existing Abidjan 225kV ring infrastructure — upgrade only",
                "land_status": "CIE (Côte d'Ivoire utility) existing land",
                "rationale": (
                    "New 225/11kV transformer bays added to existing Vridi substation. "
                    "Separates port and industrial supply from residential CIE distribution. "
                    "225kV interface allows both Azito and CIPREL to supply independently — "
                    "generation diversity for critical port operations."
                ),
            },

            {
                "id": "SUB_SAGAMU_132KV_UPGRADE",
                "name": "Sagamu Interchange 132kV Substation Upgrade",
                "coords": [6.838, 3.648],
                "voltage_levels": ["132kV", "33kV"],
                "phase": "Phase 2",
                "segment_ref": "SEG_DR_004",
                "serves": ["AL_ANC_032"],  # Sagamu Industrial Cluster
                "capacity_mw": 100.0,
                "terrain": "Existing TCN substation — transformer replacement only",
                "land_status": "TCN Nigeria existing land — no acquisition required",
                "rationale": (
                    "Lowest cost intervention on corridor at $28M. "
                    "Existing 1×40 MVA transformer replaced with 2×60 MVA — "
                    "provides N-1 redundancy and doubles capacity to 100 MW. "
                    "No new line construction — substation upgrade only."
                ),
            },
        ],

        # ================================================================
        # CORRIDOR SUMMARY
        # ================================================================
        "corridor_summary": {
            "total_substations": 15,
            "primary_hubs": 6,
            "spur_substations": 5,
            "distribution_substations": 4,

            "by_phase": {
                "phase_1": {
                    "count": 7,
                    "substations": [
                        "HUB_ABIDJAN_VRIDI",
                        "HUB_TAKORADI_ABOADZE",
                        "HUB_TEMA_INDUSTRIAL",
                        "HUB_LOME_TOKOIN",
                        "HUB_LEKKI_400KV",
                        "SUB_KUMASI_330KV",
                        "SUB_OBUASI_MINE",
                        "SUB_LOME_INDUSTRIAL_RING",
                    ],
                    "rationale": "Phase 1 substations serve Critical-class anchors and backbone segments.",
                },
                "phase_2": {
                    "count": 6,
                    "substations": [
                        "HUB_COTONOU_MARIA_GLETA",
                        "SUB_AKUSE_161KV",
                        "SUB_WETA_ZONE",
                        "SUB_COTONOU_INDUSTRIAL",
                        "SUB_ABIDJAN_VRIDI_UPGRADE",
                        "SUB_SAGAMU_132KV_UPGRADE",
                    ],
                    "rationale": "Phase 2 substations extend coverage to agricultural and industrial zones.",
                },
                "phase_3": {
                    "count": 1,
                    "substations": ["SUB_MAMPONG_161KV"],
                    "rationale": "Phase 3 conditional on lithium mine licence approval.",
                },
            },

            "by_country": {
                "cote_divoire": ["HUB_ABIDJAN_VRIDI", "SUB_ABIDJAN_VRIDI_UPGRADE"],
                "ghana": [
                    "HUB_TAKORADI_ABOADZE", "HUB_TEMA_INDUSTRIAL",
                    "SUB_KUMASI_330KV", "SUB_OBUASI_MINE",
                    "SUB_AKUSE_161KV", "SUB_WETA_ZONE", "SUB_MAMPONG_161KV",
                ],
                "togo": ["HUB_LOME_TOKOIN", "SUB_LOME_INDUSTRIAL_RING"],
                "benin": ["HUB_COTONOU_MARIA_GLETA", "SUB_COTONOU_INDUSTRIAL"],
                "nigeria": ["HUB_LEKKI_400KV", "SUB_SAGAMU_132KV_UPGRADE"],
            },

            "anchor_loads_served": {
                "total_anchors_connected": 22,
                "critical_class": [
                    "AL_ANC_008",  # Tema Port MPS
                    "AL_ANC_009",  # Tema Free Zone
                    "AL_ANC_012",  # Obuasi Gold Mine
                    "AL_ANC_017",  # Port of Lomé
                    "AL_ANC_022",  # Port of Cotonou
                    "AL_ANC_027",  # Dangote Refinery
                    "AL_ANC_030",  # MainOne Data Center
                ],
                "high_class": [
                    "AL_ANC_005",  # Port of Abidjan
                    "AL_ANC_015",  # Takoradi Port
                    "AL_ANC_019",  # Lomé Cement Plant
                    "AL_ANC_028",  # Lekki FTZ
                    "AL_ANC_029",  # Lekki Deep Sea Port
                    "AL_ANC_032",  # Sagamu Industrial
                ],
                "standard_class": [
                    "AL_ANC_014",  # Weta Rice Farm
                    "AL_ANC_035",  # Lithium Site (conditional)
                ],
            },

            "greenfield_vs_brownfield": {
                "greenfield_new_build": 8,
                "brownfield_expansion_of_existing": 5,
                "conditional_not_yet_approved": 2,
                "note": (
                    "55% of substations leverage existing utility land or infrastructure, "
                    "reducing total civil CAPEX by an estimated $62M vs full greenfield build."
                ),
            },

            "total_capacity_summary": {
                "total_transformation_capacity_mw": 7063.0,
                "phase_1_capacity_mw": 5010.0,
                "phase_2_capacity_mw": 1893.0,
                "phase_3_capacity_mw": 168.0,
            },
        },

        "message": (
            "Substation placement optimized for 15 nodes across the 1,080km Abidjan-Lagos corridor. "
            "6 primary transmission hubs (225–400kV) anchor the backbone; "
            "5 spur substations serve dedicated anchor loads (mines, agriculture); "
            "4 distribution reinforcements deliver industrial-grade supply to economic zones. "
            "Phase 1 prioritizes 7 substations serving all Critical-class anchors including "
            "Dangote Refinery (1,000 MW), Tema Port, and Obuasi Gold Mine. "
            "55% of sites leverage existing utility land — saving $62M in civil CAPEX. "
            "1 substation (Mampong) remains conditional on Ghana mining licence approval."
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