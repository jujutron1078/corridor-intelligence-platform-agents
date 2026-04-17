TOOL_DESCRIPTION = """
Detects existing infrastructure assets (ports, airports, substations, industrial
sites, major junctions, military facilities) along the corridor. Produces the
InfrastructureDetection payload the map UI renders as icon markers.

WHEN TO USE:
- User asks where existing ports/airports/substations are along the corridor.
- User asks about anchor load candidates, industrial zones, free zones.
- User asks about safety hazards along the route (checkpoints, conflict risk).
- Before route_optimization — co-location candidates reduce CAPEX.
- Before opportunity_identification agent analyses — anchor loads feed bankability.

DO NOT use for:
- Generic city lookups (use geocode_location).
- Trade / commerce data (use query_corridor_data).

INPUT EXAMPLE:
{
  "corridor_id": "AL_CORRIDOR_001",
  "image_uri": "s3://corridor/satellite/sentinel2_2024_q4.tif",
  "detection_types": ["energy", "transport", "industrial", "military"],
  "min_confidence": 0.6
}

OUTPUT SHAPE (map-parseable — do NOT rename keys):
{
  "corridor_id": "AL_CORRIDOR_001",
  "infrastructure_identified": [
    {
      "asset_id": "INF-PORT-TEMA-001",
      "asset_type": "port",
      "name": "Port of Tema",
      "country": "Ghana",
      "coordinates": {"latitude": 5.666, "longitude": 0.017},
      "confidence": 0.94,
      "class": "major_port",
      "co_location_candidate": true,
      "risk_severity": "Low",
      "is_road_safety_risk": false,
      "capacity_note": "TEU/year: 2.1M"
    }
  ],
  "road_safety_hazards_identified": [ ... same shape, always has risk_severity ... ],
  "critical_hazards_geojson": { "type": "FeatureCollection", "features": [...] },
  "summary": { "detections_total": 47, "co_location_candidates": 12 }
}

`risk_severity` must be "Low"|"Medium"|"High"|"Critical". `coordinates` must use
`latitude`/`longitude` (not `lat`/`lon`). The frontend parser is case- and
underscore-sensitive.
"""
