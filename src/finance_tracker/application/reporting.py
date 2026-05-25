"""Use case: generate monthly and cross-month summaries."""

from decimal import Decimal

from ..domain.models import MonthlySummary
from ..domain.ports import TransactionRepository


class ReportingService:
    def __init__(self, repo: TransactionRepository) -> None:
        self._repo = repo

    def monthly_summary(self, year: int, month: int) -> MonthlySummary:
        txs = self._repo.find_by_month(year, month)
        totals: dict[str, Decimal] = {}
        total_income = Decimal("0")

        for t in txs:
            if t.is_credit:
                total_income += t.amount
                continue
            category = t.category or "Uncategorised"
            totals[category] = totals.get(category, Decimal("0")) + abs(t.amount)

        return MonthlySummary(
            year=year, month=month, totals=totals, total_income=total_income
        )

    def all_monthly_summaries(self) -> list[MonthlySummary]:
        all_txs = self._repo.find_all()
        months = sorted({(t.date.year, t.date.month) for t in all_txs})
        return [self.monthly_summary(y, m) for y, m in months]
