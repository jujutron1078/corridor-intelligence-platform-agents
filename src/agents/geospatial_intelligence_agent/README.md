# Geospatial Intelligence Agent

This agent provides geographic and spatial analysis for corridor planning. It geocodes locations, defines corridor boundaries, fetches and processes geospatial layers, analyzes terrain, detects infrastructure and anchor loads from imagery, and runs route optimization subject to terrain and environmental constraints.

---

## Shared Tools (Platform-Wide)

All agents use these common tools:

| Tool | Purpose |
|------|--------|
| `think_tool` | Step-by-step reasoning and assumptions tracking. |
| `write_todos` | Structured task list for multi-step workflows. |

---

## Domain Tools

## 1) `geocode_location`

Converts place names into geographic coordinates.

### Input contract (exact)

| Field | Type | Required | Description |
|---|---|---|---|
| `locations` | `List[object]` | Yes | Locations to geocode. |
| `locations[].name` | `str` | Yes | Place name. |
| `locations[].country` | `str` | Yes | Country name. |

Example input:

```json
{
  "locations": [
    { "name": "Abidjan", "country": "Cote d'Ivoire" },
    { "name": "Lagos", "country": "Nigeria" }
  ]
}
```

### Output structure

Top-level keys:

- `resolved_locations` (`List[object]`)

Per `resolved_locations[]`:

- `input_name` (`str`)
- `latitude` (`float`)
- `longitude` (`float`)
- `confidence` (`float`, 0-1)

Example output shape:

```json
{
  "resolved_locations": [
    {
      "input_name": "Abidjan",
      "latitude": 5.359951,
      "longitude": -4.008256,
      "confidence": 0.97
    },
    {
      "input_name": "Lagos",
      "latitude": 6.524379,
      "longitude": 3.379206,
      "confidence": 0.96
    }
  ]
}
```

---

## 2) `define_corridor`

Creates a corridor polygon between source and destination coordinates.

### Input contract (exact)

| Field | Type | Required | Description |
|---|---|---|---|
| `source` | `object` | Yes | Source coordinate. |
| `source.latitude` | `float` | Yes | Source latitude. |
| `source.longitude` | `float` | Yes | Source longitude. |
| `destination` | `object` | Yes | Destination coordinate. |
| `destination.latitude` | `float` | Yes | Destination latitude. |
| `destination.longitude` | `float` | Yes | Destination longitude. |
| `buffer_width_km` | `float` | Yes | Total corridor width in km. |

Example input:

```json
{
  "source": { "latitude": 5.36, "longitude": -4.01 },
  "destination": { "latitude": 6.52, "longitude": 3.38 },
  "buffer_width_km": 50
}
```

### Output structure

Top-level keys:

- `corridor_id` (`str`)
- `length_km` (`float`)
- `area_sqkm` (`float`)
- `bounding_polygon_geojson` (`object`)
- `status` (`str`)
- `message` (`str`)

`bounding_polygon_geojson` shape:

- `type` (`"Feature"`)
- `geometry.type` (`"Polygon"`)
- `geometry.coordinates` (`List[List[List[float]]]`, GeoJSON `[lon, lat]`)
- `properties.buffer_km` (`float`)
- `properties.corridor_id` (`str`)
- `properties.description` (`str`)

---

## 3) `fetch_geospatial_layers`

Fetches/clips corridor layers and returns analysis-ready URIs plus inventory metadata.

### Input contract (exact)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `corridor_id` | `str` | Yes | - | Corridor ID from `define_corridor`. |
| `layers_requested` | `List[str]` | No | `["satellite", "dem", "land_use", "protected_areas"]` | Layer types to fetch and clip. |
| `resolution_meters` | `int` | No | `10` | Raster resolution target. |

Example input:

```json
{
  "corridor_id": "AL_CORRIDOR_POC_001",
  "layers_requested": ["satellite", "dem", "land_use", "protected_areas"],
  "resolution_meters": 10
}
```

### Output structure

Top-level keys:

- `corridor_id` (`str`)
- `status` (`str`)
- `data_inventory` (`object`)
- `uris` (`object`)
- `metadata` (`object`)

`data_inventory`:

- `layers_requested` (`List[str]`)
- `raster_layers.satellite` (`object`)
- `raster_layers.dem` (`object`)
- `raster_layers.land_use` (`object`)
- `vector_layers.protected_areas` (`object`)
- `vector_layers.administrative_boundaries` (`object`)
- `vector_layers.osm_infrastructure` (`object`)

