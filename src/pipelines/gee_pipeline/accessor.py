"""
CorridorDataAPI — clean interface for accessing all GEE corridor data.

Usage:
    api = CorridorDataAPI()
    img = api.nightlights(2023, 6)
    point_data = api.sample_at_point(lon=-0.19, lat=5.60)
    tile_url = api.quick_map(img, "nightlights")
"""

from __future__ import annotations

import logging
from typing import Any

import ee

from src.shared.pipeline.aoi import CORRIDOR, CORRIDOR_NODES
from . import processors
from .config import (
    VIS_PARAMS, DEFAULT_SCALE, MAX_PIXELS, TEST_POINTS,
    WORLDCOVER_CLASSES, DYNAMIC_WORLD_CLASSES,
)

logger = logging.getLogger("corridor.gee")


class CorridorDataAPI:
    """Unified access to all GEE corridor datasets."""

    def __init__(self, project: str | None = None):
        """
        Initialize GEE and the corridor API.

        Args:
            project: GEE cloud project ID. If None, uses default credentials.
        """
        try:
            if project:
                ee.Initialize(project=project)
            else:
                ee.Initialize()
            logger.info("GEE initialized successfully")
        except Exception:
            ee.Authenticate()
            ee.Initialize(project=project)
            logger.info("GEE authenticated and initialized")

        self._aoi = CORRIDOR.to_ee_geometry()

    # ── Tier 1: Core Economic ────────────────────────────────────────────────

    def sentinel2(self, year: int, month: int) -> ee.Image:
        """Sentinel-2 monthly composite with NDVI, NDBI, MNDWI."""
        return processors.sentinel2_composite(year, month)

    def ndvi(self, year: int, month: int) -> ee.Image:
        """NDVI from Sentinel-2."""
        return self.sentinel2(year, month).select("NDVI")

    def ndbi(self, year: int, month: int) -> ee.Image:
        """NDBI from Sentinel-2."""
        return self.sentinel2(year, month).select("NDBI")

    def nightlights(self, year: int, month: int) -> ee.Image:
        """VIIRS nighttime lights."""
        return processors.nightlights(year, month)

    def nightlights_change(self, year_start: int, year_end: int) -> ee.Image:
        """Nightlight radiance change between two years."""
        return processors.nightlights_change(year_start, year_end)

    def worldcover(self) -> ee.Image:
        """ESA WorldCover 10m (2021)."""
        return processors.worldcover()

    def dynamic_world(self, year: int, month: int) -> ee.Image:
        """Dynamic World monthly mode composite."""
        return processors.dynamic_world(year, month)

    def elevation(self) -> ee.Image:
        """SRTM elevation, slope, aspect."""
        return processors.elevation()

    def population(self, year: int) -> ee.Image:
        """WorldPop gridded population."""
        return processors.population(year)

    def population_change(self, year_start: int, year_end: int) -> ee.Image:
        """Population change between years."""
        return processors.population_change(year_start, year_end)

    def surface_water(self) -> ee.Image:
        """JRC Global Surface Water."""
        return processors.surface_water()

    def hansen_forest(self) -> ee.Image:
        """Hansen forest change."""
        return processors.hansen_forest()

    def forest_loss_by_year(self, start_year: int, end_year: int) -> ee.Image:
        """Forest loss within a year range."""
        return processors.forest_loss_by_year(start_year, end_year)

    # ── Tier 2: Enrichment ───────────────────────────────────────────────────

    def copernicus_dem(self) -> ee.Image:
        """Copernicus GLO-30 DEM."""
        return processors.copernicus_dem()

    def ghsl_built(self, epoch: int = 2020) -> ee.Image:
        """GHSL built-up surface for a given epoch."""
        return processors.ghsl_built(epoch)

    def ghsl_change(self, epoch_start: int, epoch_end: int) -> ee.Image:
        """GHSL built-up change between epochs."""
        return processors.ghsl_change(epoch_start, epoch_end)

    def building_density(self) -> ee.Image:
        """Google Open Buildings rasterized density."""
        return processors.open_buildings_density()

    def sentinel1(self, year: int, month: int) -> ee.Image:
        """Sentinel-1 SAR monthly composite (VV, VH, VV/VH ratio)."""
        return processors.sentinel1_composite(year, month)

    def climate(self, year: int, month: int) -> ee.Image:
        """ERA5-Land monthly climate (temperature, precipitation, wind)."""
        return processors.era5_climate(year, month)

    # ── Environmental & Health ────────────────────────────────────────────────

    def protected_areas(self) -> ee.Image:
        """WDPA Protected Areas binary mask (1=protected)."""
        return processors.protected_areas()

    def protected_areas_vector(self) -> ee.FeatureCollection:
        """WDPA Protected Areas as vector polygons."""
        return processors.protected_areas_vector()

    def healthcare_accessibility(self) -> ee.Image:
        """Oxford/MAP travel time to nearest healthcare facility (minutes)."""
        return processors.healthcare_accessibility()

    # ── Composite Indices ────────────────────────────────────────────────────

    def economic_activity_index(self, year: int, month: int) -> ee.Image:
        """Composite Economic Activity Index (0-1)."""
        return processors.economic_activity_index(year, month)

    # ── Change Detection ─────────────────────────────────────────────────────

    def urban_expansion(self, year_start: int, year_end: int) -> ee.Image:
        """Urban expansion detection via Dynamic World."""
        return processors.urban_expansion(year_start, year_end)

    # ── Sampling & Statistics ────────────────────────────────────────────────

    def sample_at_point(
        self,
        lon: float,
        lat: float,
        year: int = 2023,
        month: int = 6,
    ) -> dict[str, Any]:
        """
        Sample all available data layers at a specific point.

        Returns a dict with NDVI, nightlights, elevation, population,
        landcover, economic_index, etc.
        """
        point = ee.Geometry.Point([lon, lat])

        # Build a composite of key bands
        try:
            nl = self.nightlights(year, month).rename("nightlights")
        except Exception:
            nl = ee.Image(0).rename("nightlights")

        try:
            s2 = self.sentinel2(year, month)
            ndvi_img = s2.select("NDVI")
            ndbi_img = s2.select("NDBI")
        except Exception:
            ndvi_img = ee.Image(0).rename("NDVI")
            ndbi_img = ee.Image(0).rename("NDBI")

        elev = self.elevation().select("elevation")
        slope = self.elevation().select("slope")

        try:
            pop = self.population(min(year, 2020)).rename("population")
        except Exception:
            pop = ee.Image(0).rename("population")

        lc = self.worldcover().rename("landcover")

        try:
            eai = self.economic_activity_index(year, month).rename("economic_index")
        except Exception:
            eai = ee.Image(0).rename("economic_index")

        composite = ee.Image.cat([
            nl, ndvi_img, ndbi_img, elev, slope, pop, lc, eai,
        ])

        result = composite.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=DEFAULT_SCALE,
        ).getInfo()

        # Map landcover code to name
        lc_code = result.get("landcover")
        if lc_code is not None:
            result["landcover_name"] = WORLDCOVER_CLASSES.get(int(lc_code), "Unknown")

        return result

    def sample_transect(self, year: int = 2023, month: int = 6) -> list[dict]:
        """
        Sample all data at the 13 corridor nodes.

        Returns a list of dicts, one per node.
        """
        results = []
        for node in CORRIDOR_NODES:
            data = self.sample_at_point(node["lon"], node["lat"], year, month)
            data["name"] = node["name"]
            data["lon"] = node["lon"]
            data["lat"] = node["lat"]
            results.append(data)
        return results

    def zone_stats(
        self,
        image: ee.Image,
        band: str | None = None,
        scale: int = DEFAULT_SCALE,
    ) -> dict[str, Any]:
        """
        Compute zonal statistics for an image over the corridor AOI.

        Returns: mean, max, min, sum, stdDev, count.
        """
        if band:
            image = image.select(band)

        stats = image.reduceRegion(
            reducer=ee.Reducer.mean()
            .combine(ee.Reducer.max(), sharedInputs=True)
            .combine(ee.Reducer.min(), sharedInputs=True)
            .combine(ee.Reducer.sum(), sharedInputs=True)
            .combine(ee.Reducer.stdDev(), sharedInputs=True)
            .combine(ee.Reducer.count(), sharedInputs=True),
            geometry=self._aoi,
            scale=scale,
            maxPixels=MAX_PIXELS,
        )
        return stats.getInfo()

    def zone_stats_by_country(
        self,
        image: ee.Image,
        band: str | None = None,
        scale: int = 1000,
    ) -> dict[str, dict]:
        """
        Compute zonal statistics grouped by country.

        Uses FAO GAUL admin boundaries.
        """
        if band:
            image = image.select(band)

        countries = (
            ee.FeatureCollection("FAO/GAUL/2015/level0")
            .filter(ee.Filter.inList("ADM0_CODE", [182, 27, 220, 89, 66]))
        )

        result = image.reduceRegions(
            collection=countries,
            reducer=ee.Reducer.mean().combine(ee.Reducer.sum(), sharedInputs=True),
            scale=scale,
        )

        features = result.getInfo()["features"]
        stats = {}
        for f in features:
            name = f["properties"].get("ADM0_NAME", "Unknown")
            stats[name] = {
                k: v for k, v in f["properties"].items()
                if k not in ("ADM0_CODE", "ADM0_NAME", "GAUL_CODE")
            }
        return stats

    # ── Tile URL Generation ──────────────────────────────────────────────────

    @staticmethod
    def get_tile_url(image: ee.Image, vis_params: dict) -> str:
        """
        Convert an ee.Image into a tile URL for Mapbox GL JS.

        Returns: https://earthengine.googleapis.com/v1/.../tiles/{z}/{x}/{y}
        """
        map_id = image.getMapId(vis_params)
        return map_id["tile_fetcher"].url_format

    def quick_map(self, image: ee.Image, layer_name: str) -> str:
        """Get tile URL using default vis params for a named layer."""
        vis = VIS_PARAMS.get(layer_name, {"min": 0, "max": 1})
        return self.get_tile_url(image, vis)

    # ── Export ───────────────────────────────────────────────────────────────

    def export_to_drive(
        self,
        image: ee.Image,
        description: str,
        folder: str = "corridor_exports",
        scale: int = 100,
        max_pixels: float = MAX_PIXELS,
    ) -> ee.batch.Task:
        """
        Export an ee.Image to Google Drive.

        Returns the started export task.
        """
        task = ee.batch.Export.image.toDrive(
            image=image,
            description=description,
            folder=folder,
            region=self._aoi,
            scale=scale,
            maxPixels=max_pixels,
        )
        task.start()
        logger.info("Export task started: %s", description)
        return task

    # ── Validation ───────────────────────────────────────────────────────────

    def validate_dataset(self, name: str, collection_id: str) -> dict:
        """
        Check if a GEE dataset is accessible and has data in the corridor.

        Returns: {"name": ..., "accessible": bool, "count": int, "error": str|None}
        """
        try:
            col = ee.ImageCollection(collection_id).filterBounds(self._aoi)
            count = col.size().getInfo()
            return {"name": name, "accessible": True, "count": count, "error": None}
        except Exception:
            # Try as single image
            try:
                img = ee.Image(collection_id)
                _ = img.bandNames().getInfo()
                return {"name": name, "accessible": True, "count": 1, "error": None}
            except Exception:
                # Try as FeatureCollection (e.g. Open Buildings)
                try:
                    fc = ee.FeatureCollection(collection_id).filterBounds(self._aoi).limit(10)
                    count = fc.size().getInfo()
                    return {"name": name, "accessible": True, "count": count, "error": None}
                except Exception as exc:
                    return {"name": name, "accessible": False, "count": 0, "error": str(exc)}
