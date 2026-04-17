"""
GEE pipeline CLI runner.

Commands:
    python -m gee_pipeline.pipeline --validate    Check all 13 datasets
    python -m gee_pipeline.pipeline --export      Export static layers
    python -m gee_pipeline.pipeline --test        Sample data at key cities
"""

from __future__ import annotations

import json
import logging
import sys

import click
from rich.console import Console
from rich.table import Table

from src.shared.pipeline.utils import setup_logging, load_env, get_env
from .config import DATASET_CATALOG, TEST_POINTS

console = Console()
logger = logging.getLogger("corridor.gee.pipeline")


def _get_api():
    """Lazy-init the CorridorDataAPI."""
    from .accessor import CorridorDataAPI
    load_env()
    project = get_env("GEE_PROJECT")
    return CorridorDataAPI(project=project)


@click.group()
def cli():
    """Lagos-Abidjan Corridor GEE Pipeline."""
    setup_logging()


@cli.command()
def validate():
    """Check all 13 GEE datasets are accessible within the corridor AOI."""
    api = _get_api()

    table = Table(title="GEE Dataset Validation")
    table.add_column("Dataset", style="cyan")
    table.add_column("Collection ID", style="dim")
    table.add_column("Tier", justify="center")
    table.add_column("Status", justify="center")
    table.add_column("Count / Info")

    passed = 0
    failed = 0

    for name, info in DATASET_CATALOG.items():
        result = api.validate_dataset(name, info["collection"])
        if result["accessible"]:
            status = "[green]OK[/green]"
            passed += 1
        else:
            status = "[red]FAIL[/red]"
            failed += 1

        table.add_row(
            name,
            info["collection"],
            str(info["tier"]),
            status,
            str(result["count"]) if result["accessible"] else result["error"][:60],
        )

    console.print(table)
    console.print(f"\n[green]{passed} passed[/green], [red]{failed} failed[/red] of {len(DATASET_CATALOG)} datasets")

    if failed > 0:
        sys.exit(1)


@cli.command("export-static")
def export_static():
    """Export static layers to Google Drive as GEE assets."""
    api = _get_api()

    static_layers = [
        ("worldcover", api.worldcover()),
        ("elevation", api.elevation()),
        ("surface_water", api.surface_water()),
        ("hansen_forest", api.hansen_forest()),
        ("building_density", api.building_density()),
    ]

    for name, image in static_layers:
        console.print(f"Exporting {name}...", style="cyan")
        try:
            task = api.export_to_drive(image, description=f"corridor_{name}", scale=100)
            console.print(f"  Task started: {task.status()}", style="green")
        except Exception as exc:
            console.print(f"  Failed: {exc}", style="red")


@cli.command()
@click.option("--year", default=2023, help="Year for temporal data")
@click.option("--month", default=6, help="Month for temporal data")
def test(year: int, month: int):
    """Sample data at 6 key corridor cities and print values."""
    api = _get_api()

    table = Table(title=f"Corridor Data Sample ({year}-{month:02d})")
    table.add_column("City", style="cyan")
    table.add_column("Lon", justify="right")
    table.add_column("Lat", justify="right")
    table.add_column("NDVI", justify="right")
    table.add_column("Nightlights", justify="right")
    table.add_column("Elevation", justify="right")
    table.add_column("Population", justify="right")
    table.add_column("Landcover")
    table.add_column("Econ Index", justify="right")

    for city, (lon, lat) in TEST_POINTS.items():
        console.print(f"Sampling {city} ({lon}, {lat})...", style="dim")
        try:
            data = api.sample_at_point(lon, lat, year, month)
            table.add_row(
                city,
                f"{lon:.2f}",
                f"{lat:.2f}",
                f"{data.get('NDVI', 'N/A'):.3f}" if isinstance(data.get("NDVI"), (int, float)) else "N/A",
                f"{data.get('nightlights', 'N/A'):.1f}" if isinstance(data.get("nightlights"), (int, float)) else "N/A",
                f"{data.get('elevation', 'N/A'):.0f}" if isinstance(data.get("elevation"), (int, float)) else "N/A",
                f"{data.get('population', 'N/A'):.0f}" if isinstance(data.get("population"), (int, float)) else "N/A",
                data.get("landcover_name", "N/A"),
                f"{data.get('economic_index', 'N/A'):.3f}" if isinstance(data.get("economic_index"), (int, float)) else "N/A",
            )
        except Exception as exc:
            table.add_row(city, f"{lon:.2f}", f"{lat:.2f}", *["ERROR"] * 6)
            logger.error("Failed to sample %s: %s", city, exc)

    console.print(table)


if __name__ == "__main__":
    cli()
