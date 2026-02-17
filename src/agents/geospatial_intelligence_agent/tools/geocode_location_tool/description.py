TOOL_DESCRIPTION = """
Convert user-provided place names into precise geographic coordinates (lat/lon).

Call this when:
- Source or destination is not already in lat/lon format
- The user gives place names like "Abidjan", "Lagos", "Nairobi to Mombasa", "Tema Port to Kumasi"
- A location name is ambiguous and needs to be resolved to coordinates for routing

Input: JSON with a "locations" array. Each item has "name" (required) and optionally "country".
Example: {"locations": [{"name": "Abidjan", "country": "Côte d'Ivoire"}, {"name": "Lagos", "country": "Nigeria"}]}

Output: JSON with "resolved_locations" array. Each item has "input_name", "latitude", "longitude", and "confidence" (0–1).
"""
