TOOL_DESCRIPTION = """
Generates optimized route variants across the corridor using the cost surface
built by terrain_analysis + environmental_constraints + infrastructure_detection.
Produces the RouteVariant payload the UI renders as colored lines.

WHEN TO USE:
- User asks "what's the best route from X to Y" or "show me route options".
- User asks to compare min-cost vs min-distance vs max-impact variants.
- User wants to minimise protected-area impact while keeping CAPEX reasonable.
- Before infrastructure_optimization's phasing / CAPEX detail pass.

PRE-REQS:
- define_corridor_tool (gives corridor_id and AOI).
- fetch_geospatial_layers_tool (DEM, WDPA, OSM vectors).
- terrain_analysis_tool (slope + flood + soil cost surface).
- environmental_constraints_tool (hard no-go zones).
- infrastructure_detection_tool (co-location candidates).

If any pre-req output is missing, call the corresponding tool first. Do NOT ask
the user to supply cost-surface parameters — infer them from the upstream tools.

INPUT EXAMPLE:
{
  "corridor_id": "AL_CORRIDOR_001",
  "optimization_priority": "balance",
  "num_variants": 3
}

OUTPUT SHAPE (map-parseable — do NOT rename keys):
{
  "corridor_id": "AL_CORRIDOR_001",
  "route_variants": [
    {
      "variant_id": "ROUTE-A",
      "name": "Coastal highway co-located",
      "priority": "min_cost",
      "geometry": { "type": "LineString", "coordinates": [[lon, lat], ...] },
      "length_km": 1028,
      "capex_usd_billion": 14.7,
      "avg_terrain_difficulty": 3.4,
      "co_location_index": 0.67,
      "no_go_buffer_violations": 0,
      "km_through_protected_areas": 0
    }
  ],
  "recommended_variant_id": "ROUTE-A",
  "summary": { "variants_generated": 3, "best_capex_usd_billion": 14.7 }
}

Geometry MUST be a valid GeoJSON LineString with `[longitude, latitude]` pairs
(note the order). The frontend parser is case- and underscore-sensitive.
"""
