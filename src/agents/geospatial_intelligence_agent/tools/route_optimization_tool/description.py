TOOL_DESCRIPTION = """
Calculates the most efficient infrastructure paths by combining terrain (cost surface),
environmental constraints (No-Go zones), and anchor nodes from infrastructure detection.
Accepts corridor_id, anchor node coordinates, cost_surface_uri (Tool 5), constraints_uri
(Tool 6), and optional priority: min_cost, min_distance, max_impact, or balance. Returns
optimized route variants with geometry, length, CAPEX, terrain difficulty, and
co-location index for stakeholder review.
"""
