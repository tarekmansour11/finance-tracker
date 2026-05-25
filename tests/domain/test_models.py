from datetime import date
from decimal import Decimal

import pytest

from finance_tracker.domain.models import (
    MonthlySummary,
    PricePoint,
    RecurrenceFrequency,
    Subscription,
    Transaction,
)


def test_transaction_is_debit():
    t = Transaction(date=date(2024, 1, 1), description="TESCO", amount=Decimal("-20.00"))
    assert t.is_debit is True
    assert t.is_credit is False


def test_transaction_is_credit():
    t = Transaction(date=date(2024, 1, 1), description="SALARY", amount=Decimal("3500.00"))
    assert t.is_credit is True
    assert t.is_debit is False


def test_transaction_id_auto_generated():
    t = Transaction(date=date(2024, 1, 1), description="TEST", amount=Decimal("-1.00"))
    assert t.id is not None
    assert len(t.id) > 0


def test_monthly_summary_total_spent():
    summary = MonthlySummary(
        year=2024,
        month=1,
        totals={"Groceries": Decimal("100.00"), "Transport": Decimal("50.00")},
    )
    assert summary.total_spent == Decimal("150.00")


def test_monthly_summary_net():
    summary = MonthlySummary(
        year=2024,
        month=1,
        totals={"Groceries": Decimal("500.00")},
        total_income=Decimal("3500.00"),
    )
    assert summary.net == Decimal("3000.00")


def test_subscription_annual_cost_monthly():
    sub = Subscription(
        merchant="NETFLIX",
        amount=Decimal("15.99"),
        frequency=RecurrenceFrequency.MONTHLY,
    )
    assert sub.annual_cost == Decimal("15.99") * 12


def test_subscription_annual_cost_yearly():
    sub = Subscription(
        merchant="ANTIVIRUS",
        amount=Decimal("49.99"),
        frequency=RecurrenceFrequency.YEARLY,
    )
    assert sub.annual_cost == Decimal("49.99")


def test_subscription_price_increase_detected():
    sub = Subscription(
        merchant="SPOTIFY",
        amount=Decimal("11.99"),
        frequency=RecurrenceFrequency.MONTHLY,
        price_history=[
            PricePoint(date=date(2024, 1, 1), amount=Decimal("9.99")),
            PricePoint(date=date(2024, 6, 1), amount=Decimal("11.99")),
        ],
    )
    assert sub.had_price_increase is True


def test_subscription_no_price_increase():
    sub = Subscription(
        merchant="NETFLIX",
        amount=Decimal("15.99"),
        frequency=RecurrenceFrequency.MONTHLY,
        price_history=[
            PricePoint(date=date(2024, 1, 1), amount=Decimal("15.99")),
            PricePoint(date=date(2024, 2, 1), amount=Decimal("15.99")),
        ],
    )
    assert sub.had_price_increase is False
