"""Money value object: exact decimal amounts, ISO 4217 currency codes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


@dataclass(frozen=True, slots=True)
class Money:
    """An exact monetary amount in a single currency.

    Amounts are always ``Decimal`` (never floats) and never negative:
    product feeds carry prices, not debts.
    """

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "currency", self.currency.upper())
        if not _CURRENCY_RE.match(self.currency):
            msg = f"currency must be a 3-letter ISO 4217 code, got {self.currency!r}"
            raise ValueError(msg)
        if self.amount < 0:
            msg = f"amount must be non-negative, got {self.amount}"
            raise ValueError(msg)

    @classmethod
    def of(cls, amount: str | int | Decimal, currency: str) -> Money:
        """Build Money from a string/int amount without going through floats."""
        return cls(Decimal(amount), currency)

    def _check_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            msg = f"cannot compare different currencies: {self.currency} vs {other.currency}"
            raise ValueError(msg)

    def __lt__(self, other: Money) -> bool:
        self._check_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        self._check_same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        self._check_same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        self._check_same_currency(other)
        return self.amount >= other.amount
