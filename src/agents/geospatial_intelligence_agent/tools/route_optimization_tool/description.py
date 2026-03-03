TOOL_DESCRIPTION = """
Calculates the most efficient infrastructure paths using corridor context from earlier
steps (terrain, environmental constraints, infrastructure detections). You only need to
provide the optimization priority: min_cost, min_distance, max_impact, or balance.
Returns optimized route variants with geometry, length, CAPEX, terrain difficulty, and
co-location index for stakeholder review. Run after define_corridor, fetch_geospatial_layers,
terrain_analysis, environmental_constraints, and infrastructure_detection so the tool has
the necessary context.
"""
