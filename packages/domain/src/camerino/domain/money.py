"""Money value object (minor units + ISO 4217 currency code)."""

import re
from dataclasses import dataclass

_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


@dataclass(frozen=True, slots=True)
class Money:
    """An amount of money expressed in minor units (e.g. cents)."""

    amount_minor: int
    currency: str

    def __post_init__(self) -> None:
        if self.amount_minor < 0:
            raise ValueError(f"amount_minor must not be negative, got {self.amount_minor}")
        normalized = self.currency.strip().upper()
        if not _CURRENCY_RE.match(normalized):
            raise ValueError(f"currency must be a 3-letter ISO 4217 code, got {self.currency!r}")
        object.__setattr__(self, "currency", normalized)
