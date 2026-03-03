# Infrastructure Optimization Agent

This agent optimizes the technical and economic design of corridor infrastructure. It refines routes from the Geospatial agent into engineering alignments, quantifies colocation benefits, sizes voltage and capacity, optimizes substation placement, generates phasing strategies, and produces CAPEX/OPEX cost estimates.

---

## Shared Tools (Platform-Wide)

All agents use these common tools:

| Tool | Purpose |
|------|--------|
| **think_tool** | Step-by-step reasoning and documentation of assumptions. |
| **write_todos** | Structured task list for multi-step workflows. |

---

## Domain Tools

### 1. `refine_optimized_routes`

**What it does:** Calculates **least-cost paths within specific corridor proximity constraints**. It refines the broad paths from the Geospatial agent into precise engineering routes that stay within the legal highway right-of-way (or other corridor envelope).

**When to use:** When you have candidate routes from Geospatial and need alignment refined to respect RoW, colocation rules, or regulatory limits.

**Key concepts:** Right-of-way (RoW), colocation corridor, engineering alignment vs strategic path.

**Input**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `geospatial_variants` | `List[Dict]` | Yes | — | Route variants from the Geospatial agent. Each variant typically includes geometry (coordinates or GeoJSON), length_km, and any cost or constraint metadata. |
| `corridor_proximity_limit_m` | `float` | No | `500.0` | Maximum allowed distance (metres) from the highway centreline. Routes are refined to stay within this envelope. |

**Output**

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | e.g. `"Route Refinement Complete"`. |
| `job_metadata` | `Dict` | `tool`, `corridor_id`, `corridor_proximity_limit_m`, `input_variants_received`, `variants_successfully_refined`, `refinement_resolution_m`, `processing_time_seconds`, `generated_at`. |
| `refinement_weight_matrix` | `Dict` | Weights and description: `terrain_slope`, `land_acquisition_cost`, `environmental_sensitivity`, `construction_logistics`, `highway_corridor_proximity`, `no_go_zone_penalty` (hard constraint). |
| `refined_variants` | `List[Dict]` | Per variant: `id`, `source_variant_id`, `label`, `refinement_status`, `geospatial_length_km`, `refined_length_km`, `length_delta_km`, `length_delta_reason`, `alignment_score`, `alignment_score_breakdown` (row_compliance, turning_radius_compliance, terrain_smoothness, crossing_optimisation, environmental_buffer_compliance), `metric_scores` (per metric: score, weight, weighted_contribution, notes), `composite_score`, `geospatial_highway_overlap_pct`, `refined_highway_overlap_pct`, `overlap_delta_pct`, `overlap_delta_reason`, `turning_radius_adjustments` (total_adjustments_made, total_length_adjusted_km, adjustments[]), `crossings` (total_crossings, crossings_detail[] with crossing_id, type, name, coords, span_m/km, method, estimated_cost_usd), `hard_constraint_checks` (no_go_zone_violations, ramsar_buffer_violations, protected_area_encroachments, row_envelope_breaches, status; optional row_breach_resolution), `refined_segments` (segment_id, label, geospatial_length_km, refined_length_km, refined_highway_overlap_pct, turning_radius_adjustments, crossings, alignment_score, notes), `output_uri`. Optional: `refinement_warnings`, `key_tradeoff`. |
| `refinement_summary` | `Dict` | `recommended_variant_post_refinement`, `recommendation_unchanged_from_geospatial`, `recommendation_rationale`, `notable_findings`, `variant_comparison_post_refinement` (id, refined_length_km, composite_score, highway_overlap_pct, hard_constraints_passed, warnings). |
| `output_uris` | `Dict` | `all_refined_routes_geojson`, `recommended_refined_route_geojson`, `refinement_comparison_csv`, `turning_radius_adjustments_geojson`, `crossings_geojson`. |
| `message` | `string` | Human-readable summary. |

---

### 2. `quantify_colocation_benefits`

**What it does:** Models **CAPEX savings from infrastructure sharing**. It quantifies cost reductions from shared land clearing, access roads, and construction logistics when the power line is built alongside the highway (or other linear asset).

**When to use:** When comparing colocated vs standalone transmission to report savings and justify corridor approach.

**Key concepts:** Colocation = shared RoW and construction; savings in land, access, and mobilization.

**Input**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `refined_routes` | `List[Dict]` | Yes | — | Output from `refine_optimized_routes`: list of refined variants (id, refined_length_km, alignment_score, refined_highway_overlap_pct, refined_segments, etc.). |
| `shared_infrastructure_types` | `List[str]` | No | `["access_roads", "land_clearing", "security"]` | Types of shared infrastructure to include (e.g. access_roads, land_clearing, security, land_acquisition, eia_and_permitting, construction_logistics). |

