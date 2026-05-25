"""SQLite implementations of the domain repository ports."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from ..domain.models import CategoryRule, PricePoint, RecurrenceFrequency, Subscription, Transaction
from ..domain.ports import CategoryRuleRepository, SubscriptionRepository, TransactionRepository

_SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id          TEXT PRIMARY KEY,
    date        TEXT NOT NULL,
    description TEXT NOT NULL,
    amount      TEXT NOT NULL,
    currency    TEXT NOT NULL DEFAULT 'GBP',
    category    TEXT,
    merchant    TEXT,
    is_recurring INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id                TEXT PRIMARY KEY,
    merchant          TEXT NOT NULL,
    category          TEXT,
    amount            TEXT NOT NULL,
    frequency         TEXT NOT NULL,
    next_charge_date  TEXT,
    detected_at       TEXT NOT NULL,
    price_history     TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS category_rules (
    id       TEXT PRIMARY KEY,
    pattern  TEXT NOT NULL,
    category TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0
);
"""


@contextmanager
def _connect(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str | Path) -> None:
    with _connect(str(db_path)) as conn:
        conn.executescript(_SCHEMA)


class SqliteTransactionRepository(TransactionRepository):
    def __init__(self, db_path: str | Path) -> None:
        self._path = str(db_path)
        init_db(self._path)

    def save_many(self, transactions: list[Transaction]) -> int:
        saved = 0
        with _connect(self._path) as conn:
            for t in transactions:
                try:
                    conn.execute(
                        """INSERT INTO transactions
                           (id, date, description, amount, currency, category, merchant, is_recurring, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            t.id,
                            t.date.isoformat(),
                            t.description,
                            str(t.amount),
                            t.currency,
                            t.category,
                            t.merchant,
                            int(t.is_recurring),
                            t.created_at.isoformat(),
                        ),
                    )
                    saved += 1
                except sqlite3.IntegrityError:
                    pass
        return saved

    def find_all(self) -> list[Transaction]:
        with _connect(self._path) as conn:
            rows = conn.execute(
                "SELECT * FROM transactions ORDER BY date DESC"
            ).fetchall()
        return [_row_to_transaction(r) for r in rows]

    def find_by_month(self, year: int, month: int) -> list[Transaction]:
        prefix = f"{year}-{month:02d}"
        with _connect(self._path) as conn:
            rows = conn.execute(
                "SELECT * FROM transactions WHERE date LIKE ? ORDER BY date",
                (f"{prefix}%",),
            ).fetchall()
        return [_row_to_transaction(r) for r in rows]

    def find_uncategorised(self) -> list[Transaction]:
        with _connect(self._path) as conn:
            rows = conn.execute(
                "SELECT * FROM transactions WHERE category IS NULL"
            ).fetchall()
        return [_row_to_transaction(r) for r in rows]

    def update_category(self, transaction_id: str, category: str) -> None:
        with _connect(self._path) as conn:
            conn.execute(
                "UPDATE transactions SET category = ? WHERE id = ?",
                (category, transaction_id),
            )

    def exists(self, date_: date, description: str, amount: Decimal) -> bool:
        with _connect(self._path) as conn:
            row = conn.execute(
                "SELECT 1 FROM transactions WHERE date = ? AND description = ? AND amount = ?",
                (date_.isoformat(), description, str(amount)),
            ).fetchone()
        return row is not None


class SqliteSubscriptionRepository(SubscriptionRepository):
    def __init__(self, db_path: str | Path) -> None:
        self._path = str(db_path)
        init_db(self._path)

    def replace_all(self, subscriptions: list[Subscription]) -> None:
        with _connect(self._path) as conn:
            conn.execute("DELETE FROM subscriptions")
            for s in subscriptions:
                conn.execute(
                    """INSERT INTO subscriptions
                       (id, merchant, category, amount, frequency, next_charge_date, detected_at, price_history)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        s.id,
                        s.merchant,
                        s.category,
                        str(s.amount),
                        s.frequency.value,
                        s.next_charge_date.isoformat() if s.next_charge_date else None,
                        s.detected_at.isoformat(),
                        json.dumps([{"date": str(p.date), "amount": str(p.amount)} for p in s.price_history]),
                    ),
                )

    def find_all(self) -> list[Subscription]:
        with _connect(self._path) as conn:
            rows = conn.execute(
                "SELECT * FROM subscriptions ORDER BY merchant"
            ).fetchall()
        return [_row_to_subscription(r) for r in rows]


class SqliteCategoryRuleRepository(CategoryRuleRepository):
    def __init__(self, db_path: str | Path) -> None:
        self._path = str(db_path)
        init_db(self._path)

    def find_all(self) -> list[CategoryRule]:
        with _connect(self._path) as conn:
            rows = conn.execute(
                "SELECT * FROM category_rules ORDER BY priority DESC"
            ).fetchall()
        return [
            CategoryRule(id=r["id"], pattern=r["pattern"], category=r["category"], priority=r["priority"])
            for r in rows
        ]

    def save(self, rule: CategoryRule) -> None:
        with _connect(self._path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO category_rules (id, pattern, category, priority) VALUES (?, ?, ?, ?)",
                (rule.id, rule.pattern, rule.category, rule.priority),
            )


# --- helpers ---

def _row_to_transaction(row: sqlite3.Row) -> Transaction:
    return Transaction(
        id=row["id"],
        date=date.fromisoformat(row["date"]),
        description=row["description"],
        amount=Decimal(row["amount"]),
        currency=row["currency"],
        category=row["category"],
        merchant=row["merchant"],
        is_recurring=bool(row["is_recurring"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _row_to_subscription(row: sqlite3.Row) -> Subscription:
    raw_history = json.loads(row["price_history"])
    price_history = [PricePoint(date=date.fromisoformat(p["date"]), amount=Decimal(p["amount"])) for p in raw_history]
    return Subscription(
        id=row["id"],
        merchant=row["merchant"],
        category=row["category"],
        amount=Decimal(row["amount"]),
        frequency=RecurrenceFrequency(row["frequency"]),
        next_charge_date=date.fromisoformat(row["next_charge_date"]) if row["next_charge_date"] else None,
        detected_at=datetime.fromisoformat(row["detected_at"]),
        price_history=price_history,
    )
