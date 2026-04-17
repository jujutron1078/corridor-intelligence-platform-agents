"""
Health Facilities pipeline CLI runner.

Usage:
    python -m pipelines.health_pipeline.pipeline pull
"""

from __future__ import annotations

import click
from rich.console import Console

from src.shared.pipeline.utils import setup_logging, load_env

console = Console()


@click.group()
def cli():
    """HDX Health Facilities pipeline."""
    setup_logging()
    load_env()


@cli.command()
def pull():
    """Download health facilities from healthsites.io API."""
    from .downloader import download_all_countries
    from .processor import facilities_to_geojson, save_health_facilities

    console.print("[bold cyan]Downloading health facilities for corridor countries...[/bold cyan]\n")

    all_facilities = download_all_countries()
    total = sum(len(v) for v in all_facilities.values())
    console.print(f"\nFetched {total} facilities total.")

    geojson = facilities_to_geojson(all_facilities)
    path = save_health_facilities(geojson)

    console.print(f"\n[bold green]Done: {len(geojson['features'])} facilities saved to {path}[/bold green]")


if __name__ == "__main__":
    cli()
