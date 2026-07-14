"""Money value object tests."""

import pytest

from camerino.domain.money import Money


def test_money_holds_minor_units_and_currency() -> None:
    price = Money(amount_minor=12999, currency="EUR")
    assert price.amount_minor == 12999
    assert price.currency == "EUR"


def test_money_normalizes_currency_case() -> None:
    assert Money(amount_minor=1, currency="eur").currency == "EUR"


def test_money_rejects_negative_amounts() -> None:
    with pytest.raises(ValueError, match="negative"):
        Money(amount_minor=-1, currency="EUR")


@pytest.mark.parametrize("currency", ["", "EU", "EURO", "E1R"])
def test_money_rejects_invalid_currency_codes(currency: str) -> None:
    with pytest.raises(ValueError, match="currency"):
        Money(amount_minor=100, currency=currency)


def test_money_is_immutable_and_comparable() -> None:
    a = Money(amount_minor=100, currency="EUR")
    b = Money(amount_minor=100, currency="EUR")
    assert a == b
    with pytest.raises(AttributeError):
        a.amount_minor = 200  # type: ignore[misc]
