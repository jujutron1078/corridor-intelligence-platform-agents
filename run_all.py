"""
Unified CLI runner for the Corridor Intelligence Platform.

Commands:
    python run_all.py validate    Check all data sources
    python run_all.py pull        Download/extract all non-GEE data
    python run_all.py process     Process all downloaded data
    python run_all.py report      Generate data availability report
    python run_all.py serve       Start FastAPI server
    python run_all.py all         validate + pull + process + report
"""

from __future__ import annotations

import sys

import click
from rich.console import Console

from src.shared.pipeline.utils import setup_logging, load_env

console = Console()


@click.group()
def cli():
    """Lagos-Abidjan Corridor Intelligence Platform."""
    setup_logging()
    load_env()


@cli.command()
@click.option("--skip-gee", is_flag=True, help="Skip GEE validation (no auth needed)")
def validate(skip_gee: bool):
    """Check all data sources are accessible."""
    console.print("[bold cyan]Running full data validation...[/bold cyan]\n")

    from src.catalog.validator import run_full_validation
    report = run_full_validation(include_gee=not skip_gee)

    summary = report["summary"]
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  [green]Validated: {summary['validated']}[/green]")
    console.print(f"  [yellow]Partial: {summary['partial']}[/yellow]")
    console.print(f"  [red]Missing: {summary['missing']}[/red]")
    console.print(f"  Total: {summary['total']}")


