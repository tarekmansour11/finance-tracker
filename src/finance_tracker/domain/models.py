"""Core domain models — no external dependencies allowed in this layer."""

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class RecurrenceFrequency(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    date: date
    description: str
    amount: Decimal  # negative = debit, positive = credit
    currency: str = "GBP"
    category: str | None = None
    merchant: str | None = None
    is_recurring: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_debit(self) -> bool:
        return self.amount < 0

    @property
    def is_credit(self) -> bool:
        return self.amount > 0


class CategoryRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    pattern: str  # regex matched against description (case-insensitive)
    category: str
    priority: int = 0  # higher = checked first


class PricePoint(BaseModel):
    date: date
    amount: Decimal


class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    merchant: str
    category: str | None = None
    amount: Decimal  # latest known charge amount
    frequency: RecurrenceFrequency
    next_charge_date: date | None = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    price_history: list[PricePoint] = Field(default_factory=list)

    @property
    def annual_cost(self) -> Decimal:
        multipliers = {
            RecurrenceFrequency.WEEKLY: Decimal("52"),
            RecurrenceFrequency.MONTHLY: Decimal("12"),
            RecurrenceFrequency.YEARLY: Decimal("1"),
        }
        return self.amount * multipliers[self.frequency]

    @property
    def had_price_increase(self) -> bool:
        if len(self.price_history) < 2:
            return False
        return self.price_history[-1].amount > self.price_history[0].amount


class MonthlySummary(BaseModel):
    year: int
    month: int
    totals: dict[str, Decimal] = Field(default_factory=dict)  # category -> total spent
    total_income: Decimal = Decimal("0")

    @property
    def total_spent(self) -> Decimal:
        return sum(self.totals.values(), Decimal("0"))

    @property
    def net(self) -> Decimal:
        return self.total_income - self.total_spent
