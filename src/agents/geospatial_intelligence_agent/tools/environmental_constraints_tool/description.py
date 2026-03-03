TOOL_DESCRIPTION = """
Identifies legal and environmental 'No-Go' zones by checking overlap between the
corridor and protected area databases. Uses vector data from fetch_geospatial_layers
(vector_uri), performs spatial intersection with the corridor, and optionally applies
a buffer. Checks constraint types such as national parks, wetlands, cultural sites,
and forest reserves. Returns protected areas found, critical conflicts, and whether
mitigation is required for compliance.
"""