@cli.command()
def pull():
    """Download/extract all non-GEE data (OSM, USGS, World Bank, ACLED, trade)."""
    import os
    from src.shared.pipeline.freshness import record_pull
    console.print("[bold cyan]Pulling all external data...[/bold cyan]\n")

    # OSM
    console.rule("OSM Data")
    try:
        from src.pipelines.osm_pipeline.extractor import extract_all
        from src.pipelines.osm_pipeline.config import OSM_OUTPUT_FILES, OSM_DATA_DIR
        from src.shared.pipeline.utils import save_geojson, ensure_dir

        ensure_dir(OSM_DATA_DIR)
        results = extract_all()
        total_features = 0
        for name, geojson in results.items():
            path = OSM_OUTPUT_FILES.get(name)
            if path:
                save_geojson(geojson, path)
                n = len(geojson['features'])
                total_features += n
                console.print(f"  {name}: {n} features")
        record_pull("osm", total_features)
        console.print("[green]OSM extraction complete.[/green]")
    except Exception as exc:
        console.print(f"[red]OSM extraction failed: {exc}[/red]")

    # USGS Minerals
    console.rule("USGS Minerals")
    try:
        from src.pipelines.mineral_pipeline.downloader import download_geodatabase
        from src.pipelines.mineral_pipeline.processor import process_geodatabase, export_all

        result = download_geodatabase()
        if result:
            results = process_geodatabase(result)
            export_all(results)
            total = sum(len(g.get("features", [])) for g in results.values())
            record_pull("mineral", total)
            console.print(f"[green]USGS complete: {len(results)} layers, {total} features.[/green]")
        else:
            console.print("[yellow]USGS download returned no data (may need manual download).[/yellow]")
    except Exception as exc:
        console.print(f"[red]USGS download failed: {exc}[/red]")

    # World Bank indicators (no API key required)
    console.rule("World Bank Indicators")
    try:
        from src.pipelines.worldbank_pipeline.indicators import fetch_all_indicators, save_indicators

        data = fetch_all_indicators()
        total = sum(len(v) for v in data.values())
        save_indicators(data)
        record_pull("worldbank", total)
        console.print(f"[green]World Bank: {total} indicator records saved.[/green]")
    except Exception as exc:
        console.print(f"[red]World Bank pull failed: {exc}[/red]")

    # Energy (Global Power Plant Database)
    console.rule("Energy Data")
    try:
        from src.pipelines.energy_pipeline.downloader import download_power_plants
        from src.pipelines.energy_pipeline.processor import process_power_plants, export_power_plants

        csv_path = download_power_plants()
        geojson = process_power_plants(csv_path)
        export_power_plants(geojson)
        record_pull("energy", len(geojson["features"]))
        console.print(f"[green]Energy: {len(geojson['features'])} power plants saved.[/green]")
    except Exception as exc:
        console.print(f"[red]Energy data pull failed: {exc}[/red]")

    # ACLED conflict data (OAuth2 with username/password)
    console.rule("ACLED Conflict Data")
    try:
        from src.pipelines.acled_pipeline.fetcher import fetch_all_corridor_events, save_events

        events = fetch_all_corridor_events()
        save_events(events)
        record_pull("acled", len(events))
        console.print(f"[green]ACLED: {len(events)} conflict events saved.[/green]")
    except Exception as exc:
        console.print(f"[red]ACLED pull failed: {exc}[/red]")

    # Health facilities (healthsites.io — no API key required)
    console.rule("Health Facilities")
    try:
        from src.pipelines.health_pipeline.downloader import download_all_countries
        from src.pipelines.health_pipeline.processor import facilities_to_geojson, save_health_facilities

        facilities = download_all_countries()
        geojson = facilities_to_geojson(facilities)
        save_health_facilities(geojson)
        record_pull("health", len(geojson["features"]))
        console.print(f"[green]Health: {len(geojson['features'])} facilities saved.[/green]")
    except Exception as exc:
        console.print(f"[red]Health data pull failed: {exc}[/red]")

    # Trade data (prices only — Comtrade needs API key)
    console.rule("Trade Data")
    try:
        from src.pipelines.trade_pipeline.pinksheet import download_pinksheet, parse_pinksheet, save_prices

        path = download_pinksheet()
        df = parse_pinksheet(path)
        save_prices(df)
        record_pull("trade_prices", len(df))
        console.print(f"[green]Pink Sheet: {len(df)} price records saved.[/green]")
    except Exception as exc:
        console.print(f"[red]Trade data pull failed: {exc}[/red]")

    # IMF WEO
    console.rule("IMF World Economic Outlook")
    try:
        from src.pipelines.imf_pipeline.fetcher import fetch_all_indicators as imf_fetch, save_indicators as imf_save
        data = imf_fetch()
        total = sum(len(v) for v in data.values())
        imf_save(data)
        record_pull("imf", total)
        console.print(f"[green]IMF WEO: {total} indicator records saved.[/green]")
    except Exception as exc:
        console.print(f"[red]IMF WEO pull failed: {exc}[/red]")

    # CPI
    console.rule("Transparency International CPI")
    try:
        from src.pipelines.cpi_pipeline.fetcher import fetch_cpi_scores, save_cpi_scores
        scores = fetch_cpi_scores()
        save_cpi_scores(scores)
        record_pull("cpi", len(scores))
        console.print(f"[green]CPI: {len(scores)} country scores saved.[/green]")
    except Exception as exc:
        console.print(f"[red]CPI pull failed: {exc}[/red]")

    # V-Dem Governance
    console.rule("V-Dem Governance Indicators")
    try:
        from src.pipelines.vdem_pipeline.fetcher import get_governance_indicators, save_governance
        data = get_governance_indicators()
        save_governance(data)
        record_pull("vdem", 5)
        console.print("[green]V-Dem: governance indicators saved for 5 countries.[/green]")
    except Exception as exc:
        console.print(f"[red]V-Dem pull failed: {exc}[/red]")

    # Global Data Lab HDI
    console.rule("Global Data Lab Sub-national HDI")
    try:
        from src.pipelines.gdl_pipeline.fetcher import fetch_all_countries as gdl_fetch, save_subnational_hdi
        data = gdl_fetch()
        total = sum(len(v) for v in data.values()) if isinstance(data, dict) else len(data)
        save_subnational_hdi(data)
        record_pull("gdl", total)
        console.print(f"[green]GDL: {total} sub-national HDI records saved.[/green]")
    except Exception as exc:
        console.print(f"[red]GDL pull failed: {exc}[/red]")

    # FAO FAOSTAT
    console.rule("FAO Agricultural Production")
    try:
        from src.pipelines.fao_pipeline.fetcher import fetch_all_commodities, save_production
        data = fetch_all_commodities()
        total = sum(len(v) for v in data.values())
        save_production(data)
        record_pull("fao", total)
        console.print(f"[green]FAO: {total} production records saved.[/green]")
    except Exception as exc:
        console.print(f"[red]FAO pull failed: {exc}[/red]")

    # AidData
    console.rule("AidData Development Finance")
    try:
        from src.pipelines.aiddata_pipeline.fetcher import fetch_corridor_projects, save_projects as aiddata_save
        projects = fetch_corridor_projects()
        aiddata_save(projects)
        record_pull("aiddata", len(projects))
        console.print(f"[green]AidData: {len(projects)} corridor projects saved.[/green]")
    except Exception as exc:
        console.print(f"[red]AidData pull failed: {exc}[/red]")

    # GEM Planned Energy
    console.rule("Global Energy Monitor")
    try:
        from src.pipelines.gem_pipeline.fetcher import fetch_planned_projects, save_projects as gem_save
        projects = fetch_planned_projects()
        gem_save(projects)
        record_pull("gem", len(projects))
        console.print(f"[green]GEM: {len(projects)} planned energy projects saved.[/green]")
    except Exception as exc:
        console.print(f"[red]GEM pull failed: {exc}[/red]")

    # UNCTAD Port Statistics
    console.rule("UNCTAD Port Statistics")
    try:
        from src.pipelines.unctad_pipeline.fetcher import get_port_statistics, save_port_statistics
        ports = get_port_statistics()
        save_port_statistics(ports)
        record_pull("unctad", len(ports))
        console.print(f"[green]UNCTAD: {len(ports)} port records saved.[/green]")
    except Exception as exc:
        console.print(f"[red]UNCTAD pull failed: {exc}[/red]")

    # energydata.info Grid
    console.rule("energydata.info Transmission Grid")
    try:
        from src.pipelines.energydata_pipeline.fetcher import fetch_transmission_lines, fetch_substations, save_grid_data
        lines = fetch_transmission_lines()
        subs = fetch_substations()
        save_grid_data({"transmission_lines": lines, "substations": subs})
        record_pull("energydata", len(lines) + len(subs))
        console.print(f"[green]energydata.info: {len(lines)} lines + {len(subs)} substations saved.[/green]")
    except Exception as exc:
        console.print(f"[red]energydata.info pull failed: {exc}[/red]")

    # IFC PPI
    console.rule("IFC PPI Database")
    try:
        from src.pipelines.ppi_pipeline.fetcher import fetch_ppi_projects, save_ppi_projects
        projects = fetch_ppi_projects()
        save_ppi_projects(projects)
        record_pull("ppi", len(projects))
        console.print(f"[green]PPI: {len(projects)} PPP projects saved.[/green]")
    except Exception as exc:
        console.print(f"[red]PPI pull failed: {exc}[/red]")

    # GADM Admin Boundaries
    console.rule("GADM Admin Boundaries")
    try:
        from src.pipelines.gadm_pipeline.fetcher import fetch_all_countries as gadm_fetch, save_boundaries
        data = gadm_fetch()
        n = len(data.get("features", []))
        save_boundaries(data)
        record_pull("gadm", n)
        console.print(f"[green]GADM: {n} admin regions saved.[/green]")
    except Exception as exc:
        console.print(f"[red]GADM pull failed: {exc}[/red]")

    # WAPP Master Plan
    console.rule("WAPP Master Plan")
    try:
        from src.pipelines.wapp_pipeline.fetcher import get_interconnections, get_generation_targets, get_trade_volumes, save_wapp_data
        data = {"interconnections": get_interconnections(), "generation_targets": get_generation_targets(), "trade_volumes": get_trade_volumes()}
        save_wapp_data(data)
        record_pull("wapp", len(data["interconnections"]))
        console.print(f"[green]WAPP: {len(data['interconnections'])} interconnections saved.[/green]")
    except Exception as exc:
        console.print(f"[red]WAPP pull failed: {exc}[/red]")

    console.print("\n[bold green]Data pull complete.[/bold green]")


