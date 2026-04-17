TOOL_DESCRIPTION = """
Analyzes elevation, slope, flood risk, and construction difficulty for each
segment of the Lagos-Abidjan corridor. Produces the structured payload the map
UI parses into TerrainSegmentAnalysis overlays.

WHEN TO USE:
- User asks about terrain, elevation, slope, grading, earthworks.
- User asks where flooding, soft soils, or swampy ground will affect routing.
- User wants to know which segments are hardest/easiest to build.
- Before route_optimization, when the routing engine needs a cost surface.
- Before financing_optimization, when CAPEX estimates depend on terrain class.

DO NOT use for:
- Pure locate-on-map queries (use geocode_location).
- Land-use or environmental no-go zones (use environmental_constraints).
- Climate hazards over time (use climate_risk_assessment).

INPUT EXAMPLE:
{
  "corridor_id": "AL_CORRIDOR_001",
  "dem_uri": "s3://corridor/dem/srtm_30m.tif",
  "resolution_meters": 30,
  "analysis_targets": ["slope", "flood_risk", "soil_stability"],
  "sampling_interval_km": 5.0
}

OUTPUT SHAPE (map-parseable — do NOT rename keys):
{
  "analysis_metadata": { "corridor_id": "...", "segments_analyzed": 6, ... },
  "segment_analysis": [
    {
      "segment_id": "SEG-001",
      "label": "Abidjan Coastal Plain",
      "country": "Côte d'Ivoire",
      "start_km": 0, "end_km": 180,
      "start_coordinate": {"latitude": 5.302, "longitude": -4.025},
      "end_coordinate":   {"latitude": 5.110, "longitude": -2.900},
      "slope_analysis":   {"avg_slope_degrees": 1.4, "max_slope_degrees": 6.2},
      "soil_stability":   {"classification": "High", "bearing_capacity_kpa": 280},
      "flood_risk":       {"classification": "Low", "flood_zone_pct": 6},
      "construction_difficulty": {"score": 2.1, "rating": "Easy"}
    }
  ],
  "corridor_summary": { "overall_construction_difficulty": "...", "critical_segments": [...] }
}

Return field names exactly as shown. The frontend parser is case- and
underscore-sensitive. If a metric is unavailable, omit the field — do NOT put
"N/A" strings where numbers are expected.
"""
