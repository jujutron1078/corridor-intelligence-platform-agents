"""
ACLED conflict data pipeline CLI runner.

Usage:
    python -m pipelines.acled_pipeline.pipeline pull
    python -m pipelines.acled_pipeline.pipeline pull --start-year 2020 --end-year 2024
"""

from __future__ import annotations

import click
from rich.console import Console

from src.shared.pipeline.utils import setup_logging, load_env

console = Console()


@click.group()
def cli():
    """ACLED conflict data pipeline."""
    setup_logging()
    load_env()


@cli.command()
@click.option("--start-year", default=2020, help="Start year")
@click.option("--end-year", default=2024, help="End year")
def pull(start_year: int, end_year: int):
    """Fetch ACLED conflict events for corridor countries."""
    from .fetcher import fetch_all_corridor_events, save_events

    console.print(f"[bold cyan]Fetching ACLED conflict events ({start_year}-{end_year})...[/bold cyan]\n")

    events = fetch_all_corridor_events(start_year=start_year, end_year=end_year)
    path = save_events(events)

    console.print(f"\n[bold green]Done: {len(events)} events saved to {path}[/bold green]")


if __name__ == "__main__":
    cli()