`uris`:

- `satellite_raster_uri` (`str`)
- `dem_raster_uri` (`str`)
- `land_use_raster_uri` (`str`)
- `protected_areas_vector_uri` (`str`)
- `admin_boundaries_vector_uri` (`str`)
- `osm_infrastructure_uri` (`str`)
- `composite_preview_uri` (`str`)

`metadata`:

- `crs` (`str`)
- `corridor_bounding_box` (`object`)
- `corridor_length_km` (`float`)
- `buffer_each_side_km` (`float`)
- `clip_area_sqkm` (`float`)
- `processing_level` (`str`)
- `projection_used_for_area_calc` (`str`)
- `generated_at` (`str`, ISO timestamp)
- `processing_time_seconds` (`int`)
- `platform_version` (`str`)
- `data_quality_flags` (`object`)
- `downstream_tools_ready` (`List[str]`)

---

## 4) `terrain_analysis`

Computes terrain metrics from DEM and provides segment-level buildability outputs.

### Input contract (exact)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `corridor_id` | `str` | Yes | - | Corridor ID. |
| `dem_uri` | `str` | Yes | - | DEM URI/path. |
| `resolution_meters` | `int` | No | `30` | Analysis resolution. |
| `analysis_targets` | `List[str]` | No | `["slope", "flood_risk", "soil_stability"]` | Metrics to compute. |
| `sampling_interval_km` | `float` | No | `5.0` | Along-corridor sampling interval. |

Example input:

```json
{
  "corridor_id": "AL_CORRIDOR_POC_001",
  "dem_uri": "s3://corridor-platform/data/.../dem/srtm_gl1_void_filled_30m.tif",
  "resolution_meters": 30,
  "analysis_targets": ["slope", "flood_risk", "soil_stability"],
  "sampling_interval_km": 5.0
}
```

### Output structure

Top-level keys:

- `analysis_metadata` (`object`)
- `segment_analysis` (`List[object]`)
- `corridor_summary` (`object`)
- `engineering_recommendations` (`List[object]`)
- `no_go_zones` (`List[object]`)

`analysis_metadata`:

- `tool_name`, `corridor_id`, `dem_source`, `analysis_date`, `crs`
- `total_corridor_length_km`, `buffer_width_km`, `segments_analyzed`, `confidence_score`

Per `segment_analysis[]`:

- `segment_id`, `label`, `country`
- `start_km`, `end_km`
- `start_coordinate`, `end_coordinate`
- `terrain_profile`
- `slope_analysis`
- `soil_stability`
- `flood_risk`
- `construction_difficulty`
- `co_location_opportunity`

`corridor_summary` includes aggregate difficulty/flood/earthworks/co-location totals.

`engineering_recommendations[]` shape:

- `priority` (`str`)
- `segment` (`str`)
- `recommendation` (`str`)

`no_go_zones[]` shape:

- `zone_id`, `description`, `coordinates`, `radius_km`, `reason`

---

## 5) `infrastructure_detection`

Runs CV inference on corridor imagery to detect visible infrastructure.

### Input contract (exact)

| Field | Type | Required | Description |
|---|---|---|---|
| `satellite_image_uri` | `str` | Yes | Satellite raster URI/path. |
| `types` | `List[Literal]` | Yes | Detection types: `thermal_power_plant`, `oil_refinery`, `port_facility`, `special_economic_zone`, `industrial_complex`, `substation`, `mining_operation`. |

Example input:

```json
{
  "satellite_image_uri": "s3://corridor-platform/data/.../satellite/sentinel2_median_2025H2_10m.tif",
  "types": ["thermal_power_plant", "port_facility", "industrial_complex"]
}
```

### Output structure

Top-level keys:

- `job_metadata` (`object`)
- `detections` (`List[object]`)
- `summary` (`object`)
- `output_uris` (`object`)

`job_metadata` includes:

- `tool`, `corridor_id`, `corridor_boundary`, `source_raster`
- `model` (name/backbone/training/tile settings)
- `detection_thresholds`
- `generated_at`

Per `detections[]`:

