CORRIDOR_DATA_TOOL_DESCRIPTION = """Query the Corridor Intelligence Platform's data APIs.

This tool gives you direct access to ALL corridor data — economic indicators, trade flows,
energy infrastructure, conflict events, projects, manufacturing, agriculture, policy,
tourism, and geospatial layers. Use it to answer data questions with REAL numbers.

## Available functions:

### Economic & Social Indicators
- **get_country_summary(country)** — Latest GDP, FDI, trade%, inflation, electricity access for one country (ISO3: NGA, BEN, TGO, GHA, CIV)
- **get_country_indicators(indicator, country?, start_year?, end_year?)** — Time-series for: GDP, GDP_GROWTH, GDP_PER_CAPITA, FDI, TRADE_PCT_GDP, REMITTANCES, INFLATION, POPULATION, URBAN_POP_PCT, ELECTRICITY_ACCESS, INTERNET_USERS

### Trade & Commodities
- **get_trade_flows(country, commodity)** — Bilateral trade volumes/values from UN Comtrade
- **get_commodity_prices(commodity, start_year?, end_year?)** — Monthly price time-series (cocoa, gold, oil, rubber, cashew, palm_oil, cotton, fish, timber, bauxite, cement, phosphates, manganese, shea)
- **get_value_chain(commodity)** — Raw vs processed price differential per country

### Infrastructure & Energy
- **get_infrastructure()** — All ports, airports, rail, border crossings, industrial zones (GeoJSON)
- **get_power_plants(fuel?, country?)** — Power plants with capacity (MW), fuel type, location
- **get_roads(tiers?)** — Road network GeoJSON filtered by tier (1-4)

### Projects & Investment
- **get_projects(country?, sector?, status?)** — 173 corridor infrastructure projects (World Bank + EU Forum)
- **get_projects_summary()** — Total projects, cost, breakdown by sector/status/country

### Conflict & Security
- **get_conflict_events(country?, year?, event_type?)** — ACLED events with location, fatalities, actors

### Geospatial / Satellite (returns tile URLs for map rendering)
- **get_nightlights(year, month)** — VIIRS nighttime lights
- **get_population(year)** — WorldPop population density
- **get_landcover()** — ESA WorldCover land classification
- **get_economic_index(year, month)** — Composite economic activity index

### Natural Resources
- **get_minerals(commodity?, status?)** — USGS mineral sites with commodity type
- **get_economic_anchors()** — Combined minerals + ports + industrial + power

### Social Infrastructure
- **get_social_facilities(type?)** — OSM health, education, government, financial, religious, military facilities
- **get_livestock(species?)** — FAO livestock density (cattle, goats, sheep, chickens, pigs)
- **get_connectivity(type?)** — Ookla internet speed/coverage

### Policy & Governance
- **get_policies(country?, category?)** — Investment, environmental, trade policies
- **get_policy_comparison()** — Cross-country tax holidays, EIA timelines, local content
- **get_governance()** — V-Dem democracy, rule of law, corruption indices

### Agriculture & Tourism
- **get_agriculture(country?, crop?)** — FAO crop production (14 crops across 5 countries)
- **get_tourism()** — Tourism arrivals, receipts, employment by country
- **get_manufacturing(country?, sector?)** — Manufacturing companies and sectors

ALWAYS use this tool to get real data before answering. NEVER make up numbers.
"""
