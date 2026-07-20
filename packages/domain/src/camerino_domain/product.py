"""Product entity, normalized on the Google Shopping feed schema."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from camerino_domain.money import Money

_HEX_RE = re.compile(r"^#[0-9a-f]{6}$")
_NON_WORD_RE = re.compile(r"[\W_]+", re.UNICODE)


class Availability(StrEnum):
    """Stock state, aligned with Google Shopping availability values."""

    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    PREORDER = "preorder"


@dataclass(frozen=True, slots=True)
class ColorRef:
    """A product color: normalized hex, optionally with CIELAB coordinates.

    Lab coordinates are computed by ``camerino_color`` (phase 5); the domain
    only carries them so that products stay self-contained.
    """

    hex: str
    lab: tuple[float, float, float] | None = None
    name: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "hex", self.hex.lower())
        if not _HEX_RE.match(self.hex):
            msg = f"color hex must look like '#rrggbb', got {self.hex!r}"
            raise ValueError(msg)


def normalize_title(title: str) -> str:
    """Normalize a product title for fuzzy identity matching.

    Lowercases, replaces every punctuation/separator run with a single
    space, and trims. Unicode letters are preserved (accents matter for
    brand/product names).
    """
    return _NON_WORD_RE.sub(" ", title.casefold()).strip()


@dataclass(frozen=True, slots=True)
class Product:
    """A normalized product coming out of a ``SourceAdapter``.

    The schema follows the Google Shopping feed so exports stay UCP-ready.
    ``raw`` keeps the original source payload for debugging and replay.
    """

    id: str
    brand: str
    title: str
    description: str
    price: Money
    availability: Availability
    image_url: str
    product_url: str
    source_id: str
    gtin: str | None = None
    mpn: str | None = None
    sku: str | None = None
    affiliate_url: str | None = None
    color_primary: ColorRef | None = None
    category: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("id", "brand", "title", "source_id"):
            value: str = getattr(self, name)
            if not value.strip():
                msg = f"{name} must not be blank"
                raise ValueError(msg)
        if self.price.amount <= 0:
            msg = f"price must be positive, got {self.price.amount}"
            raise ValueError(msg)