**Output**

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | e.g. `"Co-location Analysis Complete"`. |
| `job_metadata` | `Dict` | `tool`, `corridor_id`, `variants_analysed`, `shared_infrastructure_types_assessed`, `baseline`, `generated_at`. |
| `savings_methodology` | `Dict` | `description`, `greenfield_unit_costs` (access_roads_per_km, land_clearing_per_km, land_acquisition_per_km, security_per_km_per_year, eia_standalone_cost, construction_logistics_per_km), `co_location_unit_costs`, `savings_rate_per_category`. |
| `variant_colocation_analysis` | `List[Dict]` | Per variant: `variant_id`, `label`, `refined_length_km`, `refined_highway_overlap_pct`, `co_located_length_km`, `standalone_length_km`, `greenfield_baseline` (description, access_roads_usd, land_clearing_usd, land_acquisition_usd, security_usd, eia_and_permitting_usd, construction_logistics_usd, total_greenfield_civil_usd), `colocation_actual_cost` (same line items + total_colocation_civil_usd), `total_colocation_savings_usd`, `savings_as_pct_of_gross_capex`, `savings_breakdown` (per category: saving_usd, saving_pct, notes), `segment_savings` (segment_id, label, length_km, highway_overlap_pct, co_located_length_km, colocation_savings_usd, savings_pct_of_segment_capex, primary_saving_driver, notes), `recommendation`. Optional: `notes`, `critical_finding`. |
| `comparative_summary` | `Dict` | `variant_ranking_by_colocation_savings` (rank, variant_id, total_savings_usd, savings_pct, overlap_pct, net_capex_usd), `key_insights`, `recommended_variant`, `recommendation_rationale`. |
| `output_uris` | `Dict` | `colocation_analysis_csv`, `segment_savings_breakdown`, `greenfield_vs_colocation_comparison`. |
| `message` | `string` | Human-readable summary of colocation benefits. |

---

### 3. `size_voltage_and_capacity`

**What it does:** Determines **optimal technical specifications** including **voltage levels (e.g. 330–400 kV)** and **conductor types** to minimize line losses over long distances while meeting load and reliability requirements.

**When to use:** After demand and route length are known; use to set voltage, conductor, and thermal capacity for the corridor.

**Key concepts:** Voltage level, conductor type, losses, thermal capacity, N-1 or reliability criteria.

**Input**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `peak_demand_mw` | `float` | Yes | Total peak demand (MW) from the Opportunity Identification agent (or demand model). |
| `transmission_distance_km` | `float` | Yes | Route length in kilometres (e.g. from refined route `refined_length_km`). |

**Output**

| Field | Type | Description |
|-------|------|-------------|
| `corridor_id` | `string` | Corridor identifier. |
| `corridor_length_km` | `float` | Total corridor length. |
| `total_segments` | `int` | Number of segments (backbone + spur + distribution). |
| `sizing_philosophy` | `string` | Rationale for sizing approach. |
| `backbone_segments` | `List[Dict]` | Per segment: `segment_id`, `gap_id`, `phase`, `name`, `from_node`, `to_node`, `route_length_km`, `highway_co_location_pct`, `countries_traversed`, `demand_profile` (current_mw, year_5_mw, year_10_mw, year_20_mw, sizing_target_mw), `voltage_selection` (recommended_voltage_kv, alternatives_considered[], voltage_selection_rationale), `security_standard` (required_standard, configuration, rationale), `conductor_specification` (type, size, bundle, thermal_rating_mw, surge_impedance_loading_mw, rationale), `reactive_power_compensation` (required, type, location, rationale), `special_considerations`. |
| `spur_segments` | `List[Dict]` | Same structure as backbone; includes `anchor_served`. |
| `distribution_reinforcements` | `List[Dict]` | `segment_id`, `anchors_served`, `voltage_kv`, `configuration`, `length_km`, `capacity_mw`, `security_standard`, `conductor_type`, `rationale`. |
| `lekki_hub_specification` | `Dict` | Hub config: `hub_id`, `location`, `coords`, `anchors_directly_served`, `hub_configuration` (voltage_levels, transformer_bays, incoming_circuits, outgoing_feeders, phase_1a_capacity_mw, phase_1b_capacity_mw, ultimate_capacity_mw), `rationale`. |
| `corridor_summary` | `Dict` | `total_segments`, `backbone_segments`, `spur_segments`, `distribution_reinforcements`, `voltage_mix` (400kv_km, 330kv_km, 161kv_km, 33_132kv_km, total_line_km), `conductor_mix`, `security_standards` (N-1-1_segments, N-1_segments, N-0_segments), `total_estimated_line_losses`, `reactive_power_compensation_sites`, `border_crossings`, `underground_cable_sections_km`, `protected_area_deviations`. |
| `message` | `string` | Human-readable summary of sizing outcome. |

