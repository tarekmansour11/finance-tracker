"""CSV reader — parses a transaction file into domain Transaction objects.

Expects columns: date, description, amount, currency (currency is optional).
Column names can be remapped via a dict passed at construction time.
"""

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..domain.models import Transaction

# Default column names the tool expects.
_DEFAULTS = {"date": "date", "description": "description", "amount": "amount", "currency": "currency"}

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"]


def _parse_date(value: str) -> date:
    for fmt in DATE_FORMATS:
        try:
            from datetime import datetime
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date format: {value!r}")


def _parse_amount(value: str) -> Decimal:
    cleaned = value.strip().replace(",", "").replace("£", "").replace("$", "").replace("€", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"Cannot parse amount: {value!r}")


class CsvReader:
    """Read transactions from a CSV file.

    Args:
        column_map: Optional mapping of canonical names → actual CSV headers.
                    e.g. {"date": "Transaction Date", "amount": "Amount (GBP)"}
    """

    def __init__(self, column_map: dict[str, str] | None = None) -> None:
        self._map = {**_DEFAULTS, **(column_map or {})}

    def read(self, path: Path) -> tuple[list[Transaction], list[str]]:
        """Return (transactions, errors).  Errors are human-readable strings."""
        transactions: list[Transaction] = []
        errors: list[str] = []

        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for line_no, row in enumerate(reader, start=2):
                try:
                    t = self._parse_row(row)
                    transactions.append(t)
                except (KeyError, ValueError) as exc:
                    errors.append(f"Line {line_no}: {exc}")

        return transactions, errors

    def _parse_row(self, row: dict[str, str]) -> Transaction:
        date_val = _parse_date(row[self._map["date"]])
        description = row[self._map["description"]].strip()
        amount = _parse_amount(row[self._map["amount"]])
        currency_col = self._map.get("currency", "currency")
        currency = row.get(currency_col, "GBP").strip() or "GBP"

        return Transaction(
            date=date_val,
            description=description,
            amount=amount,
            currency=currency,
        )
