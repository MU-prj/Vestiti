"""Cross-merchant product identity resolution and deduplication.

Matching key precedence: GTIN -> (brand, MPN) -> (brand, SKU) ->
fuzzy (brand, normalized title, color). One ``CanonicalProduct`` collects
N ``Offer`` (same garment, several shops, different prices).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from camerino_domain.offer import Offer
from camerino_domain.product import Product, normalize_title

_GTIN_SEPARATORS_RE = re.compile(r"[\s-]+")
_GTIN_VALID_LENGTHS = frozenset({8, 12, 13, 14})


def normalize_gtin(raw: str) -> str | None:
    """Normalize a GTIN to its 14-digit form; return None when invalid.

    GTIN-8/12/13 are zero-padded to GTIN-14 so that the same article coming
    from feeds with different conventions still collides on one key.
    """
    digits = _GTIN_SEPARATORS_RE.sub("", raw)
    if not digits.isdigit() or len(digits) not in _GTIN_VALID_LENGTHS:
        return None
    return digits.zfill(14)


class IdentityKind(StrEnum):
    """Which rule produced an identity key, in decreasing confidence."""

    GTIN = "gtin"
    BRAND_MPN = "brand_mpn"
    BRAND_SKU = "brand_sku"
    FUZZY = "fuzzy"


@dataclass(frozen=True, slots=True)
class IdentityKey:
    """Hashable dedup key: the rule kind plus its normalized components."""

    kind: IdentityKind
    value: tuple[str, ...]


def identity_key(product: Product) -> IdentityKey:
    """Resolve the strongest available identity key for a product."""
    if product.gtin is not None:
        gtin = normalize_gtin(product.gtin)
        if gtin is not None:
            return IdentityKey(IdentityKind.GTIN, (gtin,))
    brand = product.brand.casefold().strip()
    if product.mpn is not None and product.mpn.strip():
        return IdentityKey(IdentityKind.BRAND_MPN, (brand, product.mpn.casefold().strip()))
    if product.sku is not None and product.sku.strip():
        return IdentityKey(IdentityKind.BRAND_SKU, (brand, product.sku.casefold().strip()))
    color = product.color_primary.hex if product.color_primary is not None else ""
    return IdentityKey(IdentityKind.FUZZY, (brand, normalize_title(product.title), color))


@dataclass(slots=True)
class CanonicalProduct:
    """One garment across shops: representative data plus all known offers.

    Representative fields come from the first product seen for the key;
    later sources only contribute offers.
    """

    id: str
    key: IdentityKey
    brand: str
    title: str
    description: str
    image_url: str
    category: str | None
    color_hex: str | None
    offers: list[Offer] = field(default_factory=list)

    @classmethod
    def from_product(cls, key: IdentityKey, product: Product) -> CanonicalProduct:
        return cls(
            id=str(uuid4()),
            key=key,
            brand=product.brand,
            title=product.title,
            description=product.description,
            image_url=product.image_url,
            category=product.category,
            color_hex=product.color_primary.hex if product.color_primary else None,
        )

    def upsert_offer(self, offer: Offer) -> None:
        """Add the offer, replacing any previous offer from the same source."""
        self.offers = [o for o in self.offers if o.source_id != offer.source_id]
        self.offers.append(offer)


class ProductDeduplicator:
    """In-memory identity index: collapses source products into canonicals."""

    def __init__(self) -> None:
        self._by_key: dict[IdentityKey, CanonicalProduct] = {}

    def add(self, product: Product, *, now: datetime) -> CanonicalProduct:
        """Register a product sighting and return its canonical product."""
        key = identity_key(product)
        canonical = self._by_key.get(key)
        if canonical is None:
            canonical = CanonicalProduct.from_product(key, product)
            self._by_key[key] = canonical
        canonical.upsert_offer(Offer.from_product(product, canonical.id, now))
        return canonical

    def canonical_products(self) -> list[CanonicalProduct]:
        return list(self._by_key.values())