---

### 4. `optimize_substation_placement`

**What it does:** Optimizes **substation locations** to serve anchor loads efficiently. It determines the minimal number of step-down points required to connect the maximum number of high-value customers along the corridor.

**When to use:** When anchor loads and route are defined; use to place substations and define offtake points.

**Key concepts:** Step-down substations, anchor load connection, minimal substation count vs coverage.

**Input**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `anchor_load_clusters` | `List[Dict]` | Yes | Anchor load groupings from the Opportunity Identification agent (e.g. cluster id, location/coords, load_mw, customer names, readiness dates). |
| `refined_route_uri` | `string` | Yes | URI or reference to the chosen refined route (from `refine_optimized_routes` output) used for alignment. |

**Output**

| Field | Type | Description |
|-------|------|-------------|
| `corridor_id` | `string` | Corridor identifier. |
| `placement_philosophy` | `string` | Rationale for placement approach. |
| `primary_hubs` | `List[Dict]` | Per hub: `id`, `name`, `coords` ([lat, lon]), `voltage_levels`, `phase`, `segment_ref`, `serves` (anchor IDs), `capacity_mw`, `terrain`, `road_access`, `distance_to_highway_m`, `land_status`, `rationale`. Optional: `phase_1a_capacity_mw`, `phase_1b_capacity_mw`. |
| `spur_substations` | `List[Dict]` | Same structure; `serves` is list of anchor IDs. |
| `distribution_substations` | `List[Dict]` | `id`, `name`, `coords`, `voltage_levels`, `phase`, `segment_ref`, `serves`, `configuration`, `capacity_mw`, `terrain`, `rationale`. Optional: `distance_to_highway_m`, `land_status`. |
| `corridor_summary` | `Dict` | `total_substations`, `primary_hubs`, `spur_substations`, `distribution_substations`, `by_phase` (phase_1/2/3: count, substations[], rationale), `by_country` (list of substation IDs per country), `anchor_loads_served` (total_anchors_connected, critical_class, high_class, standard_class), `greenfield_vs_brownfield` (counts, note), `total_capacity_summary` (total_transformation_capacity_mw, phase_*_capacity_mw). |
| `message` | `string` | Human-readable summary of placement rationale. |

---

### 5. `generate_phasing_strategy`

**What it does:** Aligns **transmission development with highway construction and anchor load timelines**. It creates a **2–3 phase plan** so that power is available when industry and transport become operational.

**When to use:** To produce a phased rollout (e.g. Phase 1: trunk; Phase 2: extensions; Phase 3: last-mile) for planning and financing.

**Key concepts:** Phasing, construction sequence, demand ramp-up, readiness for anchor loads.

**Input**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `highway_schedule` | `Dict` | Yes | Construction timeline for the highway (e.g. source, per lot: segment, highway_construction_start, highway_construction_end, countries). |
| `anchor_load_readiness` | `List[Dict]` | Yes | When customers need power: per anchor or cluster (e.g. name, readiness_year, load_mw, segment). |

**Output**

| Field | Type | Description |
|-------|------|-------------|
| `corridor_id` | `string` | Corridor identifier. |
| `phasing_philosophy` | `string` | Rationale for phasing approach. |
| `highway_schedule_reference` | `Dict` | `source`, per lot: `segment`, `highway_construction_start`, `highway_construction_end`, `countries`. |
| `phasing_plan` | `List[Dict]` | Per phase: `phase`, `name`, `years`, `calendar_years`, `highway_lots_aligned`, `capex_usd`, `segments` (per segment: `segment_id`, `name`, `rationale`, `anchor_loads_energised`, `energisation_year`, `revenue_at_energisation_usd_per_year`; optional `conditional`, `conditions_required`), `substations_commissioned`, `phase_*_total_revenue_*_usd`, `phase_*_anchor_mw_connected`, `key_milestones` (milestone, target_date, dependencies), `risks` (risk, probability, impact, mitigation). |
| `corridor_summary` | `Dict` | `total_phases`, `total_construction_years`, `calendar_span`, `total_capex_usd`, `capex_by_phase`, `revenue_ramp` (year_*_usd), `anchor_mw_connected_by_phase`, `alignment_summary` (per highway lot → phase/segment, note), `conditional_segments` (count, segments[], combined_capex_if_both_proceed_usd, note). |
| `message` | `string` | Human-readable summary (e.g. phase count and alignment with highway lots). |