- `detection_id` (`str`)
- `type` (`str`)
- `subtype` (`str`)
- `matched_known_asset` (`bool`)
- `coordinates` (`object`)
- `bounding_box` (`object`)
- `confidence` (`float`)
- `verification_status` (`str`)
- `review_reason` (`str`, only when manual review is required)
- `facility_attributes` (`object`)
- `change_detection` (`object`)
- `is_anchor_load` (`bool`)
- `is_generation_asset` (`bool`)
- `is_road_safety_risk` (`bool`)
- `risk_severity` (`str | null`) values observed: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`

`summary` includes:
- `total_detections`, `detections_shown_in_sample`
- `auto_verified`, `manual_review_required`, `new_since_last_census`
- `outside_corridor_boundary_excluded`
- `by_type` (`object`)
- `anchor_loads_identified` (`object`)
- `generation_assets_identified`
- `road_safety_hazards_identified` (`object`) with:
  - `total`
  - `by_severity` (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`)
  - `by_subtype`
  - `by_country`
  - `critical_hazards_requiring_immediate_design_response` (`List[str]`)
  - `note`
- `notable_new_discoveries` (`List[str]`)
- `note` (`str`)

`output_uris`:

- `detections_geojson`
- `bounding_boxes_overlay`
- `manual_review_tiles`
- `anchor_load_list_geojson`
- `generation_assets_geojson`
- `road_safety_hazards_geojson`
- `road_safety_heatmap_raster`
- `critical_hazards_geojson`

---

## 6) `environmental_constraints`

Identifies legal, environmental, and human safety constraints for the corridor.

### Input contract (exact)

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `corridor_id` | `str` | Yes | - | Corridor ID. |
| `vector_uri` | `str` | Yes | - | Protected areas GeoJSON URI/path. |
| `constraint_types` | `List[str]` | No | `["national_parks", "wetlands", "cultural_sites", "forest_reserves"]` | Constraint classes to check. |
| `buffer_zone_meters` | `int` | No | `500` | Clearance buffer around constrained zones. |

Example input:

```json
{
  "corridor_id": "AL_CORRIDOR_POC_001",
  "vector_uri": "s3://corridor-platform/data/.../vectors/wdpa_protected_areas.geojson",
  "constraint_types": ["national_parks", "wetlands", "cultural_sites", "forest_reserves"],
  "buffer_zone_meters": 500
}
```

### Output structure

Top-level keys:

- `audit_metadata` (`object`)
- `status` (`str`)
- `overall_risk_rating` (`str`)
- `requires_esia` (`bool`)
- `esia_category` (`str`)
- `esia_rationale` (`str`)
- `protected_area_conflicts` (`List[object]`)
- `wetland_and_water_body_conflicts` (`List[object]`)
- `cultural_heritage_conflicts` (`List[object]`)
- `human_safety_conflicts` (`List[object]`)
- `no_go_zones` (`List[object]`)
- `aggregate_impact` (`object`)
- `recommended_next_steps` (`List[str]`)
- `output_uris` (`object`)

`audit_metadata` includes:

- `tool`, `corridor_id`
- `source_layers` (now includes environmental and safety sources such as `road_safety_detections`, `osm_points_of_interest`, `population_density`)
- `buffer_applied_m` (object with `environmental` and `human_safety`)
- `standards_applied` (environmental and road/community safety standards)
- `generated_at`, `total_corridor_area_sqkm`

`protected_area_conflicts[]` includes:

- `conflict_id`, `name`, `country`, `iucn_category`, `wdpa_id`
- `risk_level`, `legal_basis`, `conflict_type`
- `overlap_with_corridor_buffer_sqkm`, `overlap_pct_of_protected_area`
- `centroid`, `recommended_action`, `detour_cost_estimate_usd`
- `permitting_outlook`, `notes`

`wetland_and_water_body_conflicts[]` includes:

- `conflict_id`, `name`, `country`, `designation`, `risk_level`, `conflict_type`
- `overlap_sqkm`, `recommended_action`, `permitting_outlook`, `notes`

`cultural_heritage_conflicts[]` includes:

- `conflict_id`, `name`, `country`, `designation`, `risk_level`, `conflict_type`
- `distance_to_heritage_boundary_m`, `recommended_action`, `permitting_outlook`, `notes`

`human_safety_conflicts[]` includes:

- `conflict_id`, `source_detection`, `name`, `country`, `subtype`
- `risk_level`, `legal_basis`, `conflict_type`
- `coordinates`, `buffer_zone_m`, `affected_road_length_m`
- `key_hazard_indicators` (`object`)
- `estimated_affected_population`
- `recommended_action`
- `required_mitigation` (`List[str]`)
- `mitigation_capex_estimated_usd`
- `permitting_outlook`
- `dfI_financing_impact`
- `notes`