@cli.command()
def process():
    """Process all downloaded data."""
    console.print("[bold cyan]Processing all data...[/bold cyan]\n")

    # OSM road classification + network
    console.rule("OSM Network")
    try:
        from src.pipelines.osm_pipeline.config import OSM_OUTPUT_FILES
        from src.pipelines.osm_pipeline.processor import classify_roads, build_network_graph, find_pinch_points, generate_network_report
        from src.shared.pipeline.utils import load_geojson, save_geojson, ensure_dir
        import json

        roads_path = OSM_OUTPUT_FILES["roads"]
        if roads_path.exists():
            roads = load_geojson(roads_path)
            roads = classify_roads(roads)
            save_geojson(roads, roads_path)

            G = build_network_graph(roads)
            pinch_points = find_pinch_points(G)
            report = generate_network_report(roads, G, pinch_points)

            network_path = OSM_OUTPUT_FILES["network"]
            ensure_dir(network_path.parent)
            with open(network_path, "w") as f:
                json.dump(report, f, indent=2)

            console.print(f"  Road segments: {report['network_stats']['total_edges']}")
            console.print(f"  Total km: {report['network_stats']['total_km']}")
            console.print(f"  Pinch points: {len(pinch_points)}")
            console.print("[green]OSM network processing complete.[/green]")
        else:
            console.print("[yellow]No roads data found. Run 'pull' first.[/yellow]")
    except Exception as exc:
        console.print(f"[red]OSM processing failed: {exc}[/red]")

    # USGS minerals
    console.rule("USGS Minerals")
    try:
        from src.pipelines.mineral_pipeline.processor import process_geodatabase, export_all
        from src.shared.pipeline.utils import DATA_DIR

        gdb_dir = DATA_DIR / "mineral" / "geodatabase"
        gdb_path = None
        if gdb_dir.exists():
            for item in gdb_dir.rglob("*.gdb"):
                if item.is_dir():
                    gdb_path = item
                    break

        if gdb_path:
            results = process_geodatabase(gdb_path)
            export_all(results)
            console.print(f"[green]Processed {len(results)} mineral layers.[/green]")
        else:
            console.print("[yellow]No geodatabase found. Run 'pull' first.[/yellow]")
    except Exception as exc:
        console.print(f"[red]Mineral processing failed: {exc}[/red]")

    # Value-chain analysis
    console.rule("Value Chain")
    try:
        from src.pipelines.trade_pipeline.value_chain import compute_all_value_chains, save_value_chain_report

        results = compute_all_value_chains()
        save_value_chain_report(results)
        console.print(f"[green]Computed value chains for {len(results)} commodities.[/green]")
    except Exception as exc:
        console.print(f"[red]Value chain computation failed: {exc}[/red]")

    console.print("\n[bold green]Processing complete.[/bold green]")


