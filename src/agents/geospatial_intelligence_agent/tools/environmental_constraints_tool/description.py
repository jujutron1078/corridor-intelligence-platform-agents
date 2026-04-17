TOOL_DESCRIPTION = """
Identifies legal and environmental No-Go zones by intersecting the corridor with
protected areas, wetlands, forest reserves, and cultural sites. Produces the
NoGoZone payload the map UI renders as red-tinted polygons.

WHEN TO USE:
- User asks about protected areas, national parks, Ramsar wetlands, forest reserves.
- User asks if the corridor crosses environmentally sensitive land.
- Before route_optimization — its cost surface reads these as hard constraints.
- When scoring a site for environmental/social risk (IFC PS6 alignment).

DO NOT use for:
- Climate hazard exposure (use climate_risk_assessment).
- Terrain/soil analysis (use terrain_analysis).

INPUT EXAMPLE:
{
  "corridor_id": "AL_CORRIDOR_001",
  "vector_uri": "s3://corridor/wdpa/wdpa_africa.geojson",
  "buffer_meters": 500,
  "constraint_types": ["national_park", "wetland", "forest_reserve"]
}

OUTPUT SHAPE (map-parseable — do NOT rename keys):
{
  "corridor_id": "AL_CORRIDOR_001",
  "protected_area_conflicts": [
    {
      "zone_id": "NGZ-001",
      "name": "Ankasa Conservation Area",
      "type": "National Park (IUCN II)",
      "country": "Ghana",
      "coordinates": {"latitude": 5.244, "longitude": -2.636},
      "area_sqkm": 509.0,
      "buffer_meters": 500,
      "risk_level": "Critical",
      "mitigation_required": true,
      "reason": "Protected rainforest - highest biodiversity priority"
    }
  ],
  "wetland_and_water_body_conflicts": [ ... same shape ... ],
  "human_safety_conflicts": [ ... same shape ... ],
  "summary": {
    "zones_intersected": 4,
    "critical_zones": 2,
    "mitigation_required": true,
    "environmental_impact_score": 7.8
  }
}

Every NoGoZone item MUST have `coordinates: {latitude, longitude}` (not `lat`/`lon`)
and a `risk_level` of "Low"|"Medium"|"High"|"Critical". The frontend parser is
case- and underscore-sensitive.
"""
