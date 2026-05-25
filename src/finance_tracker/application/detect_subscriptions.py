"""Use case: scan transactions and detect recurring charges (subscriptions)."""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from ..domain.models import PricePoint, RecurrenceFrequency, Subscription, Transaction
from ..domain.ports import SubscriptionRepository

# A merchant needs at least this many charges to be considered a subscription.
MIN_OCCURRENCES = 2
# Allowed deviation (%) from the average interval before we reject it as recurring.
INTERVAL_TOLERANCE_DAYS = 5
# Allow ±10% amount variance still counts as "same subscription".
AMOUNT_TOLERANCE_RATIO = Decimal("0.10")


class DetectSubscriptionsUseCase:
    def __init__(self, repo: SubscriptionRepository) -> None:
        self._repo = repo

    def execute(self, transactions: list[Transaction]) -> list[Subscription]:
        debits = [t for t in transactions if t.is_debit]

        by_merchant: dict[str, list[Transaction]] = defaultdict(list)
        for t in debits:
            key = (t.merchant or t.description).strip().upper()
            by_merchant[key].append(t)

        subscriptions: list[Subscription] = []
        for merchant, txs in by_merchant.items():
            if len(txs) < MIN_OCCURRENCES:
                continue
            txs_sorted = sorted(txs, key=lambda x: x.date)
            frequency = self._detect_frequency(txs_sorted)
            if frequency is None:
                continue

            price_history = [
                PricePoint(date=t.date, amount=abs(t.amount)) for t in txs_sorted
            ]
            latest = txs_sorted[-1]
            sub = Subscription(
                merchant=merchant,
                category=latest.category,
                amount=abs(latest.amount),
                frequency=frequency,
                next_charge_date=self._next_charge(latest.date, frequency),
                price_history=price_history,
            )
            subscriptions.append(sub)

        self._repo.replace_all(subscriptions)
        return subscriptions

    def _detect_frequency(self, txs: list[Transaction]) -> RecurrenceFrequency | None:
        intervals = [
            (txs[i].date - txs[i - 1].date).days for i in range(1, len(txs))
        ]
        avg = sum(intervals) / len(intervals)
        spread = max(abs(d - avg) for d in intervals)

        if spread > INTERVAL_TOLERANCE_DAYS:
            return None  # too irregular

        if 6 <= avg <= 8:
            return RecurrenceFrequency.WEEKLY
        if 25 <= avg <= 35:
            return RecurrenceFrequency.MONTHLY
        if 350 <= avg <= 380:
            return RecurrenceFrequency.YEARLY
        return None

    def _next_charge(self, last: date, freq: RecurrenceFrequency) -> date:
        if freq == RecurrenceFrequency.WEEKLY:
            return last + timedelta(weeks=1)
        if freq == RecurrenceFrequency.MONTHLY:
            month = last.month % 12 + 1
            year = last.year + (last.month // 12)
            return last.replace(year=year, month=month)
        # yearly
        return last.replace(year=last.year + 1)
