"""
Ookla Speedtest pipeline CLI runner.

Usage:
    python -m pipelines.connectivity_pipeline.pipeline pull
    python -m pipelines.connectivity_pipeline.pipeline process
"""

from __future__ import annotations

import click
from rich.console import Console

from src.shared.pipeline.utils import setup_logging, load_env

console = Console()


@click.group()
def cli():
    """Ookla Speedtest Open Data pipeline."""
    setup_logging()
    load_env()


@cli.command()
@click.option("--type", "network_type", default="mobile", help="Network type: mobile or fixed")
def pull(network_type: str):
    """Download Ookla Speedtest tiles."""
    from .downloader import download_ookla_tiles

    console.print(f"[bold cyan]Downloading Ookla {network_type} data...[/bold cyan]")
    path = download_ookla_tiles(network_type=network_type)
    if path:
        console.print(f"[bold green]Done: {path}[/bold green]")
    else:
        console.print("[yellow]Download failed. Manual download may be required.[/yellow]")


@cli.command()
@click.option("--type", "network_type", default="mobile", help="Network type: mobile or fixed")
def process(network_type: str):
    """Process Ookla Parquet data into corridor GeoJSON."""
    from .processor import process_speedtest_parquet, save_connectivity, get_connectivity_summary
    from .downloader import CONNECTIVITY_DATA_DIR

    parquet_path = CONNECTIVITY_DATA_DIR / f"speedtest_{network_type}.parquet"
    console.print(f"[bold cyan]Processing Ookla {network_type} data...[/bold cyan]")

    geojson = process_speedtest_parquet(parquet_path, network_type)
    save_connectivity(geojson, network_type)

    summary = get_connectivity_summary(geojson)
    console.print(f"  Tiles: {summary['total_tiles']}")
    console.print(f"  Avg download: {summary['avg_download_mbps']} Mbps")
    console.print(f"  Avg upload: {summary['avg_upload_mbps']} Mbps")
    console.print(f"  Avg latency: {summary['avg_latency_ms']} ms")
    console.print("[bold green]Done.[/bold green]")


if __name__ == "__main__":
    cli()
