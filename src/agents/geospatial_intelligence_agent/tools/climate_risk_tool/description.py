TOOL_DESCRIPTION = """
Assesses climate-hazard risk (drought, heat stress, coastal flooding, and a
composite multi-hazard score) for the corridor AOI or a specific sub-segment.

WHEN TO USE:
  - User asks about climate vulnerability, drought, heat stress, sea-level rise,
    or long-term asset resilience.
  - You are scoring an investment opportunity and need a hazard badge.
  - Terrain analysis alone is not enough — pair this with terrain_analysis_tool
    for a full environmental picture.

Returns structured JSON with per-hazard `score` (0..1), `category`, and
`details`. The payload maps directly to the frontend ClimateRiskSummary type
in lib/map-overlay.ts so it renders automatically on the map and opportunity
cards.
"""
