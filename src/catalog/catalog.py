"""
Unified data source registry for the Corridor Intelligence Platform.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("corridor.catalog")


class SourceType(str, Enum):
    GEE = "gee"
    OSM = "osm"
    USGS = "usgs"
    API = "api"
    MANUAL = "manual"


class ValidationStatus(str, Enum):
    VALIDATED = "validated"
    PARTIAL = "partial"
    MISSING = "missing"
    MANUAL = "manual"
    UNKNOWN = "unknown"


@dataclass
class DataSource:
    """Registry entry for a single data source."""

    name: str
    source_type: SourceType
    url: str
    description: str
    coverage: str
    resolution: str
    temporal_range: str
    status: ValidationStatus = ValidationStatus.UNKNOWN
    notes: str = ""
    tier: int = 1
    collection_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source_type": self.source_type.value,
            "url": self.url,
            "description": self.description,
            "coverage": self.coverage,
            "resolution": self.resolution,
            "temporal_range": self.temporal_range,
            "status": self.status.value,
            "notes": self.notes,
            "tier": self.tier,
            "collection_id": self.collection_id,
        }


# ── Full data catalog ────────────────────────────────────────────────────────

DATA_SOURCES: list[DataSource] = [
    # ── GEE Tier 1 ───────────────────────────────────────────────────────────
    DataSource(
        name="Sentinel-2 L2A",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED",
        description="Multi-spectral surface reflectance. Compute NDVI, NDBI, MNDWI.",
        coverage="Lagos-Abidjan corridor (50km buffer)",
        resolution="10m",
        temporal_range="2015-2024 (monthly composites)",
        tier=1,
        collection_id="COPERNICUS/S2_SR_HARMONIZED",
    ),
    DataSource(
        name="VIIRS Nightlights",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/NOAA_VIIRS_DNB_MONTHLY_V1_VCMSLCFG",
        description="Monthly nighttime radiance. Primary economic activity proxy.",
        coverage="Lagos-Abidjan corridor (50km buffer)",
        resolution="500m",
        temporal_range="2012-2024 (monthly)",
        tier=1,
        collection_id="NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG",
    ),
    DataSource(
        name="ESA WorldCover",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v200",
        description="Global 10m land cover classification (2021).",
        coverage="Global",
        resolution="10m",
        temporal_range="2021 (static)",
        tier=1,
        collection_id="ESA/WorldCover/v200",
    ),
    DataSource(
        name="Dynamic World",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1",
        description="Near-real-time land cover from Sentinel-2. Used for urban expansion detection.",
        coverage="Global",
        resolution="10m",
        temporal_range="2016-2024 (monthly mode)",
        tier=1,
        collection_id="GOOGLE/DYNAMICWORLD/V1",
    ),
    DataSource(
        name="SRTM Elevation",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/USGS_SRTMGL1_003",
        description="Digital elevation model. Derive slope and aspect.",
        coverage="Global (60°N-56°S)",
        resolution="30m",
        temporal_range="Static",
        tier=1,
        collection_id="USGS/SRTMGL1_003",
    ),
    DataSource(
        name="WorldPop",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/WorldPop_GP_100m_pop",
        description="Gridded population estimates.",
        coverage="Global",
        resolution="100m",
        temporal_range="2000-2020 (annual)",
        tier=1,
        collection_id="WorldPop/GP/100m/pop",
        notes="Stops at 2020. Use GHSL + Open Buildings as proxy for later years.",
    ),
    DataSource(
        name="JRC Surface Water",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_GlobalSurfaceWater",
        description="35-year summary of surface water occurrence, seasonality, change.",
        coverage="Global",
        resolution="30m",
        temporal_range="Static (1984-2021 summary)",
        tier=1,
        collection_id="JRC/GSW1_4/GlobalSurfaceWater",
    ),
    DataSource(
        name="Hansen Forest Change",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2023_v1_11",
        description="Global forest loss, gain, and tree cover (2000-2023).",
        coverage="Global",
        resolution="30m",
        temporal_range="Static (annual loss encoded 2001-2023)",
        tier=1,
        collection_id="UMD/hansen/global_forest_change_2023_v1_11",
    ),

    # ── GEE Tier 2 ───────────────────────────────────────────────────────────
    DataSource(
        name="Copernicus DEM",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_DEM_GLO30",
        description="Copernicus 30m global DEM.",
        coverage="Global",
        resolution="30m",
        temporal_range="Static",
        tier=2,
        collection_id="COPERNICUS/DEM/GLO30",
    ),
    DataSource(
        name="GHSL Built-Up",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S",
        description="Built-up surface area across multiple epochs (1975-2020).",
        coverage="Global",
        resolution="100m",
        temporal_range="Multi-epoch: 1975, 1990, 2000, 2015, 2020",
        tier=2,
        collection_id="JRC/GHSL/P2023A/GHS_BUILT_S",
    ),
    DataSource(
        name="Google Open Buildings",
        source_type=SourceType.GEE,
        url="https://sites.research.google/open-buildings/",
        description="Individual building footprints from satellite imagery. Rasterized to 1km density grid.",
        coverage="Africa, South/Southeast Asia",
        resolution="Building-level (rasterized to 1km)",
        temporal_range="Static",
        tier=2,
        collection_id="GOOGLE/Research/open-buildings/v3/polygons",
    ),
    DataSource(
        name="Sentinel-1 SAR",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD",
        description="C-band SAR radar imagery. All-weather observation. VV/VH bands.",
        coverage="Global",
        resolution="10m",
        temporal_range="2015-2024 (monthly composites)",
        tier=2,
        collection_id="COPERNICUS/S1_GRD",
        notes="Workaround for Sentinel-2 cloud cover during wet season (May-October).",
    ),
    DataSource(
        name="ERA5-Land Climate",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_MONTHLY_AGGR",
        description="Monthly temperature, precipitation, wind speed from reanalysis.",
        coverage="Global",
        resolution="~11km",
        temporal_range="2015-2024 (monthly)",
        tier=2,
        collection_id="ECMWF/ERA5_LAND/MONTHLY_AGGR",
    ),

    # ── GEE Tier 2 (New) ─────────────────────────────────────────────────────
    DataSource(
        name="WDPA Protected Areas",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/WCMC_WDPA_current_polygons",
        description="World Database on Protected Areas — national parks, nature reserves, wildlife sanctuaries.",
        coverage="Global (filtered to corridor AOI)",
        resolution="Vector (polygons)",
        temporal_range="Static (updated regularly)",
        tier=2,
        collection_id="WCMC/WDPA/current/polygons",
    ),
    DataSource(
        name="Oxford/MAP Healthcare Accessibility",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/Oxford_MAP_accessibility_to_healthcare_2019",
        description="Travel time to nearest healthcare facility in minutes. Identifies health coverage gaps.",
        coverage="Global",
        resolution="1km",
        temporal_range="2019 (static)",
        tier=2,
        collection_id="projects/malariaatlasproject/assets/accessibility/accessibility_to_healthcare/2019",
    ),

    # ── OSM ──────────────────────────────────────────────────────────────────
    DataSource(
        name="OSM Road Network",
        source_type=SourceType.OSM,
        url="https://overpass-api.de/",
        description="Full road network classified into 4 quality tiers. NetworkX graph with connectivity analysis.",
        coverage="Lagos-Abidjan corridor bounding box",
        resolution="Vector (individual road segments)",
        temporal_range="Current (live)",
        notes="Secondary roads patchy in Benin/Togo. Supplement with GRIP + USGS roads.",
    ),
    DataSource(
        name="OSM Infrastructure",
        source_type=SourceType.OSM,
        url="https://overpass-api.de/",
        description="Ports, airports, rail, border crossings, industrial zones, SEZs, key POIs.",
        coverage="Lagos-Abidjan corridor bounding box",
        resolution="Vector",
        temporal_range="Current (live)",
    ),

    # ── USGS ─────────────────────────────────────────────────────────────────
    DataSource(
        name="USGS Africa Minerals",
        source_type=SourceType.USGS,
        url="https://doi.org/10.5066/P97EQWXP",
        description="Mineral facilities, exploration sites, deposits, power plants, pipelines, ports, roads.",
        coverage="Africa (filtered to corridor AOI)",
        resolution="Vector (point/line features)",
        temporal_range="Static (published 2021)",
    ),

    # ── API ──────────────────────────────────────────────────────────────────
    DataSource(
        name="UN Comtrade",
        source_type=SourceType.API,
        url="https://comtradeapi.un.org/",
        description="Bilateral trade flows for corridor countries. Key commodities: cocoa, gold, bauxite, oil, rubber, timber.",
        coverage="5 corridor countries (NGA, BEN, TGO, GHA, CIV)",
        resolution="Country-level annual/monthly",
        temporal_range="2015-2023",
    ),
    DataSource(
        name="ACLED Conflict Data",
        source_type=SourceType.API,
        url="https://api.acleddata.com/",
        description="Geocoded political violence and protest events. Includes battles, protests, riots, violence against civilians.",
        coverage="5 corridor countries (filtered to AOI bbox)",
        resolution="Event-level (geocoded points)",
        temporal_range="2020-2024",
        notes="Requires free research API key. Register at developer.acleddata.com.",
    ),
    DataSource(
        name="World Bank Open Data",
        source_type=SourceType.API,
        url="https://api.worldbank.org/v2/",
        description="Economic indicators: GDP, FDI, trade %, remittances, ease of business, inflation, electricity access, internet users.",
        coverage="5 corridor countries (NGA, BEN, TGO, GHA, CIV)",
        resolution="Country-level annual",
        temporal_range="2010-2024",
        notes="No API key required. 13 indicators configured.",
    ),
    DataSource(
        name="World Bank Pink Sheet",
        source_type=SourceType.API,
        url="https://www.worldbank.org/en/research/commodity-markets",
        description="Monthly commodity prices. Raw vs. refined price differentials.",
        coverage="Global commodities",
        resolution="Monthly time-series",
        temporal_range="1960-present",
    ),

    # ── Download Datasets ──────────────────────────────────────────────────
    DataSource(
        name="FAO Gridded Livestock (GLW 3)",
        source_type=SourceType.API,
        url="https://dataverse.harvard.edu/dataverse/glw_3",
        description="Gridded livestock density at ~10km resolution: cattle, goats, sheep, chickens, pigs.",
        coverage="Global (clipped to corridor AOI)",
        resolution="~10km",
        temporal_range="2010 (static)",
        notes="GeoTIFF download from Harvard Dataverse. Requires rasterio for processing.",
    ),
    DataSource(
        name="Ookla Speedtest Open Data",
        source_type=SourceType.API,
        url="https://github.com/teamookla/ookla-open-data",
        description="Internet speed and coverage data at ~610m resolution. Mobile and fixed networks.",
        coverage="Global (filtered to corridor AOI)",
        resolution="~610m (H3 tiles)",
        temporal_range="Quarterly (2019-2024)",
        notes="Parquet format. Requires pyarrow for processing. Large files (~2GB each).",
    ),
    DataSource(
        name="HDX Health Facilities",
        source_type=SourceType.API,
        url="https://healthsites.io/",
        description="Geocoded health facilities from healthsites.io. Hospitals, clinics, pharmacies.",
        coverage="5 corridor countries",
        resolution="Point features",
        temporal_range="Current (live API)",
        notes="Free API, no key needed. Supplements OSM health data.",
    ),
    DataSource(
        name="Global Power Plant Database",
        source_type=SourceType.API,
        url="https://datasets.wri.org/dataset/globalpowerplantdatabase",
        description="Power plants worldwide with capacity, fuel type, owner. From WRI / Global Energy Monitor.",
        coverage="5 corridor countries (filtered from global)",
        resolution="Point features",
        temporal_range="Static (published 2021)",
        notes="CSV download, no API key required.",
    ),

    # ── Manual ───────────────────────────────────────────────────────────────
    DataSource(
        name="Policy Documents",
        source_type=SourceType.MANUAL,
        url="",
        description="National trade policies, ECOWAS agreements, corridor development plans.",
        coverage="5 corridor countries",
        resolution="Document-level",
        temporal_range="Various",
        status=ValidationStatus.MANUAL,
        notes="Requires manual PDF collection. Not automated in pipeline.",
    ),
    DataSource(
        name="Mapillary Street Imagery",
        source_type=SourceType.MANUAL,
        url="https://www.mapillary.com/",
        description="Street-level imagery for visual corridor assessment.",
        coverage="Sparse — mainly Lagos, Accra, Abidjan",
        resolution="Image-level",
        temporal_range="Various",
        status=ValidationStatus.PARTIAL,
        notes="Sparse outside major cities. Use satellite + Claude Vision for rural areas.",
    ),

    # ── GEE Tier 2 (Enrichment) ─────────────────────────────────────────────
    DataSource(
        name="Global Flood Database",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/GLOBAL_FLOOD_DB_MODIS_EVENTS_V1",
        description="Historical flood events from MODIS satellite imagery. Flood extent, duration, and affected areas.",
        coverage="Global (filtered to corridor AOI)",
        resolution="250m",
        temporal_range="2000-2018 (historical events)",
        tier=2,
        collection_id="GLOBAL_FLOOD_DB/MODIS_EVENTS/V1",
    ),
    DataSource(
        name="iSDAsoil Africa",
        source_type=SourceType.GEE,
        url="https://developers.google.com/earth-engine/datasets/catalog/ISDASOIL_Africa_v1_clay_content",
        description="Soil properties for Africa: clay content, pH, sand content, bulk density, organic carbon, nitrogen. Critical for construction feasibility.",
        coverage="Africa",
        resolution="30m",
        temporal_range="Static",
        tier=2,
        collection_id="ISDASOIL/Africa/v1/clay_content",
        notes="Multiple collections for different soil properties. 30m resolution for Africa only.",
    ),

    # ── New API Pipelines ──────────────────────────────────────────────────────
    DataSource(
        name="IMF World Economic Outlook",
        source_type=SourceType.API,
        url="https://www.imf.org/external/datamapper/api/v1",
        description="GDP growth forecasts, inflation, current account, government debt, unemployment from IMF WEO.",
        coverage="5 corridor countries (NGA, BEN, TGO, GHA, CIV)",
        resolution="Country-level annual",
        temporal_range="2010-2029 (includes forecasts)",
        notes="Public API, no key required. Complements World Bank with forward-looking forecasts.",
    ),
    DataSource(
        name="Transparency International CPI",
        source_type=SourceType.API,
        url="https://www.transparency.org/cpi",
        description="Corruption Perceptions Index. Scale 0-100 (higher = less corrupt). Key for sovereign risk assessment.",
        coverage="5 corridor countries",
        resolution="Country-level annual",
        temporal_range="2012-2024",
        notes="Reference data fallback included for offline use.",
    ),
    DataSource(
        name="V-Dem Governance Indicators",
        source_type=SourceType.API,
        url="https://v-dem.net/",
        description="Electoral democracy, liberal democracy, rule of law, corruption, civil liberties indices (0-1 scale).",
        coverage="5 corridor countries",
        resolution="Country-level annual",
        temporal_range="1900-2024 (reference data subset)",
        notes="Reference data approach. Full dataset requires bulk CSV download.",
    ),
    DataSource(
        name="Global Data Lab Sub-national HDI",
        source_type=SourceType.API,
        url="https://globaldatalab.org/shdi/",
        description="Sub-national Human Development Index: education, income, health indices at district/region level.",
        coverage="13+ corridor regions across 5 countries",
        resolution="Admin Level 1 (region/state)",
        temporal_range="2010-2022",
        notes="Public API. Enables sub-national poverty/development analysis.",
    ),
    DataSource(
        name="AidData Development Finance",
        source_type=SourceType.API,
        url="https://www.aiddata.org/",
        description="Georeferenced international development finance: AfDB, World Bank, IFC, EU, bilateral donors.",
        coverage="5 corridor countries",
        resolution="Project-level (geocoded points)",
        temporal_range="2000-2024",
        notes="Reference data with 27 corridor-relevant projects. Bulk data requires registration.",
    ),
    DataSource(
        name="Global Energy Monitor",
        source_type=SourceType.API,
        url="https://globalenergymonitor.org/",
        description="Planned, announced, and under-construction power plants: solar, wind, gas, hydro, battery storage.",
        coverage="5 corridor countries",
        resolution="Project-level (geocoded points)",
        temporal_range="Current pipeline (2024-2030+)",
        notes="Reference data with 23 planned projects. Complements GPPD with forward-looking pipeline.",
    ),
    DataSource(
        name="FAO FAOSTAT Agricultural Production",
        source_type=SourceType.API,
        url="https://fenixservices.fao.org/faostat/api/v1/",
        description="Agricultural production: cocoa, palm oil, cashew, rubber, yams, cassava, maize, rice. Tonnes, hectares, yield.",
        coverage="5 corridor countries",
        resolution="Country-level annual",
        temporal_range="2010-2023",
        notes="Public API, no key required. 8 key corridor commodities configured.",
    ),
    DataSource(
        name="UNCTAD Port Statistics",
        source_type=SourceType.API,
        url="https://unctadstat.unctad.org/",
        description="Port throughput (TEU), cargo volumes, vessel calls, dwell times for 9 corridor ports.",
        coverage="9 corridor ports (Lagos, Cotonou, Lom\u00e9, Tema, Takoradi, Abidjan, etc.)",
        resolution="Port-level annual",
        temporal_range="2018-2024",
        notes="Reference data approach. Key anchor load demand input.",
    ),
    DataSource(
        name="energydata.info Transmission Grid",
        source_type=SourceType.API,
        url="https://energydata.info/",
        description="Existing transmission lines (33-330kV), substations, and grid infrastructure from World Bank ESMAP.",
        coverage="5 corridor countries",
        resolution="Line/point features",
        temporal_range="Current (updated periodically)",
        notes="CKAN API with reference data fallback. 20 transmission lines, 15 substations.",
    ),
    DataSource(
        name="IFC PPI Database",
        source_type=SourceType.API,
        url="https://ppi.worldbank.org/",
        description="Past PPP/PFI projects: energy, transport, telecoms, water. Investment amounts, contract types, DFI support.",
        coverage="5 corridor countries",
        resolution="Project-level",
        temporal_range="1990-2024",
        notes="Reference data with 20 PPP projects. Key input for financing agent DFI matching.",
    ),
    DataSource(
        name="WAPP Master Plan",
        source_type=SourceType.MANUAL,
        url="https://www.ecowapp.org/",
        description="West African Power Pool interconnections, generation targets, cross-border trade volumes.",
        coverage="ECOWAS region (focused on 5 corridor countries)",
        resolution="Line/country-level",
        temporal_range="2024-2033 (master plan horizon)",
        status=ValidationStatus.MANUAL,
        notes="Hardcoded reference data from WAPP publications. 12 interconnections, generation targets, trade volumes.",
    ),
    DataSource(
        name="GADM Administrative Boundaries",
        source_type=SourceType.API,
        url="https://gadm.org/",
        description="Admin Level 1 boundaries for zonal statistics aggregation. States, regions, departments.",
        coverage="5 corridor countries",
        resolution="Vector (admin polygons)",
        temporal_range="Static (v4.1)",
        notes="GeoJSON download. Enables sub-national aggregation of all raster/point data.",
    ),
]


def get_catalog() -> list[DataSource]:
    """Return the full data catalog."""
    return DATA_SOURCES


def get_catalog_by_type(source_type: SourceType) -> list[DataSource]:
    """Filter catalog by source type."""
    return [ds for ds in DATA_SOURCES if ds.source_type == source_type]


def get_catalog_by_tier(tier: int) -> list[DataSource]:
    """Filter catalog by tier (1 or 2)."""
    return [ds for ds in DATA_SOURCES if ds.tier == tier]