@cli.command()
def report():
    """Generate data availability report."""
    console.print("[bold cyan]Generating data availability report...[/bold cyan]\n")

    try:
        from src.catalog.validator import run_full_validation
        from src.catalog.report import save_report

        validation = run_full_validation(include_gee=False)
        path = save_report(validation)
        console.print(f"[green]Report saved: {path}[/green]")
    except Exception as exc:
        console.print(f"[red]Report generation failed: {exc}[/red]")


@cli.command()
@click.option("--host", default=None, help="Override host")
@click.option("--port", default=None, type=int, help="Override port")
def serve(host: str | None, port: int | None):
    """Start the FastAPI server."""
    import uvicorn
    from src.api.config import API_HOST, API_PORT

    actual_host = host or API_HOST
    actual_port = port or API_PORT

    console.print(f"[bold cyan]Starting API server at {actual_host}:{actual_port}...[/bold cyan]")
    uvicorn.run(
        "src.api.main:app",
        host=actual_host,
        port=actual_port,
        reload=True,
        log_level="info",
    )


@cli.command("all")
@click.pass_context
def run_all(ctx):
    """Run validate + pull + process + report."""
    ctx.invoke(validate, skip_gee=True)
    ctx.invoke(pull)
    ctx.invoke(process)
    ctx.invoke(report)


