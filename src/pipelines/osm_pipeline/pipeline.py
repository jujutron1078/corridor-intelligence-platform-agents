"""
OSM pipeline CLI runner.

Commands:
    python -m osm_pipeline.pipeline extract    Pull all data from Overpass
    python -m osm_pipeline.pipeline process    Build network graph
    python -m osm_pipeline.pipeline validate   Check data completeness
    python -m osm_pipeline.pipeline export     Save GeoJSON files
"""

from __future__ import annotations

import json
import logging

import click
from rich.console import Console
from rich.table import Table

from src.shared.pipeline.utils import setup_logging, save_geojson, ensure_dir
from .config import OSM_DATA_DIR, OSM_OUTPUT_FILES

console = Console()
logger = logging.getLogger("corridor.osm.pipeline")


@click.group()
def cli():
    """Lagos-Abidjan Corridor OSM Pipeline."""
    setup_logging()


@cli.command()
def extract():
    """Pull all OSM data from the Overpass API."""
    from .extractor import extract_all

    console.print("[bold cyan]Extracting OSM data for Lagos-Abidjan corridor...[/bold cyan]")
    results = extract_all()

    ensure_dir(OSM_DATA_DIR)
    for name, geojson in results.items():
        path = OSM_OUTPUT_FILES.get(name)
        if path:
            save_geojson(geojson, path)
            console.print(f"  {name}: {len(geojson['features'])} features -> {path.name}")

    console.print("[bold green]Extraction complete.[/bold green]")


@cli.command()
def process():
    """Process extracted roads into a network graph."""
    from src.shared.pipeline.utils import load_geojson
    from .processor import classify_roads, build_network_graph, find_pinch_points, generate_network_report

    roads_path = OSM_OUTPUT_FILES["roads"]
    if not roads_path.exists():
        console.print("[red]Roads data not found. Run 'extract' first.[/red]")
        return

    console.print("[bold cyan]Processing road network...[/bold cyan]")
    roads = load_geojson(roads_path)

    # Classify
    roads = classify_roads(roads)
    save_geojson(roads, roads_path)
    console.print(f"  Classified {len(roads['features'])} road segments")

    # Build graph
    G = build_network_graph(roads)
    pinch_points = find_pinch_points(G)

    # Generate report
    report = generate_network_report(roads, G, pinch_points)
    report_path = OSM_OUTPUT_FILES["network"]
    ensure_dir(report_path.parent)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    # Display results
    stats = report["network_stats"]
    table = Table(title="Road Network Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Total segments", f"{stats['total_edges']:,}")
    table.add_row("Total intersections", f"{stats['total_nodes']:,}")
    table.add_row("Total km", f"{stats['total_km']:,.1f}")
    table.add_row("Connected components", str(stats["connected_components"]))

    for tier_key, km in stats["km_by_tier"].items():
        table.add_row(f"  {tier_key}", f"{km:,.1f} km")

    table.add_row("Pinch points found", str(len(pinch_points)))
    console.print(table)

    if pinch_points:
        pp_table = Table(title="Top Pinch Points")
        pp_table.add_column("Location")
        pp_table.add_column("Nearest Node")
        pp_table.add_column("Degree", justify="right")
        pp_table.add_column("Distance (km)", justify="right")
        for pp in pinch_points[:10]:
            pp_table.add_row(
                f"({pp['lon']:.4f}, {pp['lat']:.4f})",
                pp["nearest_node"],
                str(pp["degree"]),
                f"{pp['distance_km']:.1f}",
            )
        console.print(pp_table)


@cli.command()
def validate():
    """Check completeness of extracted OSM data."""
    table = Table(title="OSM Data Validation")
    table.add_column("Layer", style="cyan")
    table.add_column("File", style="dim")
    table.add_column("Status")
    table.add_column("Features", justify="right")

    for name, path in OSM_OUTPUT_FILES.items():
        if name == "network":
            continue
        if path.exists():
            try:
                from src.shared.pipeline.utils import load_geojson
                data = load_geojson(path)
                count = len(data.get("features", []))
                status = "[green]OK[/green]" if count > 0 else "[yellow]EMPTY[/yellow]"
                table.add_row(name, path.name, status, str(count))
            except Exception as exc:
                table.add_row(name, path.name, "[red]ERROR[/red]", str(exc)[:40])
        else:
            table.add_row(name, path.name, "[red]MISSING[/red]", "—")

    console.print(table)


@cli.command()
def export():
    """Re-export all GeoJSON files (after processing)."""
    console.print("All GeoJSON files are already saved in:", str(OSM_DATA_DIR))
    validate.invoke(click.Context(validate))


if __name__ == "__main__":
    cli()