---

### 6. `generate_cost_estimates`

**What it does:** Generates **detailed CAPEX and OPEX estimates**. It uses regional unit costs (IEA) for lines, substations, and labor to produce a project budget, typically with a contingency (e.g. 15%).

**When to use:** After routes, voltage, substations, and phasing are set; use to produce the cost base for financial modeling and financing optimization.

**Key concepts:** CAPEX (lines, substations, civils, contingency), OPEX (O&M, insurance), regional unit rates.

**Input**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `technical_specs` | `Dict` | Yes | Voltage and conductor data from `size_voltage_and_capacity` (e.g. backbone/spur segment specs: recommended_voltage_kv, conductor type, thermal_rating_mw). Can be full sizing output or a summary. |
| `route_length_km` | `float` | Yes | Total transmission route length in kilometres (from refined route). |
| `substation_count` | `int` | Yes | Number of substations (from `optimize_substation_placement` corridor_summary.total_substations). |

**Output**

| Field | Type | Description |
|-------|------|-------------|
| `corridor_id` | `string` | Corridor identifier. |
| `cost_basis` | `Dict` | `pricing_date`, `currency`, `contingency_pct`, `unit_cost_source`, `regional_adjustments` (per country), `colocation_savings_applied`, `colocation_savings_basis`. |
| `unit_costs_usd` | `Dict` | `transmission_lines` (per km by voltage/conductor), `substations` (per bay/type), `reactive_power_compensation` (shunt_reactor_per_mvar, svc_per_mvar, statcom_per_mvar), `ancillary` (scada_per_substation, fiber_optic_per_km, border_crossing_package, esia_per_segment, resettlement_per_household). |
| `capex_by_segment` | `List[Dict]` | Per segment: `segment_id`, `name`, `phase`, `route_length_km`, `voltage_kv`, `conductor`, `colocation_pct`, `line_costs_usd` (breakdown + subtotal), `substation_costs_usd`, `ancillary_costs_usd`, `subtotal_before_contingency_usd`, `colocation_savings_usd`, `subtotal_after_savings_usd`, `contingency_15pct_usd`, `total_segment_capex_usd`. Optional: `conditional`, `note`. |
| `cost_summary` | `Dict` | `line_costs_usd`, `substation_costs_usd`, `reactive_power_compensation_usd`, `scada_and_fiber_usd`, `esia_resettlement_and_permitting_usd`, `local_content_and_regulatory_levies_usd`, `other_civil_and_eia_usd`, `subtotal_before_contingency_usd`, `total_colocation_savings_usd`, `subtotal_after_colocation_savings_usd`, `contingency_15pct_usd`, `total_capex_usd`; `annual_opex_usd` (transmission_line_maintenance, substation_maintenance, scada_and_it_systems, insurance, staffing_corridor_operations, reactive_power_compensation_maintenance, total_annual_opex_usd). |
| `cost_by_phase` | `Dict` | Per phase: `segments`, `total_capex_usd`, `pct_of_total`, `rationale`. |
| `cost_by_country` | `Dict` | Per country: `capex_usd`, `pct_of_total`, `primary_items`. |
| `colocation_savings_breakdown` | `Dict` | `total_savings_usd`, `pct_of_gross_capex`, `by_category`, `highest_saving_segment` (segment, overlap_pct, saving_usd), `lowest_saving_segment`. |
| `capex_range` | `string` | Formatted CAPEX range (e.g. `"$840M - $1,040M"`). |
| `message` | `string` | Human-readable summary (basis: voltage, conductor, colocation; net CAPEX and OPEX). |

---

## Typical Workflow

1. **Routes:** Use `refine_optimized_routes` to turn Geospatial paths into engineering alignments within RoW.
2. **Colocation:** Use `quantify_colocation_benefits` to quantify savings from shared corridor.
3. **Sizing:** Use `size_voltage_and_capacity` to set voltage and conductor for the corridor.
4. **Substations:** Use `optimize_substation_placement` to place step-downs and connect anchor loads.
5. **Phasing:** Use `generate_phasing_strategy` to align build-out with highway and demand.
6. **Costs:** Use `generate_cost_estimates` to produce CAPEX/OPEX for the Financing and Economic Impact agents.
