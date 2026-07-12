"""Tests for the Money value object."""

from decimal import Decimal

import pytest

from camerino_domain.money import Money


def test_money_holds_decimal_amount_and_iso_currency() -> None:
    price = Money(Decimal("39.90"), "EUR")
    assert price.amount == Decimal("39.90")
    assert price.currency == "EUR"


def test_money_normalizes_currency_to_uppercase() -> None:
    assert Money(Decimal("5"), "eur").currency == "EUR"


@pytest.mark.parametrize("currency", ["EURO", "E1R", "", "E", "€"])
def test_money_rejects_invalid_currency_codes(currency: str) -> None:
    with pytest.raises(ValueError, match="currency"):
        Money(Decimal("5"), currency)


def test_money_rejects_negative_amounts() -> None:
    with pytest.raises(ValueError, match="amount"):
        Money(Decimal("-0.01"), "EUR")


def test_money_of_parses_string_amounts_without_floats() -> None:
    assert Money.of("39.90", "EUR").amount == Decimal("39.90")


def test_money_equality_ignores_trailing_zeros() -> None:
    assert Money.of("10.00", "EUR") == Money.of("10.0", "EUR")


def test_money_orders_amounts_within_the_same_currency() -> None:
    assert Money.of("9.99", "EUR") < Money.of("10", "EUR")
    assert Money.of("10", "EUR") <= Money.of("10.00", "EUR")
    assert Money.of("10", "EUR") > Money.of("9.99", "EUR")
    assert Money.of("10", "EUR") >= Money.of("10.00", "EUR")


def test_money_refuses_to_order_across_currencies() -> None:
    with pytest.raises(ValueError, match="currencies"):
        Money.of("1", "EUR") < Money.of("1", "USD")  # noqa: B015
