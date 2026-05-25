"""Shared fixtures for all tests."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from finance_tracker.domain.models import Transaction
from finance_tracker.infrastructure.database import (
    SqliteCategoryRuleRepository,
    SqliteSubscriptionRepository,
    SqliteTransactionRepository,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def in_memory_db(tmp_path) -> Path:
    """Return a path to a fresh temporary SQLite database."""
    return tmp_path / "test.db"


@pytest.fixture
def transaction_repo(in_memory_db):
    return SqliteTransactionRepository(in_memory_db)


@pytest.fixture
def subscription_repo(in_memory_db):
    return SqliteSubscriptionRepository(in_memory_db)


@pytest.fixture
def rule_repo(in_memory_db):
    return SqliteCategoryRuleRepository(in_memory_db)


@pytest.fixture
def sample_transactions() -> list[Transaction]:
    return [
        Transaction(date=date(2024, 1, 2), description="TESCO SUPERSTORE", amount=Decimal("-45.32")),
        Transaction(date=date(2024, 1, 3), description="SALARY BACS CREDIT", amount=Decimal("3500.00")),
        Transaction(date=date(2024, 1, 5), description="NETFLIX.COM", amount=Decimal("-15.99")),
        Transaction(date=date(2024, 1, 7), description="TFL TRAVEL", amount=Decimal("-4.80")),
        Transaction(date=date(2024, 1, 10), description="DELIVEROO ORDER", amount=Decimal("-23.50")),
    ]
