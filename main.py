import asyncio
import os
from typing import Optional
from pathlib import Path

import typer
from rich import print as rprint
from rich.table import Table
from rich.panel import Panel

from scrapers.books_scraper import BooksScraper
from scrapers.generic_scraper import GenericScraper
from scrapers.amazon_scraper import AmazonScraper
from scrapers.base_scraper import ScrapeError
from exporters.csv_exporter import CSVExporter
from exporters.json_exporter import JSONExporter
from exporters.excel_exporter import ExcelExporter
from utils.logger import setup_logger, console

app = typer.Typer(
    name="dataminer",
    help="A professional web scraping toolkit for e-commerce product data.",
    rich_markup_mode="rich",
)

logger = setup_logger()

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def _export(products, prefix: str = "products", currency: str = "USD"):
    base = OUTPUT_DIR / prefix
    files = {}

    csv_path = f"{base}.csv"
    CSVExporter().export(products, csv_path)
    files["CSV"] = csv_path

    json_path = f"{base}.json"
    JSONExporter().export(products, json_path)
    files["JSON"] = json_path

    xlsx_path = f"{base}.xlsx"
    ExcelExporter(currency=currency).export(products, xlsx_path)
    files["Excel"] = xlsx_path

    return files


def _show_results(products):
    table = Table(title=f"Scraped {len(products)} Products", title_style="bold blue")
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", width=50)
    table.add_column("Price", justify="right", width=12)
    table.add_column("Rating", justify="center", width=8)
    table.add_column("Availability", width=14)

    for i, p in enumerate(products[:20], 1):
        name = (p.name[:60] + "...") if len(p.name) > 60 else p.name
        rating = f"{p.rating:.1f}" if p.rating is not None else "—"
        table.add_row(str(i), name, p.formatted_price, rating, p.availability)

    if len(products) > 20:
        table.add_row(
            "...", f"... and {len(products) - 20} more", "", "", ""
        )

    console.print(table)


def _print_file_summary(files: dict):
    console.print()
    rprint(Panel.fit(
        "[bold green]> Export Complete[/bold green]\n"
        + "\n".join(f"  - [cyan]{fmt}[/cyan]: {path}" for fmt, path in files.items()),
        title="Output Files",
        border_style="green",
    ))


@app.command()
def books(
    pages: int = typer.Option(1, "--pages", "-p", help="Number of pages to scrape"),
    currency: str = typer.Option("GBP", "--currency", "-c", help="Currency code"),
):
    """Scrape product data from books.toscrape.com"""
    with console.status("[bold blue]Scraping books...") as _:
        scraper = BooksScraper()
        try:
            products = asyncio.run(scraper.scrape(max_pages=pages))
        except Exception as e:
            rprint(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(1)

    if not products:
        rprint("[yellow]No products found.[/yellow]")
        raise typer.Exit()

    _show_results(products)
    files = _export(products, prefix="books", currency=currency)
    _print_file_summary(files)


@app.command()
def generic(
    url: str = typer.Argument(..., help="URL of the e-commerce page to scrape"),
    currency: str = typer.Option("USD", "--currency", "-c", help="Currency code"),
):
    """Scrape products from any generic e-commerce page using Playwright"""
    with console.status("[bold blue]Launching browser and scraping...") as _:
        scraper = GenericScraper(url)
        try:
            products = asyncio.run(scraper.scrape())
        except ScrapeError as e:
            rprint(f"[bold red]Scrape Error:[/bold red] {e}")
            raise typer.Exit(1)
        except Exception as e:
            rprint(f"[bold red]Unexpected Error:[/bold red] {e}")
            raise typer.Exit(1)

    if not products:
        rprint("[yellow]No products found at the given URL.[/yellow]")
        raise typer.Exit()

    _show_results(products)
    files = _export(products, prefix="generic", currency=currency)
    _print_file_summary(files)


@app.command()
def amazon(
    search: str = typer.Argument(..., help="Search term for Amazon products"),
    currency: str = typer.Option("USD", "--currency", "-c", help="Currency code"),
):
    """Scrape Amazon search results (template — requires proxy/API)"""
    scraper = AmazonScraper(search)
    try:
        products = asyncio.run(scraper.scrape())
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

    if not products:
        rprint(
            "[yellow]Amazon scraping requires a proxy service or API. "
            "See scrapers/amazon_scraper.py for details.[/yellow]"
        )
        raise typer.Exit()

    _show_results(products)
    files = _export(products, prefix="amazon", currency=currency)
    _print_file_summary(files)


@app.command()
def info():
    """Display project information"""
    rprint(Panel.fit(
        "[bold]DataMiner[/bold] v0.1.0\n"
        "A professional web scraping toolkit for e-commerce product data.\n\n"
        "[bold]Commands:[/bold]\n"
        "  [cyan]books[/cyan]     Scrape books.toscrape.com\n"
        "  [cyan]generic[/cyan]   Scrape any e-commerce page via Playwright\n"
        "  [cyan]amazon[/cyan]    Amazon search (template)\n\n"
        "[bold]Output:[/bold] CSV, JSON, and professionally formatted Excel files.",
        title="DataMiner",
        border_style="blue",
    ))


if __name__ == "__main__":
    app()
