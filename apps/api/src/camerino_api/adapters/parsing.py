"""Shared feed-parsing helpers: prices and availability normalization."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from camerino_domain import Availability, Money

_AMOUNT_FIRST_RE = re.compile(r"^(?P<amount>\d+(?:[.,]\d+)?)\s*(?P<currency>[A-Za-z]{3})$")
_CURRENCY_FIRST_RE = re.compile(r"^(?P<currency>[A-Za-z]{3})\s*(?P<amount>\d+(?:[.,]\d+)?)$")

_AVAILABILITY_MAP = {
    "in stock": Availability.IN_STOCK,
    "in_stock": Availability.IN_STOCK,
    "instock": Availability.IN_STOCK,
    "out of stock": Availability.OUT_OF_STOCK,
    "out_of_stock": Availability.OUT_OF_STOCK,
    "outofstock": Availability.OUT_OF_STOCK,
    "preorder": Availability.PREORDER,
    "pre-order": Availability.PREORDER,
    # Nearest normalized state: purchasable now, shipped later.
    "backorder": Availability.PREORDER,
}


def parse_price(raw: str) -> Money | None:
    """Parse feed prices like '139.99 EUR' or 'EUR 139.99'; None when invalid."""
    text = raw.strip()
    match = _AMOUNT_FIRST_RE.match(text) or _CURRENCY_FIRST_RE.match(text)
    if match is None:
        return None
    amount = match.group("amount").replace(",", ".")
    try:
        return Money(Decimal(amount), match.group("currency"))
    except (InvalidOperation, ValueError):
        return None


def parse_availability(raw: str) -> Availability | None:
    """Normalize feed availability wording; None when unrecognized."""
    return _AVAILABILITY_MAP.get(raw.strip().casefold())
