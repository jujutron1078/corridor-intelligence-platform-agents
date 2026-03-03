TOOL_DESCRIPTION = """
Runs computer vision inference on satellite imagery to detect anchor loads and
existing infrastructure points. Accepts an S3 image URI from the fetch_geospatial_layers
tool and a list of infrastructure types to detect (e.g. energy, transport, settlements).
Returns detected features with coordinates, labels, confidence scores, and class.
"""
