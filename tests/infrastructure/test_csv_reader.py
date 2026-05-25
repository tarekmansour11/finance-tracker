from decimal import Decimal
from pathlib import Path

import pytest

from finance_tracker.infrastructure.csv_reader import CsvReader

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_reads_standard_csv():
    reader = CsvReader()
    transactions, errors = reader.read(FIXTURES / "standard.csv")

    assert len(errors) == 0
    assert len(transactions) == 13


def test_parses_amounts_correctly():
    reader = CsvReader()
    transactions, _ = reader.read(FIXTURES / "standard.csv")

    tesco = next(t for t in transactions if "TESCO" in t.description)
    assert tesco.amount == Decimal("-45.32")

    salary = next(t for t in transactions if "SALARY" in t.description)
    assert salary.amount == Decimal("3500.00")


def test_parses_currency():
    reader = CsvReader()
    transactions, _ = reader.read(FIXTURES / "standard.csv")
    assert all(t.currency == "GBP" for t in transactions)


def test_handles_duplicates_in_file():
    reader = CsvReader()
    transactions, errors = reader.read(FIXTURES / "with_duplicates.csv")
    # The CSV reader returns all rows — de-duplication is the use case's job
    assert len(errors) == 0
    assert len(transactions) == 6


def test_bad_date_produces_error(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("date,description,amount,currency\nNOT-A-DATE,TEST,-5.00,GBP\n")
    reader = CsvReader()
    transactions, errors = reader.read(bad_csv)
    assert len(transactions) == 0
    assert len(errors) == 1
    assert "2" in errors[0]  # line number


def test_bad_amount_produces_error(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("date,description,amount,currency\n2024-01-01,TEST,NOT_AMOUNT,GBP\n")
    reader = CsvReader()
    transactions, errors = reader.read(bad_csv)
    assert len(errors) == 1


def test_custom_column_map(tmp_path):
    # Simulate a bank with different column names
    csv_content = "Transaction Date,Narrative,Amount (GBP)\n2024-01-15,TESCO,-45.32\n"
    f = tmp_path / "custom.csv"
    f.write_text(csv_content)

    reader = CsvReader(column_map={"date": "Transaction Date", "description": "Narrative", "amount": "Amount (GBP)"})
    transactions, errors = reader.read(f)
    assert len(errors) == 0
    assert len(transactions) == 1
    assert transactions[0].amount == Decimal("-45.32")


def test_dd_mm_yyyy_date_format(tmp_path):
    csv_content = "date,description,amount,currency\n15/01/2024,TESCO,-45.32,GBP\n"
    f = tmp_path / "dates.csv"
    f.write_text(csv_content)
    reader = CsvReader()
    transactions, errors = reader.read(f)
    assert len(errors) == 0
    from datetime import date
    assert transactions[0].date == date(2024, 1, 15)
