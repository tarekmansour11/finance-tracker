from datetime import date
from decimal import Decimal

import pytest

from finance_tracker.application.import_transactions import ImportTransactionsUseCase
from finance_tracker.domain.models import Transaction
from finance_tracker.domain.ports import Categoriser
from finance_tracker.infrastructure.rule_engine import RuleBasedCategoriser


class _FixedCategoriser(Categoriser):
    """Always returns a fixed category — for isolation."""
    def __init__(self, category: str = "Other"):
        self._category = category

    def categorise(self, description, amount):
        return self._category


def test_imports_new_transactions(transaction_repo, sample_transactions):
    use_case = ImportTransactionsUseCase(transaction_repo, _FixedCategoriser())
    result = use_case.execute(sample_transactions)
    assert result.imported == len(sample_transactions)
    assert result.skipped == 0


def test_skips_duplicates(transaction_repo, sample_transactions):
    use_case = ImportTransactionsUseCase(transaction_repo, _FixedCategoriser())
    use_case.execute(sample_transactions)
    result = use_case.execute(sample_transactions)  # second run — all duplicates
    assert result.imported == 0
    assert result.skipped == len(sample_transactions)


def test_categorises_uncategorised_transactions(transaction_repo):
    t = Transaction(date=date(2024, 1, 1), description="TESCO", amount=Decimal("-20.00"), category=None)
    use_case = ImportTransactionsUseCase(transaction_repo, RuleBasedCategoriser())
    use_case.execute([t])
    saved = transaction_repo.find_all()
    assert saved[0].category == "Groceries"


def test_preserves_existing_category(transaction_repo):
    t = Transaction(date=date(2024, 1, 1), description="MYSTERY", amount=Decimal("-20.00"), category="Shopping")
    use_case = ImportTransactionsUseCase(transaction_repo, _FixedCategoriser("Other"))
    use_case.execute([t])
    saved = transaction_repo.find_all()
    assert saved[0].category == "Shopping"  # not overwritten


def test_partial_duplicate_batch(transaction_repo):
    t1 = Transaction(date=date(2024, 1, 1), description="TESCO", amount=Decimal("-20.00"))
    t2 = Transaction(date=date(2024, 1, 2), description="NETFLIX", amount=Decimal("-15.99"))
    use_case = ImportTransactionsUseCase(transaction_repo, _FixedCategoriser())
    use_case.execute([t1])
    result = use_case.execute([t1, t2])
    assert result.imported == 1
    assert result.skipped == 1
