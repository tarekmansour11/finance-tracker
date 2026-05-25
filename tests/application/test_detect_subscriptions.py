from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from finance_tracker.application.detect_subscriptions import DetectSubscriptionsUseCase
from finance_tracker.domain.models import RecurrenceFrequency, Transaction
from finance_tracker.infrastructure.csv_reader import CsvReader
from finance_tracker.infrastructure.database import SqliteSubscriptionRepository

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _make_monthly_txs(description: str, months: list[int], amount: Decimal) -> list[Transaction]:
    return [
        Transaction(date=date(2024, m, 5), description=description, amount=-amount)
        for m in months
    ]


def test_detects_monthly_subscription(subscription_repo):
    txs = _make_monthly_txs("NETFLIX.COM", [1, 2, 3, 4], Decimal("15.99"))
    use_case = DetectSubscriptionsUseCase(subscription_repo)
    subs = use_case.execute(txs)
    assert len(subs) == 1
    assert subs[0].frequency == RecurrenceFrequency.MONTHLY
    assert subs[0].amount == Decimal("15.99")


def test_detects_multiple_subscriptions(subscription_repo):
    netflix = _make_monthly_txs("NETFLIX.COM", [1, 2, 3, 4], Decimal("15.99"))
    spotify = _make_monthly_txs("SPOTIFY PREMIUM", [1, 2, 3, 4], Decimal("9.99"))
    use_case = DetectSubscriptionsUseCase(subscription_repo)
    subs = use_case.execute(netflix + spotify)
    assert len(subs) == 2
    merchants = {s.merchant for s in subs}
    assert "NETFLIX.COM" in merchants
    assert "SPOTIFY PREMIUM" in merchants


def test_ignores_one_off_charges(subscription_repo):
    txs = [Transaction(date=date(2024, 1, 20), description="ONE OFF PURCHASE", amount=Decimal("-250.00"))]
    use_case = DetectSubscriptionsUseCase(subscription_repo)
    subs = use_case.execute(txs)
    assert len(subs) == 0


def test_ignores_credits(subscription_repo):
    # Salary appears monthly but is a credit — should not be flagged as subscription
    credits = [
        Transaction(date=date(2024, m, 10), description="SALARY BACS CREDIT", amount=Decimal("3500.00"))
        for m in [1, 2, 3, 4]
    ]
    use_case = DetectSubscriptionsUseCase(subscription_repo)
    subs = use_case.execute(credits)
    assert len(subs) == 0


def test_builds_price_history(subscription_repo):
    txs = _make_monthly_txs("NETFLIX.COM", [1, 2, 3], Decimal("15.99"))
    use_case = DetectSubscriptionsUseCase(subscription_repo)
    subs = use_case.execute(txs)
    assert len(subs[0].price_history) == 3


def test_persists_to_repo(subscription_repo):
    txs = _make_monthly_txs("SPOTIFY PREMIUM", [1, 2, 3, 4], Decimal("9.99"))
    use_case = DetectSubscriptionsUseCase(subscription_repo)
    use_case.execute(txs)
    persisted = subscription_repo.find_all()
    assert len(persisted) == 1
    assert persisted[0].merchant == "SPOTIFY PREMIUM"


def test_from_fixture_csv(subscription_repo):
    reader = CsvReader()
    transactions, _ = reader.read(FIXTURES / "subscriptions.csv")
    use_case = DetectSubscriptionsUseCase(subscription_repo)
    subs = use_case.execute(transactions)
    merchants = {s.merchant for s in subs}
    assert "NETFLIX.COM" in merchants
    assert "SPOTIFY PREMIUM" in merchants
