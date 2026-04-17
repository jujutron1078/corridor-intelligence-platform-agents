"""Safe coordinate extraction from GeoJSON-like structures."""


def extract_lon_lat(coords) -> tuple[float, float] | None:
    """Safely extract (lon, lat) from various coordinate formats.

    Handles: [lon, lat], [lon, lat, alt], [[lon, lat]], [[[lon, lat]]], etc.
    Returns None if extraction fails.
    """
    if not coords:
        return None
    c = coords
    while isinstance(c, list) and len(c) > 0 and isinstance(c[0], list):
        c = c[0]
    if isinstance(c, (list, tuple)) and len(c) >= 2:
        try:
            return (float(c[0]), float(c[1]))
        except (TypeError, ValueError):
            return None
    return None
