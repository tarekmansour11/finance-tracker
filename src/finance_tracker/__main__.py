"""CLI entry point for finance-tracker."""

import typer

app = typer.Typer(
    name="finance-tracker",
    help="Self-hosted personal finance tracker.",
    add_completion=False,
)


@app.command()
def version():
    """Print the current version."""
    from finance_tracker import __version__

    typer.echo(f"finance-tracker v{__version__}")


@app.command()
def import_transactions(
    file: str = typer.Argument(..., help="Path to the transaction CSV file"),
):
    """Import transactions from a CSV export.

    TODO: implement importers for Monzo, Starling, HSBC formats.
    """
    typer.echo(f"[TODO] Import transactions from: {file}")


@app.command()
def summary(
    month: str = typer.Option(None, "--month", "-m", help="Month to summarise (YYYY-MM)"),
):
    """Show a spending summary for the given month.

    TODO: implement spending summary grouped by category.
    """
    typer.echo(f"[TODO] Show summary for: {month or 'current month'}")


if __name__ == "__main__":
    app()