@cli.command()
@click.pass_context
def setup(ctx):
    """Bootstrap a fresh clone: pull all data, process, and report.

    Runs: pull + Comtrade (if API key set) + process + report.
    Use this after cloning the repo to populate the data/ directory.
    """
    import os

    from src.shared.pipeline.freshness import record_pull
    console.print("[bold cyan]Setting up Corridor Intelligence Platform...[/bold cyan]\n")

    # 1. Pull non-GEE data (OSM, USGS, Pink Sheet)
    ctx.invoke(pull)

    # 2. Comtrade trade flows (optional — requires API key)
    console.rule("Comtrade Trade Flows")
    comtrade_key = os.environ.get("COMTRADE_API_KEY", "")
    if comtrade_key and not comtrade_key.startswith("your-"):
        try:
            from src.pipelines.trade_pipeline.comtrade import (
                get_bilateral_flows, save_trade_data, COMMODITY_HS_CODES,
            )

            total = 0
            for commodity in COMMODITY_HS_CODES:
                df = get_bilateral_flows(commodity)
                if not df.empty:
                    save_trade_data(df, f"trade_flows_{commodity}")
                    total += len(df)
            record_pull("trade_comtrade", total)
            console.print(f"[green]Comtrade: saved {total} trade flow records.[/green]")
        except Exception as exc:
            console.print(f"[red]Comtrade fetch failed: {exc}[/red]")
    else:
        console.print("[yellow]COMTRADE_API_KEY not set — skipping trade flows.[/yellow]")
        console.print("[dim]Set it in .env to fetch UN Comtrade data.[/dim]")

    # 3. Process all downloaded data
    ctx.invoke(process)

    # 4. Generate data availability report
    ctx.invoke(report)

    console.print("\n[bold green]Setup complete![/bold green]")
    console.print("Run [bold]python run_all.py serve[/bold] to start the API server.")


