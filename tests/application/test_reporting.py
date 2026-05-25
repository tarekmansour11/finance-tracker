from datetime import date
from decimal import Decimal

import pytest

from finance_tracker.application.reporting import ReportingService
from finance_tracker.domain.models import Transaction


def test_monthly_summary_totals(transaction_repo):
    txs = [
        Transaction(date=date(2024, 1, 2), description="TESCO", amount=Decimal("-45.00"), category="Groceries"),
        Transaction(date=date(2024, 1, 5), description="NETFLIX", amount=Decimal("-15.99"), category="Entertainment"),
        Transaction(date=date(2024, 1, 3), description="SALARY", amount=Decimal("3500.00"), category="Income"),
    ]
    transaction_repo.save_many(txs)
    service = ReportingService(transaction_repo)
    summary = service.monthly_summary(2024, 1)

    assert summary.totals["Groceries"] == Decimal("45.00")
    assert summary.totals["Entertainment"] == Decimal("15.99")
    assert summary.total_income == Decimal("3500.00")
    assert summary.total_spent == Decimal("60.99")


def test_monthly_summary_groups_same_category(transaction_repo):
    txs = [
        Transaction(date=date(2024, 1, 2), description="TESCO", amount=Decimal("-45.00"), category="Groceries"),
        Transaction(date=date(2024, 1, 10), description="SAINSBURYS", amount=Decimal("-30.00"), category="Groceries"),
    ]
    transaction_repo.save_many(txs)
    service = ReportingService(transaction_repo)
    summary = service.monthly_summary(2024, 1)
    assert summary.totals["Groceries"] == Decimal("75.00")


def test_monthly_summary_excludes_other_months(transaction_repo):
    jan = Transaction(date=date(2024, 1, 15), description="JAN TX", amount=Decimal("-100.00"), category="Other")
    feb = Transaction(date=date(2024, 2, 15), description="FEB TX", amount=Decimal("-200.00"), category="Other")
    transaction_repo.save_many([jan, feb])
    service = ReportingService(transaction_repo)
    jan_summary = service.monthly_summary(2024, 1)
    assert jan_summary.total_spent == Decimal("100.00")


def test_all_summaries_returns_one_per_month(transaction_repo):
    txs = [
        Transaction(date=date(2024, 1, 1), description="A", amount=Decimal("-10.00")),
        Transaction(date=date(2024, 2, 1), description="B", amount=Decimal("-10.00")),
        Transaction(date=date(2024, 3, 1), description="C", amount=Decimal("-10.00")),
    ]
    transaction_repo.save_many(txs)
    service = ReportingService(transaction_repo)
    summaries = service.all_monthly_summaries()
    assert len(summaries) == 3
    assert summaries[0].month == 1
    assert summaries[2].month == 3
