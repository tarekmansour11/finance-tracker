"""FastAPI web application — serves the HTML dashboard."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from finance_tracker.application.reporting import ReportingService
from finance_tracker.infrastructure.database import (
    SqliteSubscriptionRepository,
    SqliteTransactionRepository,
)

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def create_app(db_path: Path) -> FastAPI:
    app = FastAPI(title="finance-tracker", docs_url=None, redoc_url=None)
    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

    tx_repo = SqliteTransactionRepository(db_path)
    sub_repo = SqliteSubscriptionRepository(db_path)
    reporting = ReportingService(tx_repo)

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        today = date.today()
        return _month_view(request, templates, today.year, today.month, tx_repo, sub_repo, reporting)

    @app.get("/month/{year}/{month}", response_class=HTMLResponse)
    def month(request: Request, year: int, month: int):
        return _month_view(request, templates, year, month, tx_repo, sub_repo, reporting)

    @app.get("/transactions", response_class=HTMLResponse)
    def transactions(request: Request, category: str = "", search: str = ""):
        all_txs = tx_repo.find_all()
        if category:
            all_txs = [t for t in all_txs if (t.category or "") == category]
        if search:
            all_txs = [t for t in all_txs if search.lower() in t.description.lower()]
        categories = sorted({t.category or "Uncategorised" for t in tx_repo.find_all()})
        return templates.TemplateResponse(request, "transactions.html", {
            "transactions": all_txs,
            "categories": categories,
            "selected_category": category,
            "search": search,
        })

    @app.get("/subscriptions", response_class=HTMLResponse)
    def subscriptions_view(request: Request):
        subs = sorted(sub_repo.find_all(), key=lambda s: s.annual_cost, reverse=True)
        total_annual = sum(s.annual_cost for s in subs)
        return templates.TemplateResponse(request, "subscriptions.html", {
            "subscriptions": subs,
            "total_annual": total_annual,
        })

    return app


def _month_view(request, templates, year, month, tx_repo, sub_repo, reporting):
    summary = reporting.monthly_summary(year, month)
    all_summaries = reporting.all_monthly_summaries()
    recent_txs = [t for t in tx_repo.find_by_month(year, month)][:20]
    subs = sub_repo.find_all()

    # Build chart data
    category_labels = list(summary.totals.keys())
    category_values = [float(v) for v in summary.totals.values()]

    month_labels = [f"{s.year}-{s.month:02d}" for s in all_summaries]
    month_totals = [float(s.total_spent) for s in all_summaries]
    month_incomes = [float(s.total_income) for s in all_summaries]

    today = date.today()
    prev_month = month - 1 or 12
    prev_year = year if month > 1 else year - 1
    next_month = month % 12 + 1
    next_year = year if month < 12 else year + 1

    return templates.TemplateResponse(request, "index.html", {
        "summary": summary,
        "recent_txs": recent_txs,
        "subscriptions": subs,
        "category_labels": category_labels,
        "category_values": category_values,
        "month_labels": month_labels,
        "month_totals": month_totals,
        "month_incomes": month_incomes,
        "year": year,
        "month": month,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "is_current_month": (year == today.year and month == today.month),
    })