@cli.command()
@click.option("--force", is_flag=True, help="Re-pull everything regardless of age")
@click.pass_context
def refresh(ctx, force: bool):
    """Re-pull only stale data pipelines (or all with --force).

    Checks data/freshness.json and re-downloads any pipeline whose data
    is older than its staleness threshold.  Much faster than a full setup.
    """
    import os
    from src.shared.pipeline.freshness import (
        get_stale_pipelines, STALENESS_THRESHOLDS,
        load_freshness, age_days, record_pull,
    )

    stale = list(STALENESS_THRESHOLDS.keys()) if force else get_stale_pipelines()

    if not stale:
        console.print("[bold green]All data is fresh — nothing to refresh.[/bold green]")
        freshness = load_freshness()
        for name in STALENESS_THRESHOLDS:
            days = age_days(name)
            pulled = freshness.get(name, {}).get("pulled_at", "never")
            console.print(f"  {name:18s}  pulled {pulled}  ({days:.0f}d ago)" if days else f"  {name:18s}  never pulled")
        return

    console.print(f"[bold cyan]Refreshing {len(stale)} stale pipeline(s): {', '.join(stale)}[/bold cyan]\n")

    # OSM
    if "osm" in stale:
        console.rule("OSM Data")
        try:
            from src.pipelines.osm_pipeline.extractor import extract_all
            from src.pipelines.osm_pipeline.config import OSM_OUTPUT_FILES, OSM_DATA_DIR
            from src.shared.pipeline.utils import save_geojson, ensure_dir

            ensure_dir(OSM_DATA_DIR)
            results = extract_all()
            total_features = 0
            for name, geojson in results.items():
                path = OSM_OUTPUT_FILES.get(name)
                if path:
                    save_geojson(geojson, path)
                    total_features += len(geojson["features"])
            record_pull("osm", total_features)
            console.print(f"[green]OSM refreshed: {total_features} features.[/green]")
        except Exception as exc:
            console.print(f"[red]OSM refresh failed: {exc}[/red]")

    # USGS Minerals
    if "mineral" in stale:
        console.rule("USGS Minerals")
        try:
            from src.pipelines.mineral_pipeline.downloader import download_geodatabase
            from src.pipelines.mineral_pipeline.processor import process_geodatabase, export_all

            result = download_geodatabase()
            if result:
                results = process_geodatabase(result)
                export_all(results)
                total = sum(len(g.get("features", [])) for g in results.values())
                record_pull("mineral", total)
                console.print(f"[green]Minerals refreshed: {len(results)} layers, {total} features.[/green]")
        except Exception as exc:
            console.print(f"[red]Mineral refresh failed: {exc}[/red]")

    # World Bank
    if "worldbank" in stale:
        console.rule("World Bank Indicators")
        try:
            from src.pipelines.worldbank_pipeline.indicators import fetch_all_indicators, save_indicators
            data = fetch_all_indicators()
            total = sum(len(v) for v in data.values())
            save_indicators(data)
            record_pull("worldbank", total)
            console.print(f"[green]World Bank refreshed: {total} records.[/green]")
        except Exception as exc:
            console.print(f"[red]World Bank refresh failed: {exc}[/red]")

    # Energy
    if "energy" in stale:
        console.rule("Energy Data")
        try:
            from src.pipelines.energy_pipeline.downloader import download_power_plants
            from src.pipelines.energy_pipeline.processor import process_power_plants, export_power_plants
            csv_path = download_power_plants()
            geojson = process_power_plants(csv_path)
            export_power_plants(geojson)
            record_pull("energy", len(geojson["features"]))
            console.print(f"[green]Energy refreshed: {len(geojson['features'])} plants.[/green]")
        except Exception as exc:
            console.print(f"[red]Energy refresh failed: {exc}[/red]")

    # ACLED
    if "acled" in stale:
        console.rule("ACLED Conflict Data")
        try:
            from src.pipelines.acled_pipeline.fetcher import fetch_all_corridor_events, save_events
            events = fetch_all_corridor_events()
            save_events(events)
            record_pull("acled", len(events))
            console.print(f"[green]ACLED refreshed: {len(events)} events.[/green]")
        except Exception as exc:
            console.print(f"[red]ACLED refresh failed: {exc}[/red]")

    # Health facilities
    if "health" in stale:
        console.rule("Health Facilities")
        try:
            from src.pipelines.health_pipeline.downloader import download_all_countries
            from src.pipelines.health_pipeline.processor import facilities_to_geojson, save_health_facilities

            facilities = download_all_countries()
            geojson = facilities_to_geojson(facilities)
            save_health_facilities(geojson)
            record_pull("health", len(geojson["features"]))
            console.print(f"[green]Health refreshed: {len(geojson['features'])} facilities.[/green]")
        except Exception as exc:
            console.print(f"[red]Health refresh failed: {exc}[/red]")

    # Trade prices
    if "trade_prices" in stale:
        console.rule("Trade Prices")
        try:
            from src.pipelines.trade_pipeline.pinksheet import download_pinksheet, parse_pinksheet, save_prices
            path = download_pinksheet()
            df = parse_pinksheet(path)
            save_prices(df)
            record_pull("trade_prices", len(df))
            console.print(f"[green]Prices refreshed: {len(df)} records.[/green]")
        except Exception as exc:
            console.print(f"[red]Trade prices refresh failed: {exc}[/red]")

    # Comtrade
    if "trade_comtrade" in stale:
        console.rule("Comtrade Trade Flows")
        comtrade_key = os.environ.get("COMTRADE_API_KEY", "")
        if comtrade_key and not comtrade_key.startswith("your-"):
            try:
                from src.pipelines.trade_pipeline.comtrade import (
                    get_bilateral_flows, save_trade_data, COMMODITY_HS_CODES,
                )
                total = 0
                for commodity in COMMODITY_HS_CODES:
                    df = get_bilateral_flows(commodity)
                    if not df.empty:
                        save_trade_data(df, f"trade_flows_{commodity}")
                        total += len(df)
                record_pull("trade_comtrade", total)
                console.print(f"[green]Comtrade refreshed: {total} records.[/green]")
            except Exception as exc:
                console.print(f"[red]Comtrade refresh failed: {exc}[/red]")
        else:
            console.print("[yellow]COMTRADE_API_KEY not set — skipping.[/yellow]")

    # IMF WEO
    if "imf" in stale:
        console.rule("IMF WEO")
        try:
            from src.pipelines.imf_pipeline.fetcher import fetch_all_indicators as imf_fetch, save_indicators as imf_save
            data = imf_fetch()
            total = sum(len(v) for v in data.values())
            imf_save(data)
            record_pull("imf", total)
            console.print(f"[green]IMF refreshed: {total} records.[/green]")
        except Exception as exc:
            console.print(f"[red]IMF refresh failed: {exc}[/red]")

    # CPI
    if "cpi" in stale:
        console.rule("CPI")
        try:
            from src.pipelines.cpi_pipeline.fetcher import fetch_cpi_scores, save_cpi_scores
            scores = fetch_cpi_scores()
            save_cpi_scores(scores)
            record_pull("cpi", len(scores))
            console.print(f"[green]CPI refreshed: {len(scores)} scores.[/green]")
        except Exception as exc:
            console.print(f"[red]CPI refresh failed: {exc}[/red]")

    # V-Dem
    if "vdem" in stale:
        console.rule("V-Dem Governance")
        try:
            from src.pipelines.vdem_pipeline.fetcher import get_governance_indicators, save_governance
            data = get_governance_indicators()
            save_governance(data)
            record_pull("vdem", 5)
            console.print("[green]V-Dem refreshed.[/green]")
        except Exception as exc:
            console.print(f"[red]V-Dem refresh failed: {exc}[/red]")

    # GDL
    if "gdl" in stale:
        console.rule("Global Data Lab HDI")
        try:
            from src.pipelines.gdl_pipeline.fetcher import fetch_all_countries as gdl_fetch, save_subnational_hdi
            data = gdl_fetch()
            total = sum(len(v) for v in data.values()) if isinstance(data, dict) else len(data)
            save_subnational_hdi(data)
            record_pull("gdl", total)
            console.print(f"[green]GDL refreshed: {total} records.[/green]")
        except Exception as exc:
            console.print(f"[red]GDL refresh failed: {exc}[/red]")

    # FAO
    if "fao" in stale:
        console.rule("FAO Production")
        try:
            from src.pipelines.fao_pipeline.fetcher import fetch_all_commodities, save_production
            data = fetch_all_commodities()
            total = sum(len(v) for v in data.values())
            save_production(data)
            record_pull("fao", total)
            console.print(f"[green]FAO refreshed: {total} records.[/green]")
        except Exception as exc:
            console.print(f"[red]FAO refresh failed: {exc}[/red]")

    # AidData
    if "aiddata" in stale:
        console.rule("AidData")
        try:
            from src.pipelines.aiddata_pipeline.fetcher import fetch_corridor_projects, save_projects as aiddata_save
            projects = fetch_corridor_projects()
            aiddata_save(projects)
            record_pull("aiddata", len(projects))
            console.print(f"[green]AidData refreshed: {len(projects)} projects.[/green]")
        except Exception as exc:
            console.print(f"[red]AidData refresh failed: {exc}[/red]")

    # GEM
    if "gem" in stale:
        console.rule("Global Energy Monitor")
        try:
            from src.pipelines.gem_pipeline.fetcher import fetch_planned_projects, save_projects as gem_save
            projects = fetch_planned_projects()
            gem_save(projects)
            record_pull("gem", len(projects))
            console.print(f"[green]GEM refreshed: {len(projects)} projects.[/green]")
        except Exception as exc:
            console.print(f"[red]GEM refresh failed: {exc}[/red]")

    # UNCTAD
    if "unctad" in stale:
        console.rule("UNCTAD Ports")
        try:
            from src.pipelines.unctad_pipeline.fetcher import get_port_statistics, save_port_statistics
            ports = get_port_statistics()
            save_port_statistics(ports)
            record_pull("unctad", len(ports))
            console.print(f"[green]UNCTAD refreshed: {len(ports)} ports.[/green]")
        except Exception as exc:
            console.print(f"[red]UNCTAD refresh failed: {exc}[/red]")

    # energydata.info
    if "energydata" in stale:
        console.rule("energydata.info Grid")
        try:
            from src.pipelines.energydata_pipeline.fetcher import fetch_transmission_lines, fetch_substations, save_grid_data
            lines = fetch_transmission_lines()
            subs = fetch_substations()
            save_grid_data({"transmission_lines": lines, "substations": subs})
            record_pull("energydata", len(lines) + len(subs))
            console.print(f"[green]energydata.info refreshed: {len(lines)} lines + {len(subs)} subs.[/green]")
        except Exception as exc:
            console.print(f"[red]energydata.info refresh failed: {exc}[/red]")

    # PPI
    if "ppi" in stale:
        console.rule("IFC PPI")
        try:
            from src.pipelines.ppi_pipeline.fetcher import fetch_ppi_projects, save_ppi_projects
            projects = fetch_ppi_projects()
            save_ppi_projects(projects)
            record_pull("ppi", len(projects))
            console.print(f"[green]PPI refreshed: {len(projects)} projects.[/green]")
        except Exception as exc:
            console.print(f"[red]PPI refresh failed: {exc}[/red]")

    # GADM
    if "gadm" in stale:
        console.rule("GADM Boundaries")
        try:
            from src.pipelines.gadm_pipeline.fetcher import fetch_all_countries as gadm_fetch, save_boundaries
            data = gadm_fetch()
            n = len(data.get("features", []))
            save_boundaries(data)
            record_pull("gadm", n)
            console.print(f"[green]GADM refreshed: {n} regions.[/green]")
        except Exception as exc:
            console.print(f"[red]GADM refresh failed: {exc}[/red]")

    # WAPP
    if "wapp" in stale:
        console.rule("WAPP Master Plan")
        try:
            from src.pipelines.wapp_pipeline.fetcher import get_interconnections, get_generation_targets, get_trade_volumes, save_wapp_data
            data = {"interconnections": get_interconnections(), "generation_targets": get_generation_targets(), "trade_volumes": get_trade_volumes()}
            save_wapp_data(data)
            record_pull("wapp", len(data["interconnections"]))
            console.print(f"[green]WAPP refreshed.[/green]")
        except Exception as exc:
            console.print(f"[red]WAPP refresh failed: {exc}[/red]")

    # Re-process (road classification, value chains, etc.)
    console.rule("Re-processing")
    ctx.invoke(process)

    console.print("\n[bold green]Refresh complete.[/bold green]")


if __name__ == "__main__":
    cli()