`no_go_zones[]` now combines categories:

- Environmental zones with `category: "environmental"` and classic no-go classification
- Safety zones with `category: "human_safety"` plus:
  - `source_conflict`
  - `source_detection`
  - `classification` (e.g. `DESIGN INTERVENTION REQUIRED`)
- Map tooltip payload:
  - `tooltip.title`
  - `tooltip.severity`
  - `tooltip.summary`
  - `tooltip.action`
  - `tooltip.source_conflict`

Tooltip recommendation for UI:

- Use `tooltip.title` as header.
- Show `tooltip.summary` and `reason` together for context.
- Highlight `tooltip.action` as the required intervention.
- Add badge color by `classification` / `tooltip.severity`.

`aggregate_impact` now includes:

- Environmental totals (`total_protected_area_conflicts`, `total_wetland_conflicts`, etc.)
- Safety totals (`total_human_safety_conflicts`, `human_safety_conflicts_by_severity`, `total_human_safety_mitigation_capex_usd`, `total_estimated_population_in_conflict_zones`, etc.)
- Combined totals (`total_all_conflicts`, `total_combined_mitigation_capex_usd`, `esg_risk_rating_for_dfi_financing`)
- Expanded permitting and financing risk fields

`recommended_next_steps` now includes both:

- Environmental actions (re-routes, Ramsar, ESIA, agency engagement)
- Human safety actions (RSAP, immediate controls, authority coordination, safety no-go submission to routing)

`output_uris`:

- `constraints_geojson`
- `no_go_zones_geojson` (combined environmental + human safety zones)
- `environmental_no_go_zones_geojson` (environment-only subset)
- `conflict_report_pdf`
- `esia_scope_checklist`
- `human_safety_conflicts_geojson`
- `safety_no_go_zones_geojson`
- `road_safety_action_plan_template`
- `esmp_safety_chapter`
- `combined_no_go_zones_geojson`

---

## 7) `route_optimization`

Builds and ranks route variants from terrain, environment, and detections.

### Input contract (exact)

Important: in current implementation, this tool only takes one direct argument; other inputs are consumed from prior tool outputs in agent context.

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `priority` | `Literal["min_cost", "min_distance", "max_impact", "balance"]` | No | `"balance"` | Optimization objective. |

Example input:

```json
{
  "priority": "balance"
}
```

### Output structure

Top-level keys:

- `job_metadata` (`object`)
- `cost_weight_matrix` (`object`)
- `optimized_routes` (`List[object]`)
- `recommended_route` (`object`)
- `phasing_recommendation` (`object`)
- `variants_eliminated` (`object`)
- `output_uris` (`object`)

`job_metadata` includes:

- algorithm details, consumed input URIs, grid dimensions, variants generated, timing

Per `optimized_routes[]`:

- `variant_id`, `rank`, `label`, `description`
- `total_length_km`, `vs_straight_line_overhead_pct`, `composite_score`
- `coordinates` (polyline point list)
- `route_geojson` (GeoJSON LineString)
- `scoring_breakdown`
- `segments` (optional detailed segment list)
- `totals`
- `financial_indicators`
- `key_tradeoff` (optional)

`recommended_route`:

- `variant_id`
- `rationale`
- `conditions` (`List[str]`)

`phasing_recommendation`:

- `phase_1`, `phase_2`, `phase_3`
- each phase has `segments`, `rationale`, `combined_length_km`, `combined_net_capex_usd`, revenue fields

`variants_eliminated`:

- `total_eliminated`
- `reasons` (counts by elimination cause)

`output_uris`:

- `all_routes_geojson`
- `top5_routes_geojson`
- `recommended_route_geojson`
- `cost_grid_raster`
- `phasing_map_geojson`
- `comparison_report_csv`

---

## Typical Sequence

1. `geocode_location`
2. `define_corridor`
3. `fetch_geospatial_layers`
4. `terrain_analysis`
5. `environmental_constraints`
6. `infrastructure_detection`
7. `route_optimization`

---

## Notes On Contracts

- Input tables above reflect the current Pydantic schemas in `src/agents/geospatial_intelligence_agent/tools/*/schema.py`.
- Output structures above reflect the current tool return payload shapes in `src/agents/geospatial_intelligence_agent/tools/*/tool.py`.
- Many outputs are currently mocked but structurally representative and safe for downstream contract integration.
