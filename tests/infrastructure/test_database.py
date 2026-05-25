from datetime import date
from decimal import Decimal

import pytest

from finance_tracker.domain.models import CategoryRule, Transaction
from finance_tracker.infrastructure.database import (
    SqliteCategoryRuleRepository,
    SqliteSubscriptionRepository,
    SqliteTransactionRepository,
)


def test_save_and_retrieve_transactions(transaction_repo, sample_transactions):
    transaction_repo.save_many(sample_transactions)
    result = transaction_repo.find_all()
    assert len(result) == len(sample_transactions)


def test_returns_count_of_saved(transaction_repo, sample_transactions):
    count = transaction_repo.save_many(sample_transactions)
    assert count == len(sample_transactions)


def test_duplicate_not_saved(transaction_repo):
    t = Transaction(date=date(2024, 1, 1), description="TESCO", amount=Decimal("-20.00"))
    transaction_repo.save_many([t])
    count = transaction_repo.save_many([t])
    assert count == 0
    assert len(transaction_repo.find_all()) == 1


def test_exists_returns_true_for_duplicate(transaction_repo):
    t = Transaction(date=date(2024, 1, 1), description="TESCO", amount=Decimal("-20.00"))
    transaction_repo.save_many([t])
    assert transaction_repo.exists(t.date, t.description, t.amount) is True


def test_exists_returns_false_for_new(transaction_repo):
    assert transaction_repo.exists(date(2024, 1, 1), "NEW MERCHANT", Decimal("-5.00")) is False


def test_find_by_month(transaction_repo, sample_transactions):
    transaction_repo.save_many(sample_transactions)
    jan = transaction_repo.find_by_month(2024, 1)
    assert len(jan) == len(sample_transactions)


def test_find_by_month_excludes_other_months(transaction_repo):
    t_jan = Transaction(date=date(2024, 1, 15), description="JAN", amount=Decimal("-10.00"))
    t_feb = Transaction(date=date(2024, 2, 15), description="FEB", amount=Decimal("-10.00"))
    transaction_repo.save_many([t_jan, t_feb])
    assert len(transaction_repo.find_by_month(2024, 1)) == 1
    assert len(transaction_repo.find_by_month(2024, 2)) == 1


def test_update_category(transaction_repo):
    t = Transaction(date=date(2024, 1, 1), description="MYSTERY", amount=Decimal("-5.00"), category=None)
    transaction_repo.save_many([t])
    transaction_repo.update_category(t.id, "Shopping")
    result = transaction_repo.find_all()
    assert result[0].category == "Shopping"


def test_find_uncategorised(transaction_repo):
    t1 = Transaction(date=date(2024, 1, 1), description="KNOWN", amount=Decimal("-5.00"), category="Groceries")
    t2 = Transaction(date=date(2024, 1, 2), description="UNKNOWN", amount=Decimal("-5.00"), category=None)
    transaction_repo.save_many([t1, t2])
    uncategorised = transaction_repo.find_uncategorised()
    assert len(uncategorised) == 1
    assert uncategorised[0].description == "UNKNOWN"
