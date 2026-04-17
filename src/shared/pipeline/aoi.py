"""
Shared Area of Interest (AOI) definition for the Lagos-Abidjan corridor.

All pipelines and services import corridor geometry from here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shapely.geometry import LineString, box
from shapely.ops import transform

if TYPE_CHECKING:
    import ee


# ── Corridor nodes (lon, lat) ────────────────────────────────────────────────
CORRIDOR_NODES: list[dict] = [
    {"name": "Lagos",          "lon": 3.40,  "lat": 6.45},
    {"name": "Seme Border",    "lon": 2.63,  "lat": 6.46},
    {"name": "Cotonou",        "lon": 2.42,  "lat": 6.37},
    {"name": "Hilacondji",     "lon": 1.62,  "lat": 6.21},
    {"name": "Lomé",           "lon": 1.23,  "lat": 6.17},
    {"name": "Aflao",          "lon": 1.10,  "lat": 6.13},
    {"name": "Tema",           "lon": 0.00,  "lat": 5.55},
    {"name": "Accra",          "lon": -0.19, "lat": 5.60},
    {"name": "Cape Coast",     "lon": -1.02, "lat": 5.10},
    {"name": "Takoradi",       "lon": -1.76, "lat": 4.93},
    {"name": "Axim",           "lon": -2.17, "lat": 5.10},
    {"name": "Elubo",          "lon": -3.00, "lat": 5.27},
    {"name": "Abidjan",        "lon": -3.97, "lat": 5.36},
]

# ── Bounding box ─────────────────────────────────────────────────────────────
BBOX_WEST = -4.5
BBOX_SOUTH = 4.5
BBOX_EAST = 4.0
BBOX_NORTH = 7.0

# ── Countries ─────────────────────────────────────────────────────────────────
COUNTRIES = ["NGA", "BEN", "TGO", "GHA", "CIV"]
COUNTRY_NAMES = {
    "NGA": "Nigeria",
    "BEN": "Benin",
    "TGO": "Togo",
    "GHA": "Ghana",
    "CIV": "Côte d'Ivoire",
}

# ── Buffer ────────────────────────────────────────────────────────────────────
BUFFER_KM = 50


@dataclass(frozen=True)
class CorridorAOI:
    """Immutable corridor geometry container."""

    nodes: list[dict]
    buffer_km: float
    bbox: tuple[float, float, float, float]
    countries: list[str]

    @property
    def node_coords(self) -> list[tuple[float, float]]:
        """Return (lon, lat) tuples for all nodes."""
        return [(n["lon"], n["lat"]) for n in self.nodes]

    @property
    def centerline(self) -> LineString:
        """Corridor centerline as a Shapely LineString."""
        return LineString(self.node_coords)

    @property
    def buffered_polygon(self):
        """Corridor buffered by ~BUFFER_KM (approximate degrees)."""
        # ~0.45 degrees ≈ 50 km at this latitude
        deg_buffer = self.buffer_km / 111.0
        return self.centerline.buffer(deg_buffer)

    @property
    def bbox_polygon(self):
        """Bounding box as a Shapely Polygon."""
        return box(*self.bbox)

    # ── GEE helpers ──────────────────────────────────────────────────────────

    def to_ee_geometry(self) -> "ee.Geometry":
        """Convert buffered corridor polygon to ee.Geometry.Polygon."""
        import ee

        coords = list(self.buffered_polygon.exterior.coords)
        return ee.Geometry.Polygon([[[x, y] for x, y in coords]])

    def to_ee_bbox(self) -> "ee.Geometry.Rectangle":
        """Bounding box as ee.Geometry.Rectangle."""
        import ee

        return ee.Geometry.Rectangle(list(self.bbox))

    def to_ee_point(self, lon: float, lat: float) -> "ee.Geometry.Point":
        """Create an ee.Geometry.Point."""
        import ee

        return ee.Geometry.Point([lon, lat])

    def to_geojson(self) -> dict:
        """Return buffered corridor as a GeoJSON Feature."""
        from shapely.geometry import mapping

        geom = mapping(self.buffered_polygon)
        # Reduce coordinate precision to 5 decimal places (~1 m accuracy)
        # to keep payload small for LLM context windows.
        if "coordinates" in geom:
            geom["coordinates"] = [
                [[round(c, 5) for c in pair] for pair in ring]
                for ring in geom["coordinates"]
            ]

        return {
            "type": "Feature",
            "properties": {
                "name": "Lagos-Abidjan Corridor",
                "buffer_km": self.buffer_km,
                "countries": self.countries,
            },
            "geometry": geom,
        }

    def to_nodes_geojson(self) -> dict:
        """Return corridor nodes as a GeoJSON FeatureCollection."""
        features = []
        for node in self.nodes:
            features.append({
                "type": "Feature",
                "properties": {"name": node["name"]},
                "geometry": {
                    "type": "Point",
                    "coordinates": [node["lon"], node["lat"]],
                },
            })
        return {"type": "FeatureCollection", "features": features}


# ── Singleton instance ────────────────────────────────────────────────────────
CORRIDOR = CorridorAOI(
    nodes=CORRIDOR_NODES,
    buffer_km=BUFFER_KM,
    bbox=(BBOX_WEST, BBOX_SOUTH, BBOX_EAST, BBOX_NORTH),
    countries=COUNTRIES,
)
