"""Abstract interfaces (ports) — inner layer contracts that infrastructure must satisfy."""

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from .models import CategoryRule, Subscription, Transaction


class TransactionRepository(ABC):
    @abstractmethod
    def save_many(self, transactions: list[Transaction]) -> int:
        """Persist transactions; return count actually saved (excluding duplicates)."""

    @abstractmethod
    def find_all(self) -> list[Transaction]: ...

    @abstractmethod
    def find_by_month(self, year: int, month: int) -> list[Transaction]: ...

    @abstractmethod
    def find_uncategorised(self) -> list[Transaction]: ...

    @abstractmethod
    def update_category(self, transaction_id: str, category: str) -> None: ...

    @abstractmethod
    def exists(self, date_: date, description: str, amount: Decimal) -> bool: ...


class SubscriptionRepository(ABC):
    @abstractmethod
    def replace_all(self, subscriptions: list[Subscription]) -> None:
        """Overwrite the subscription list (re-detected on each run)."""

    @abstractmethod
    def find_all(self) -> list[Subscription]: ...


class CategoryRuleRepository(ABC):
    @abstractmethod
    def find_all(self) -> list[CategoryRule]: ...

    @abstractmethod
    def save(self, rule: CategoryRule) -> None: ...


class Categoriser(ABC):
    @abstractmethod
    def categorise(self, description: str, amount: Decimal) -> str | None:
        """Return a category string, or None if uncertain."""
