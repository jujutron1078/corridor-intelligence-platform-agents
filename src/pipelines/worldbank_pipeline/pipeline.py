"""
World Bank pipeline CLI runner.

Usage:
    python -m pipelines.worldbank_pipeline.pipeline pull
    python -m pipelines.worldbank_pipeline.pipeline pull --start-year 2015
"""

from __future__ import annotations

import click
from rich.console import Console

from src.shared.pipeline.utils import setup_logging, load_env

console = Console()


@click.group()
def cli():
    """World Bank Open Data pipeline."""
    setup_logging()
    load_env()


@cli.command()
@click.option("--start-year", default=2010, help="Start year for data fetch")
@click.option("--end-year", default=2024, help="End year for data fetch")
def pull(start_year: int, end_year: int):
    """Fetch all World Bank indicators for corridor countries."""
    from .indicators import fetch_all_indicators, save_indicators, INDICATORS

    console.print(f"[bold cyan]Fetching {len(INDICATORS)} World Bank indicators ({start_year}-{end_year})...[/bold cyan]\n")

    data = fetch_all_indicators(start_year=start_year, end_year=end_year)

    total_records = sum(len(v) for v in data.values())
    path = save_indicators(data)

    console.print(f"\n[bold green]Done: {total_records} records saved to {path}[/bold green]")


if __name__ == "__main__":
    cli()
