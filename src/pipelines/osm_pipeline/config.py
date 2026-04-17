"""OSM pipeline configuration — Overpass API settings, query templates, road classification."""

from __future__ import annotations

from src.shared.pipeline.aoi import BBOX_SOUTH, BBOX_WEST, BBOX_NORTH, BBOX_EAST

# ── Overpass API ─────────────────────────────────────────────────────────────

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT = 180  # seconds per query
OVERPASS_MAX_ELEMENTS = 10_000
RATE_LIMIT_CALLS = 2
RATE_LIMIT_PERIOD = 60  # seconds

# ── Bounding box in Overpass format (south, west, north, east) ───────────────

OVERPASS_BBOX = f"{BBOX_SOUTH},{BBOX_WEST},{BBOX_NORTH},{BBOX_EAST}"

# ── Road classification tiers ────────────────────────────────────────────────

ROAD_TIERS = {
    1: ["motorway", "motorway_link", "trunk", "trunk_link"],
    2: ["primary", "primary_link", "secondary", "secondary_link"],
    3: ["tertiary", "tertiary_link", "unclassified"],
    4: ["residential", "track"],
}

# Reverse lookup: highway type → tier
HIGHWAY_TO_TIER = {}
for tier, types in ROAD_TIERS.items():
    for t in types:
        HIGHWAY_TO_TIER[t] = tier

# ── Query templates ──────────────────────────────────────────────────────────

