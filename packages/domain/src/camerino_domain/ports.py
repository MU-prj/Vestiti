"""Ports (interfaces) the outside world implements for the domain.

Only abstractions live here: no I/O, no framework imports. Concrete
adapters (Shopify, Google Shopping feeds, affiliate networks, mocks)
belong to the application layer.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from camerino_domain.identity import CanonicalProduct, IdentityKey
from camerino_domain.offer import Offer
from camerino_domain.product import Product


class SourceAdapter(Protocol):
    """A product source: official feeds, affiliate networks, Storefront APIs.

    Implementations must never scrape retail sites in violation of their
    terms of service (project hard invariant #1).
    """

    @property
    def source_id(self) -> str:
        """Stable identifier of this source (used on offers)."""
        ...

    def fetch_products(self) -> AsyncIterator[Product]:
        """Yield normalized products from the source."""
        ...


class ProductStore(Protocol):
    """Persistence port for canonical products and their offers."""

    async def get_by_key(self, key: IdentityKey) -> CanonicalProduct | None:
        """Load the canonical product for an identity key, if it exists."""
        ...

    async def add_canonical(self, canonical: CanonicalProduct) -> None:
        """Persist a brand-new canonical product (without offers)."""
        ...

    async def upsert_offer(self, offer: Offer, *, raw: dict[str, object]) -> None:
        """Insert or replace the offer for (canonical product, source)."""
        ...
