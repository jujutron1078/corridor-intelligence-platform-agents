"""
Trade & commodity data pipeline CLI runner.

Commands:
    python -m trade_pipeline.pipeline pull-trade     Pull UN Comtrade data
    python -m trade_pipeline.pipeline pull-prices     Download Pink Sheet
    python -m trade_pipeline.pipeline compute-gaps    Compute value-chain gaps
"""

from __future__ import annotations

import logging

import click
from rich.console import Console
from rich.table import Table

from src.shared.pipeline.utils import setup_logging

console = Console()
logger = logging.getLogger("corridor.trade.pipeline")


@click.group()
def cli():
    """Lagos-Abidjan Corridor Trade & Commodity Pipeline."""
    setup_logging()


@cli.command("pull-trade")
@click.option("--commodity", default=None, help="Specific commodity (cocoa, gold, oil, etc.) or all")
def pull_trade(commodity: str | None):
    """Pull bilateral trade flows from UN Comtrade."""
    from .comtrade import get_bilateral_flows, save_trade_data, COMMODITY_HS_CODES

    commodities = [commodity] if commodity else list(COMMODITY_HS_CODES.keys())

    for comm in commodities:
        console.print(f"[cyan]Pulling trade data for {comm}...[/cyan]")
        try:
            df = get_bilateral_flows(comm)
            if not df.empty:
                save_trade_data(df, f"trade_flows_{comm}")
                console.print(f"  [green]{len(df)} records saved[/green]")
            else:
                console.print(f"  [yellow]No data returned[/yellow]")
        except Exception as exc:
            console.print(f"  [red]Failed: {exc}[/red]")

    console.print("[bold green]Trade data pull complete.[/bold green]")


@cli.command("pull-prices")
@click.option("--force", is_flag=True, help="Force re-download")
def pull_prices(force: bool):
    """Download World Bank Pink Sheet commodity prices."""
    from .pinksheet import download_pinksheet, parse_pinksheet, save_prices

    console.print("[cyan]Downloading World Bank Pink Sheet...[/cyan]")
    try:
        path = download_pinksheet(force=force)
        console.print(f"  Downloaded: {path}")

        console.print("[cyan]Parsing prices...[/cyan]")
        df = parse_pinksheet(path)
        save_prices(df)

        if not df.empty:
            table = Table(title="Commodity Prices Summary")
            table.add_column("Commodity", style="cyan")
            table.add_column("Records", justify="right")
            table.add_column("Date Range")

            for comm in df["commodity"].unique():
                sub = df[df["commodity"] == comm]
                date_range = f"{sub['date'].min():%Y-%m} to {sub['date'].max():%Y-%m}"
                table.add_row(comm, str(len(sub)), date_range)

            console.print(table)
        else:
            console.print("[yellow]No price data parsed[/yellow]")

    except Exception as exc:
        console.print(f"[red]Failed: {exc}[/red]")


@cli.command("compute-gaps")
def compute_gaps():
    """Compute value-chain gaps for all commodities."""
    from .value_chain import compute_all_value_chains, save_value_chain_report

    console.print("[cyan]Computing value-chain gaps...[/cyan]")
    results = compute_all_value_chains()
    save_value_chain_report(results)

    table = Table(title="Value-Chain Gap Analysis")
    table.add_column("Commodity", style="cyan")
    table.add_column("Raw Product")
    table.add_column("Processed Product")
    table.add_column("Multiplier", justify="right")
    table.add_column("Raw Price", justify="right")
    table.add_column("Processed Price", justify="right")

    for commodity, data in results.items():
        raw_p = f"${data['raw_price']:,.0f}" if data.get("raw_price") else "N/A"
        proc_p = f"${data['processed_price']:,.0f}" if data.get("processed_price") else "N/A"
        table.add_row(
            commodity,
            data["raw_product"],
            data["processed_product"],
            f"{data['multiplier']:.1f}x",
            raw_p,
            proc_p,
        )

    console.print(table)

    # Show country gaps for key commodities
    for commodity in ["cocoa", "oil", "bauxite"]:
        if commodity not in results:
            continue
        gaps = results[commodity]["gaps_by_country"]
        gap_table = Table(title=f"{commodity.title()} Processing Gaps by Country")
        gap_table.add_column("Country", style="cyan")
        gap_table.add_column("Role")
        gap_table.add_column("Processing %", justify="right")
        gap_table.add_column("Missed Value %", justify="right")
        gap_table.add_column("Notes")

        for iso3, gap in gaps.items():
            gap_table.add_row(
                gap["country_name"],
                gap["role"],
                f"{gap['processing_pct']}%",
                f"{gap['missed_value_pct']}%",
                gap["notes"],
            )
        console.print(gap_table)

    console.print("[bold green]Value-chain analysis complete.[/bold green]")


if __name__ == "__main__":
    cli()
