"""SourceAdapter: the only doorway products may enter Camerino through.

Hard invariant: sources are official feeds only (Google Shopping feeds,
affiliate networks, Shopify Storefront API, merchant-provided feeds).
No adapter may scrape retail HTML.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from camerino.domain import Product


class SourceAdapter(ABC):
    """Fetches normalized products from one official source."""

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Stable identifier of the source (used on offers and dedup)."""

    @abstractmethod
    def fetch(self) -> AsyncIterator[Product]:
        """Yield the source's current catalog as normalized products."""
