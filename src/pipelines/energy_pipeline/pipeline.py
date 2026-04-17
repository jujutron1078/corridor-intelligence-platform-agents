"""
Energy pipeline CLI runner.

Usage:
    python -m pipelines.energy_pipeline.pipeline pull
    python -m pipelines.energy_pipeline.pipeline process
"""

from __future__ import annotations

import click
from rich.console import Console

from src.shared.pipeline.utils import setup_logging, load_env

console = Console()


@click.group()
def cli():
    """Global Energy Monitor pipeline."""
    setup_logging()
    load_env()


@cli.command()
def pull():
    """Download the Global Power Plant Database."""
    from .downloader import download_power_plants

    console.print("[bold cyan]Downloading power plant data...[/bold cyan]")
    path = download_power_plants()
    console.print(f"[bold green]Done: {path}[/bold green]")


@cli.command()
def process():
    """Process power plant data into corridor GeoJSON."""
    from .processor import process_power_plants, export_power_plants, get_energy_summary

    console.print("[bold cyan]Processing power plant data...[/bold cyan]")
    geojson = process_power_plants()
    export_power_plants(geojson)

    summary = get_energy_summary(geojson)
    console.print(f"  Plants: {summary['total_plants']}")
    console.print(f"  Total capacity: {summary['total_capacity_mw']} MW")
    for fuel, stats in summary["by_fuel"].items():
        console.print(f"    {fuel}: {stats['count']} plants, {stats['capacity_mw']:.0f} MW")

    console.print("[bold green]Done.[/bold green]")


if __name__ == "__main__":
    cli()
