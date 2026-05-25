"""Use case: import a batch of transactions, de-duplicate, and categorise."""

from dataclasses import dataclass

from ..domain.models import Transaction
from ..domain.ports import Categoriser, TransactionRepository


@dataclass
class ImportResult:
    imported: int
    skipped: int  # duplicates


class ImportTransactionsUseCase:
    def __init__(self, repo: TransactionRepository, categoriser: Categoriser) -> None:
        self._repo = repo
        self._categoriser = categoriser

    def execute(self, transactions: list[Transaction]) -> ImportResult:
        to_save: list[Transaction] = []
        skipped = 0

        for t in transactions:
            if self._repo.exists(t.date, t.description, t.amount):
                skipped += 1
                continue
            if t.category is None:
                t.category = self._categoriser.categorise(t.description, t.amount)
            to_save.append(t)

        saved = self._repo.save_many(to_save)
        return ImportResult(imported=saved, skipped=skipped)
