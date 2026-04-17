"""
FAO Livestock pipeline CLI runner.

Usage:
    python -m pipelines.livestock_pipeline.pipeline pull
    python -m pipelines.livestock_pipeline.pipeline process
"""

from __future__ import annotations

import click
from rich.console import Console

from src.shared.pipeline.utils import setup_logging, load_env

console = Console()


@click.group()
def cli():
    """FAO Gridded Livestock pipeline."""
    setup_logging()
    load_env()


@cli.command()
@click.option("--species", default=None, help="Download a specific species: cattle, goats, sheep, chickens, pigs")
def pull(species: str | None):
    """Download FAO GLW 3 livestock GeoTIFFs."""
    from .downloader import download_all, download_species, SPECIES_URLS

    if species:
        url = SPECIES_URLS.get(species)
        if not url:
            console.print(f"[red]Unknown species: {species}. Available: {list(SPECIES_URLS.keys())}[/red]")
            return
        console.print(f"[bold cyan]Downloading {species}...[/bold cyan]")
        download_species(species, url)
    else:
        console.print("[bold cyan]Downloading all livestock species...[/bold cyan]")
        results = download_all()
        console.print(f"[bold green]Downloaded {len(results)} species.[/bold green]")


@cli.command()
def process():
    """Extract corridor livestock statistics from GeoTIFFs."""
    from .processor import extract_corridor_stats, save_stats

    console.print("[bold cyan]Processing livestock data...[/bold cyan]")
    stats = extract_corridor_stats()
    save_stats(stats)

    for species, data in stats.items():
        if "error" not in data:
            console.print(f"  {species}: {data.get('total_heads', 0):,.0f} heads")
    console.print("[bold green]Done.[/bold green]")


if __name__ == "__main__":
    cli()
