"""Typer CLI — the main entry point for the finance-tracker tool."""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="finance-tracker", help="Self-hosted personal finance tracker.", add_completion=False)
console = Console()

_DEFAULT_DB = Path.home() / ".finance-tracker" / "finance.db"


def _get_db_path(db: Path | None) -> Path:
    path = db or _DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _build_deps(db_path: Path):
    from finance_tracker.application.detect_subscriptions import DetectSubscriptionsUseCase
    from finance_tracker.application.import_transactions import ImportTransactionsUseCase
    from finance_tracker.application.reporting import ReportingService
    from finance_tracker.infrastructure.database import (
        SqliteSubscriptionRepository,
        SqliteTransactionRepository,
    )
    from finance_tracker.infrastructure.ollama_client import OllamaCategoriser
    from finance_tracker.infrastructure.rule_engine import RuleBasedCategoriser

    tx_repo = SqliteTransactionRepository(db_path)
    sub_repo = SqliteSubscriptionRepository(db_path)
    rule_cat = RuleBasedCategoriser()
    categoriser = OllamaCategoriser(fallback=rule_cat)

    return {
        "tx_repo": tx_repo,
        "sub_repo": sub_repo,
        "import_uc": ImportTransactionsUseCase(tx_repo, categoriser),
        "detect_uc": DetectSubscriptionsUseCase(sub_repo),
        "reporting": ReportingService(tx_repo),
    }


@app.command()
def import_csv(
    file: Path = typer.Argument(..., help="Path to the CSV file to import"),
    db: Path = typer.Option(None, "--db", help="Path to the SQLite database"),
    date_col: str = typer.Option("date", "--date-col"),
    desc_col: str = typer.Option("description", "--desc-col"),
    amount_col: str = typer.Option("amount", "--amount-col"),
    currency_col: str = typer.Option("currency", "--currency-col"),
):
    """Import transactions from a CSV file."""
    from finance_tracker.infrastructure.csv_reader import CsvReader

    if not file.exists():
        console.print(f"[red]File not found:[/red] {file}")
        raise typer.Exit(1)

    db_path = _get_db_path(db)
    deps = _build_deps(db_path)

    column_map = {"date": date_col, "description": desc_col, "amount": amount_col, "currency": currency_col}
    reader = CsvReader(column_map)
    transactions, errors = reader.read(file)

    if errors:
        console.print(f"[yellow]Parse warnings ({len(errors)}):[/yellow]")
        for e in errors:
            console.print(f"  {e}")

    result = deps["import_uc"].execute(transactions)
    console.print(f"[green]Imported:[/green] {result.imported}  [dim]Skipped (duplicates): {result.skipped}[/dim]")

    # Auto-detect subscriptions after import
    all_txs = deps["tx_repo"].find_all()
    subs = deps["detect_uc"].execute(all_txs)
    if subs:
        console.print(f"[blue]Subscriptions detected:[/blue] {len(subs)}")


@app.command()
def summary(
    year: int = typer.Option(None, "--year", "-y"),
    month: int = typer.Option(None, "--month", "-m"),
    db: Path = typer.Option(None, "--db"),
):
    """Show a monthly spending summary."""
    from datetime import date

    db_path = _get_db_path(db)
    deps = _build_deps(db_path)
    reporting = deps["reporting"]

    if year and month:
        summaries = [reporting.monthly_summary(year, month)]
    else:
        summaries = reporting.all_monthly_summaries()
        if not summaries:
            console.print("[yellow]No transactions found. Import a CSV first.[/yellow]")
            return

    for s in summaries:
        console.rule(f"[bold]{s.year}-{s.month:02d}[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Category")
        table.add_column("Amount", justify="right")
        for cat, amount in sorted(s.totals.items(), key=lambda x: x[1], reverse=True):
            table.add_row(cat, f"£{amount:.2f}")
        table.add_row("[bold]Total Spent[/bold]", f"[bold]£{s.total_spent:.2f}[/bold]")
        table.add_row("[green]Income[/green]", f"[green]£{s.total_income:.2f}[/green]")
        table.add_row("[cyan]Net[/cyan]", f"[cyan]£{s.net:.2f}[/cyan]")
        console.print(table)


@app.command()
def subscriptions(db: Path = typer.Option(None, "--db")):
    """List all detected subscriptions."""
    db_path = _get_db_path(db)
    deps = _build_deps(db_path)
    subs = deps["sub_repo"].find_all()

    if not subs:
        console.print("[yellow]No subscriptions detected yet. Run import first.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Merchant")
    table.add_column("Amount", justify="right")
    table.add_column("Frequency")
    table.add_column("Annual Cost", justify="right")
    table.add_column("Next Charge")
    table.add_column("Price Rise?")

    for s in sorted(subs, key=lambda x: x.annual_cost, reverse=True):
        price_flag = "[red]YES[/red]" if s.had_price_increase else ""
        table.add_row(
            s.merchant,
            f"£{s.amount:.2f}",
            s.frequency.value,
            f"£{s.annual_cost:.2f}",
            str(s.next_charge_date or "—"),
            price_flag,
        )

    console.print(table)
    total_annual = sum(s.annual_cost for s in subs)
    console.print(f"\n[bold]Total annual subscription spend:[/bold] £{total_annual:.2f}")


@app.command()
def serve(
    db: Path = typer.Option(None, "--db"),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
):
    """Start the web dashboard."""
    import uvicorn
    from finance_tracker.presentation.web.app import create_app

    db_path = _get_db_path(db)
    web_app = create_app(db_path)
    console.print(f"[green]Dashboard running at[/green] http://{host}:{port}")
    uvicorn.run(web_app, host=host, port=port)
