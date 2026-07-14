"""Product entity, normalized on the Google Shopping feed schema (UCP-ready)."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from camerino.domain.money import Money

_HEX_COLOR_RE = re.compile(r"^#[0-9a-f]{6}$")


class Availability(StrEnum):
    """Google Shopping availability values."""

    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    PREORDER = "preorder"


@dataclass(frozen=True, slots=True)
class Lab:
    """A color in CIELAB (D65) space."""

    l_star: float
    a_star: float
    b_star: float


@dataclass(frozen=True, slots=True)
class Product:
    """A normalized product as emitted by a SourceAdapter.

    `id` is the source-scoped external identifier: the pair
    (`source_id`, `id`) uniquely identifies the listing at its source.
    """

    id: str
    source_id: str
    brand: str
    title: str
    description: str
    price: Money
    availability: Availability
    image_url: str
    product_url: str
    category: str
    gtin: str | None = None
    mpn: str | None = None
    sku: str | None = None
    affiliate_url: str | None = None
    color_primary_hex: str | None = None
    color_primary_lab: Lab | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("id", "source_id", "brand", "title", "product_url"):
            value: str = getattr(self, name)
            if not value.strip():
                raise ValueError(f"{name} must not be blank")
        if self.color_primary_hex is not None:
            normalized = self.color_primary_hex.strip().lower()
            if not _HEX_COLOR_RE.match(normalized):
                raise ValueError(
                    f"color_primary_hex must be like '#rrggbb', got {self.color_primary_hex!r}"
                )
            object.__setattr__(self, "color_primary_hex", normalized)
