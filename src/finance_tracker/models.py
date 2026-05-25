"""Core data models for finance-tracker."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """A single financial transaction."""

    id: str
    date: date
    description: str
    amount: Decimal  # positive = credit, negative = debit
    currency: str = "GBP"
    category: str | None = None
    notes: str | None = None


class Category(BaseModel):
    """A spending category with an optional monthly budget."""

    name: str
    budget: Decimal | None = Field(default=None, description="Monthly budget in GBP")


class MonthlySummary(BaseModel):
    """Aggregated spending for a single month."""

    year: int
    month: int  # 1–12
    totals: dict[str, Decimal] = Field(default_factory=dict)  # category -> total spent

    @property
    def total_spent(self) -> Decimal:
        return sum(self.totals.values(), Decimal(0))