QUERIES = {
    "roads": """
[out:json][timeout:{timeout}][bbox:{bbox}];
(
  way["highway"~"^(motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|unclassified|residential|track)$"];
);
out body;
>;
out skel qt;
""",

    "railways": """
[out:json][timeout:{timeout}][bbox:{bbox}];
(
  way["railway"~"^(rail|light_rail|narrow_gauge)$"];
);
out body;
>;
out skel qt;
""",

    "ports": """
[out:json][timeout:{timeout}][bbox:{bbox}];
(
  node["amenity"="ferry_terminal"];
  way["amenity"="ferry_terminal"];
  node["man_made"="pier"];
  way["man_made"="pier"];
  node["landuse"="port"];
  way["landuse"="port"];
  relation["landuse"="port"];
  node["harbour"="yes"];
  way["harbour"="yes"];
  node["industrial"="port"];
  way["industrial"="port"];
);
out body;
>;
out skel qt;
""",

    "airports": """
[out:json][timeout:{timeout}][bbox:{bbox}];
(
  node["aeroway"="aerodrome"];
  way["aeroway"="aerodrome"];
  relation["aeroway"="aerodrome"];
);
out body;
>;
out skel qt;
""",

    "industrial": """
[out:json][timeout:{timeout}][bbox:{bbox}];
(
  way["landuse"="industrial"];
  relation["landuse"="industrial"];
);
out body;
>;
out skel qt;
""",

    "sez_ftz": """
[out:json][timeout:{timeout}][bbox:{bbox}];
(
  way["landuse"="industrial"]["industrial"~"free_trade|special_economic|export_processing"];
  relation["landuse"="industrial"]["industrial"~"free_trade|special_economic|export_processing"];
  node["name"~"Free Trade|SEZ|Special Economic|Export Processing",i];
  way["name"~"Free Trade|SEZ|Special Economic|Export Processing",i];
);
out body;
>;
out skel qt;
""",

    "border_crossings": """
[out:json][timeout:{timeout}][bbox:{bbox}];
(
  node["barrier"="border_control"];
  node["border_type"="nation"];
  way["barrier"="border_control"];
);
out body;
>;
out skel qt;
""",

    "pois": """
[out:json][timeout:{timeout}][bbox:{bbox}];
(
  node["amenity"="fuel"];
  node["amenity"="marketplace"];
  node["building"="warehouse"];
  node["office"="customs"];
  node["amenity"="customs"];
  way["amenity"="marketplace"];
  way["building"="warehouse"];
);
out body;
>;
out skel qt;
""",

    "health": """
[out:json][timeout:{timeout}][bbox:{bbox}];
(
  node["amenity"="hospital"];
  way["amenity"="hospital"];
  relation["amenity"="hospital"];
  node["amenity"="clinic"];
  way["amenity"="clinic"];
  node["amenity"="doctors"];
  node["amenity"="pharmacy"];
  node["amenity"="dentist"];
  node["healthcare"="hospital"];
  way["healthcare"="hospital"];
  node["healthcare"="clinic"];
  node["healthcare"="centre"];
  way["healthcare"="centre"];
);
out body;
>;
out skel qt;
""",

    "education": """
[out:json][timeout:{timeout}][bbox:{bbox}];
(
  node["amenity"="school"];
  way["amenity"="school"];
  relation["amenity"="school"];
  node["amenity"="university"];
  way["amenity"="university"];
  relation["amenity"="university"];
  node["amenity"="college"];
  way["amenity"="college"];
  node["amenity"="kindergarten"];
  way["amenity"="kindergarten"];
  node["amenity"="library"];
  way["amenity"="library"];
);
out body;
>;
out skel qt;
""",

    "government": """
[out:json][timeout:{timeout}][bbox:{bbox}];
(
  node["amenity"="police"];
  way["amenity"="police"];
  node["amenity"="fire_station"];
  way["amenity"="fire_station"];
  node["amenity"="townhall"];
  way["amenity"="townhall"];
  node["amenity"="courthouse"];
  way["amenity"="courthouse"];
  node["office"="government"];
  way["office"="government"];
  node["amenity"="post_office"];
  node["amenity"="prison"];
  way["amenity"="prison"];
);
out body;
>;
out skel qt;
""",

    "financial": """
[out:json][timeout:{timeout}][bbox:{bbox}];
(
  node["amenity"="bank"];
  way["amenity"="bank"];
  node["amenity"="atm"];
  node["amenity"="bureau_de_change"];
  node["amenity"="money_transfer"];
  node["office"="insurance"];
  node["amenity"="microfinance"];
);
out body;
>;
out skel qt;
""",

    "religious": """
[out:json][timeout:{timeout}][bbox:{bbox}];
(
  node["amenity"="place_of_worship"];
  way["amenity"="place_of_worship"];
  relation["amenity"="place_of_worship"];
);
out body;
>;
out skel qt;
""",

    "military": """
[out:json][timeout:{timeout}][bbox:{bbox}];
(
  node["military"];
  way["military"];
  relation["military"];
  node["landuse"="military"];
  way["landuse"="military"];
  relation["landuse"="military"];
);
out body;
>;
out skel qt;
""",

    "recreational": """
[out:json][timeout:{timeout}][bbox:{bbox}];
(
  node["leisure"="park"];
  way["leisure"="park"];
  relation["leisure"="park"];
  node["leisure"="sports_centre"];
  way["leisure"="sports_centre"];
  node["leisure"="stadium"];
  way["leisure"="stadium"];
  node["leisure"="swimming_pool"];
  way["leisure"="swimming_pool"];
  node["leisure"="pitch"];
  way["leisure"="pitch"];
  node["tourism"="hotel"];
  way["tourism"="hotel"];
  node["tourism"="attraction"];
  way["tourism"="attraction"];
  node["tourism"="museum"];
  way["tourism"="museum"];
);
out body;
>;
out skel qt;
""",
}

# ── Output paths ─────────────────────────────────────────────────────────────

from pathlib import Path
from src.shared.pipeline.utils import DATA_DIR

OSM_DATA_DIR = DATA_DIR / "osm"
OSM_OUTPUT_FILES = {
    "roads": OSM_DATA_DIR / "roads.geojson",
    "railways": OSM_DATA_DIR / "railways.geojson",
    "ports": OSM_DATA_DIR / "ports.geojson",
    "airports": OSM_DATA_DIR / "airports.geojson",
    "industrial": OSM_DATA_DIR / "industrial.geojson",
    "sez_ftz": OSM_DATA_DIR / "sez_ftz.geojson",
    "border_crossings": OSM_DATA_DIR / "border_crossings.geojson",
    "pois": OSM_DATA_DIR / "pois.geojson",
    "health": OSM_DATA_DIR / "health.geojson",
    "education": OSM_DATA_DIR / "education.geojson",
    "government": OSM_DATA_DIR / "government.geojson",
    "financial": OSM_DATA_DIR / "financial.geojson",
    "religious": OSM_DATA_DIR / "religious.geojson",
    "military": OSM_DATA_DIR / "military.geojson",
    "recreational": OSM_DATA_DIR / "recreational.geojson",
    "network": OSM_DATA_DIR / "road_network.json",
}
