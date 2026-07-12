"""Offer: one merchant's listing of a canonical product."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from camerino_domain.money import Money
from camerino_domain.product import Availability, Product


@dataclass(frozen=True, slots=True)
class Offer:
    """The same garment, one specific shop: price, stock and where to buy."""

    canonical_product_id: str
    source_id: str
    final_price: Money
    availability: Availability
    url: str
    last_seen_at: datetime

    @classmethod
    def from_product(
        cls, product: Product, canonical_product_id: str, last_seen_at: datetime
    ) -> Offer:
        """Project a normalized source product onto its canonical listing."""
        return cls(
            canonical_product_id=canonical_product_id,
            source_id=product.source_id,
            final_price=product.price,
            availability=product.availability,
            url=product.affiliate_url or product.product_url,
            last_seen_at=last_seen_at,
        )
