"""
USGS mineral pipeline CLI runner.

Commands:
    python -m mineral_pipeline.pipeline download    Download geodatabase
    python -m mineral_pipeline.pipeline process     Parse and filter
    python -m mineral_pipeline.pipeline export      Save as GeoJSON
"""

from __future__ import annotations

import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from src.shared.pipeline.utils import setup_logging, DATA_DIR

console = Console()
logger = logging.getLogger("corridor.mineral.pipeline")

MINERAL_DATA_DIR = DATA_DIR / "mineral"
GDB_DIR = MINERAL_DATA_DIR / "geodatabase"


def _find_gdb() -> Path | None:
    """Find the .gdb directory in the mineral data folder."""
    if not GDB_DIR.exists():
        return None
    for item in GDB_DIR.rglob("*.gdb"):
        if item.is_dir():
            return item
    return None


@click.group()
def cli():
    """Lagos-Abidjan Corridor USGS Mineral Pipeline."""
    setup_logging()


@cli.command()
def download():
    """Download the USGS Africa mineral geodatabase from ScienceBase."""
    from .downloader import download_geodatabase

    console.print("[bold cyan]Downloading USGS mineral geodatabase...[/bold cyan]")
    result = download_geodatabase()

    if result:
        console.print(f"[bold green]Download complete: {result}[/bold green]")
    else:
        console.print("[bold red]Download failed. Check logs for details.[/bold red]")


@cli.command()
def process():
    """Process the downloaded geodatabase — filter to AOI, classify, export."""
    from .processor import process_geodatabase, export_all, list_gdb_layers

    gdb_path = _find_gdb()
    if not gdb_path:
        console.print("[red]No .gdb found. Run 'download' first.[/red]")
        return

    console.print(f"[bold cyan]Processing geodatabase: {gdb_path}[/bold cyan]")

    # List layers
    layers = list_gdb_layers(gdb_path)
    console.print(f"  Found {len(layers)} layers: {', '.join(layers[:10])}{'...' if len(layers) > 10 else ''}")

    # Process
    results = process_geodatabase(gdb_path)

    # Export
    export_all(results)

    # Summary
    table = Table(title="Processed Mineral Layers")
    table.add_column("Layer", style="cyan")
    table.add_column("Features", justify="right")

    for name, geojson in results.items():
        table.add_row(name, str(len(geojson.get("features", []))))

    console.print(table)
    console.print(f"[bold green]Processed {len(results)} layers.[/bold green]")


@cli.command()
def export():
    """Re-export processed data as GeoJSON."""
    process.invoke(click.Context(process))


if __name__ == "__main__":
    cli()
