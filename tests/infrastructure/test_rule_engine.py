from decimal import Decimal

import pytest

from finance_tracker.infrastructure.rule_engine import RuleBasedCategoriser


@pytest.fixture
def categoriser():
    return RuleBasedCategoriser()


def test_categorises_groceries(categoriser):
    assert categoriser.categorise("TESCO SUPERSTORE", Decimal("-45.00")) == "Groceries"
    assert categoriser.categorise("SAINSBURYS LOCAL", Decimal("-12.00")) == "Groceries"
    assert categoriser.categorise("WAITROSE 001", Decimal("-30.00")) == "Groceries"


def test_categorises_entertainment(categoriser):
    assert categoriser.categorise("NETFLIX.COM", Decimal("-15.99")) == "Entertainment"
    assert categoriser.categorise("SPOTIFY PREMIUM", Decimal("-9.99")) == "Entertainment"
    assert categoriser.categorise("DISNEY PLUS", Decimal("-7.99")) == "Entertainment"


def test_categorises_eating_out(categoriser):
    assert categoriser.categorise("DELIVEROO ORDER #123", Decimal("-23.50")) == "Eating Out"
    assert categoriser.categorise("UBER EATS", Decimal("-15.00")) == "Eating Out"


def test_categorises_transport(categoriser):
    assert categoriser.categorise("TFL TRAVEL", Decimal("-4.80")) == "Transport"
    assert categoriser.categorise("NATIONAL RAIL", Decimal("-22.50")) == "Transport"


def test_categorises_utilities(categoriser):
    assert categoriser.categorise("OCTOPUS ENERGY", Decimal("-87.00")) == "Utilities"


def test_categorises_housing(categoriser):
    assert categoriser.categorise("RENT PAYMENT", Decimal("-1200.00")) == "Housing"


def test_categorises_income(categoriser):
    assert categoriser.categorise("SALARY BACS CREDIT", Decimal("3500.00")) == "Income"


def test_unknown_falls_back_to_other(categoriser):
    assert categoriser.categorise("RANDOM XYZ SHOP 1234", Decimal("-5.00")) == "Other"


def test_case_insensitive(categoriser):
    assert categoriser.categorise("tesco superstore", Decimal("-20.00")) == "Groceries"
    assert categoriser.categorise("TESCO SUPERSTORE", Decimal("-20.00")) == "Groceries"
