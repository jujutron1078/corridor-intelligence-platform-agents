# Geospatial Intelligence Agent

This agent provides geographic and spatial analysis for corridor planning. It geocodes locations, defines corridor boundaries, fetches and processes geospatial layers (e.g. imagery, DEM, land use), analyzes terrain, detects infrastructure and anchor loads from imagery, and runs route optimization subject to terrain and environmental constraints.

---

## Shared Tools (Platform-Wide)

All agents use these common tools:

| Tool | Purpose |
|------|--------|
| **think_tool** | Step-by-step reasoning and documentation of assumptions. |
| **write_todos** | Structured task list for multi-step workflows. |

---

## Domain Tools

### 1. `geocode_location`

**What it does:** Converts **user-provided place names into precise geographic coordinates (latitude/longitude)**. Use it when the source or destination is not already in lat/lon format—e.g. names like "Abidjan", "Lagos", "Nairobi to Mombasa", or "Tema Port to Kumasi"—or when a location is ambiguous and must be resolved for routing.

**Input:** JSON with a `locations` array. Each item has `name` (required) and optionally `country`.  
Example: `{"locations": [{"name": "Abidjan", "country": "Côte d'Ivoire"}, {"name": "Lagos", "country": "Nigeria"}]}`

**Output:** JSON with a `resolved_locations` array. Each item has `input_name`, `latitude`, `longitude`, and `confidence` (0–1).

**When to use:** First step when the user specifies locations by name; use the returned coordinates in `define_corridor` and downstream tools.

---

### 2. `define_corridor`

**What it does:** Creates a **geographic bounding polygon (corridor)** between two points with a specified buffer width. This defines the search and analysis area for all subsequent infrastructure and environmental analysis.

**When to use:** After you have coordinates (from `geocode_location` or user input), to establish the corridor geometry that `fetch_geospatial_layers`, terrain, and route tools will use.

**Key concepts:** Corridor = polygon (often a buffered line between A and B). All later layers are clipped to this area.

---

### 3. `fetch_geospatial_layers`

**What it does:** **Fetches, clips, and processes geospatial layers** for a corridor defined by `define_corridor`. It downloads requested layer types (e.g. satellite imagery, DEM, land use, protected areas) at the specified resolution, clips them to the corridor boundary, and returns **Analysis Ready Data (ARD)** with file URIs for downstream tools and key extracted data points for the agent.

**When to use:** After the corridor is defined; request the layers needed for terrain analysis, infrastructure detection, and routing (e.g. DEM, imagery, land use, protected areas).

**Key concepts:** ARD = pre-processed, corridor-clipped layers; URIs are passed to `terrain_analysis`, `infrastructure_detection`, and `route_optimization`.

---

### 4. `terrain_analysis`

**What it does:** Analyzes **elevation data (DEM from fetch_geospatial_layers)** to calculate slopes, flood risks, and construction difficulty scores along the corridor. It produces terrain statistics, engineering notes, and a **cost surface** for the routing engine.

**When to use:** When you need slope, flood risk, and buildability to feed into route optimization and cost estimation.

**Key concepts:** Cost surface = raster where cell values represent relative cost/difficulty of building; used by `route_optimization` to find least-cost paths.

---

### 5. `infrastructure_detection`

**What it does:** Runs **computer vision inference on satellite imagery** to detect anchor loads and existing infrastructure. It accepts an S3 image URI from `fetch_geospatial_layers` and a list of infrastructure types to detect (e.g. energy, transport, settlements). It returns detected features with coordinates, labels, confidence scores, and class.

**When to use:** To identify existing infrastructure and potential anchor loads (mines, industries, settlements) from imagery before routing and demand modeling.

**Key concepts:** Anchor load = demand node (e.g. mine, factory, town); detections feed into route optimization and opportunity identification.

---

### 6. `route_optimization`

**What it does:** Calculates the **most efficient infrastructure paths** by combining the terrain cost surface, environmental constraints (e.g. No-Go zones), and anchor nodes from infrastructure detection. It accepts corridor_id, anchor node coordinates, cost_surface_uri (from terrain analysis), constraints_uri (e.g. from environmental layers), and optional priority: `min_cost`, `min_distance`, `max_impact`, or `balance`. It returns optimized route variants with geometry, length, CAPEX, terrain difficulty, and co-location index for stakeholder review.

**When to use:** After terrain and constraints are ready and anchor nodes are defined; use to get candidate alignments for the corridor.

**Key concepts:** Least-cost path, No-Go zones, anchor nodes, co-location (e.g. with highway), multiple objectives (cost vs distance vs impact).

---

## Typical Workflow

1. **Geocode:** Use `geocode_location` for any place-name endpoints.
2. **Corridor:** Use `define_corridor` with endpoints and buffer to create the analysis polygon.
3. **Layers:** Use `fetch_geospatial_layers` to get DEM, imagery, land use, protected areas, etc.
4. **Terrain:** Use `terrain_analysis` on the DEM to get slopes, flood risk, and cost surface.
5. **Detection:** Use `infrastructure_detection` on imagery to get anchor loads and existing infrastructure.
6. **Routes:** Use `route_optimization` with cost surface, constraints, and anchors to produce optimized corridor alignments.

Outputs (route geometry, CAPEX, anchors) feed into the Infrastructure Optimization and Opportunity Identification agents.
