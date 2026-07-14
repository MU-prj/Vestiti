"""Cross-merchant product identity resolution (dedup).

Matching precedence, strongest first (see docs/adr/0001-product-identity-dedup.md):

1. ``gtin``       - normalized, checksum-validated GTIN-14
2. ``brand_mpn``  - normalized brand + manufacturer part number
3. ``brand_sku``  - normalized brand + merchant SKU
4. ``fuzzy``      - normalized brand + normalized title + quantized primary color

All keys are deterministic string functions of the product: the same input
always resolves to the same canonical product, in memory and in SQL alike.
"""

import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol

from camerino.domain.offer import Offer
from camerino.domain.product import Product

_GTIN_LENGTHS = frozenset({8, 12, 13, 14})
_NON_DIGITS_RE = re.compile(r"\D")
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE_RE = re.compile(r"\s+")

KeyKind = Literal["gtin", "brand_mpn", "brand_sku", "fuzzy"]


def _gtin_checksum_valid(digits: str) -> bool:
    """Validate the GS1 mod-10 check digit (rightmost digit)."""
    total = 0
    # Weights 3/1 alternate starting from the digit next to the check digit.
    for position, char in enumerate(reversed(digits[:-1])):
        weight = 3 if position % 2 == 0 else 1
        total += int(char) * weight
    return (10 - total % 10) % 10 == int(digits[-1])


def normalize_gtin(value: str) -> str | None:
    """Normalize a GTIN to 14 digits; return None if malformed or bad checksum."""
    digits = _NON_DIGITS_RE.sub("", value)
    if len(digits) not in _GTIN_LENGTHS or not _gtin_checksum_valid(digits):
        return None
    return digits.zfill(14)


def _normalize_text(value: str) -> str:
    """Casefold, strip accents/punctuation, collapse whitespace."""
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    without_punct = _PUNCT_RE.sub(" ", without_accents.casefold())
    return _WHITESPACE_RE.sub(" ", without_punct).strip()


def normalize_brand(value: str) -> str:
    """Normalize a brand name for identity matching."""
    return _normalize_text(value)


def normalize_title(value: str) -> str:
    """Normalize a product title for fuzzy identity matching."""
    return _normalize_text(value)


def color_bucket(hex_color: str | None) -> str:
    """Quantize a '#rrggbb' color to coarse RGB buckets (64 levels per channel).

    Shops photograph and encode the same garment with slightly different
    colors; bucketing keeps the fuzzy key stable across small variations
    while still separating clearly different colorways.
    """
    if hex_color is None:
        return "none"
    r, g, b = (int(hex_color[i : i + 2], 16) // 64 for i in (1, 3, 5))
    return f"{r}{g}{b}"


@dataclass(frozen=True, slots=True)
class IdentityKey:
    """A single deterministic dedup key for a product."""

    kind: KeyKind
    value: str


def identity_keys(product: Product) -> tuple[IdentityKey, ...]:
    """Compute the ordered (strongest-first) identity keys for a product."""
    keys: list[IdentityKey] = []
    if product.gtin is not None:
        gtin = normalize_gtin(product.gtin)
        if gtin is not None:
            keys.append(IdentityKey(kind="gtin", value=gtin))
    brand = normalize_brand(product.brand)
    if product.mpn is not None and product.mpn.strip():
        keys.append(IdentityKey(kind="brand_mpn", value=f"{brand}|{product.mpn.strip().lower()}"))
    if product.sku is not None and product.sku.strip():
        keys.append(IdentityKey(kind="brand_sku", value=f"{brand}|{product.sku.strip().lower()}"))
    fuzzy = f"{brand}|{normalize_title(product.title)}|{color_bucket(product.color_primary_hex)}"
    keys.append(IdentityKey(kind="fuzzy", value=fuzzy))
    return tuple(keys)


@dataclass(slots=True)
class CanonicalProduct:
    """One garment, aggregated across N shops ("one product, many offers")."""

    id: str
    brand: str
    title: str
    description: str
    category: str
    image_url: str
    gtin: str | None = None
    mpn: str | None = None
    sku: str | None = None
    color_primary_hex: str | None = None
    offers: list[Offer] = field(default_factory=list)

    def merge_product(self, product: Product) -> None:
        """Fill identifiers and descriptive fields the canonical is missing."""
        if self.gtin is None and product.gtin is not None:
            self.gtin = normalize_gtin(product.gtin)
        if self.mpn is None and product.mpn is not None:
            self.mpn = product.mpn
        if self.sku is None and product.sku is not None:
            self.sku = product.sku
        if self.color_primary_hex is None and product.color_primary_hex is not None:
            self.color_primary_hex = product.color_primary_hex
        if not self.description and product.description:
            self.description = product.description
        if not self.category and product.category:
            self.category = product.category
        if not self.image_url and product.image_url:
            self.image_url = product.image_url

    def upsert_offer(self, product: Product, *, now: datetime) -> Offer:
        """Add the product's offer, or refresh it if already known."""
        url = product.product_url
        for offer in self.offers:
            if offer.source_id == product.source_id and offer.url == url:
                offer.price = product.price
                offer.availability = product.availability
                offer.affiliate_url = product.affiliate_url
                offer.last_seen_at = now
                return offer
        offer = Offer(
            source_id=product.source_id,
            url=url,
            price=product.price,
            availability=product.availability,
            affiliate_url=product.affiliate_url,
            first_seen_at=now,
            last_seen_at=now,
        )
        self.offers.append(offer)
        return offer


_KEY_STRENGTH: dict[KeyKind, int] = {"gtin": 3, "brand_mpn": 2, "brand_sku": 1, "fuzzy": 0}


class HasStrongIdentifiers(Protocol):
    """Anything carrying the strong identifiers of a canonical product.

    Satisfied by CanonicalProduct and by persistence rows alike, so the
    conflict rule below is shared between the in-memory index and SQL lookups.
    """

    @property
    def gtin(self) -> str | None: ...

    @property
    def mpn(self) -> str | None: ...


def conflicts_on_stronger_key(
    product: Product, candidate: HasStrongIdentifiers, matched_kind: KeyKind
) -> bool:
    """True if an identifier stronger than the matched key disagrees on both sides.

    Two listings with different valid GTINs are different garments no matter
    how similar their titles look; the same goes for the MPN below a
    brand_sku or fuzzy match.
    """
    strength = _KEY_STRENGTH[matched_kind]
    if strength < _KEY_STRENGTH["gtin"] and product.gtin is not None and candidate.gtin:
        product_gtin = normalize_gtin(product.gtin)
        if product_gtin is not None and product_gtin != candidate.gtin:
            return True
    candidate_mpn = candidate.mpn
    return (
        strength < _KEY_STRENGTH["brand_mpn"]
        and product.mpn is not None
        and candidate_mpn is not None
        and product.mpn.strip().lower() != candidate_mpn.strip().lower()
    )


class IdentityIndex:
    """In-memory identity resolver: maps identity keys to canonical products."""

    def __init__(self) -> None:
        self._by_key: dict[IdentityKey, CanonicalProduct] = {}
        self._canonicals: list[CanonicalProduct] = []

    @property
    def canonicals(self) -> list[CanonicalProduct]:
        """All canonical products known to the index."""
        return list(self._canonicals)

    def resolve(self, product: Product) -> CanonicalProduct | None:
        """Find the canonical product matching the strongest available key.

        A weaker-key match is rejected when an identifier stronger than the
        matching key is present on both sides and disagrees: two listings
        with different valid GTINs are different garments no matter how
        similar their titles look.
        """
        for key in identity_keys(product):
            canonical = self._by_key.get(key)
            if canonical is not None and not conflicts_on_stronger_key(
                product, canonical, key.kind
            ):
                return canonical
        return None

    def add(self, product: Product, *, now: datetime) -> tuple[CanonicalProduct, bool]:
        """Merge a product into the index; return (canonical, created)."""
        canonical = self.resolve(product)
        created = canonical is None
        if canonical is None:
            canonical = CanonicalProduct(
                id=str(uuid.uuid4()),
                brand=product.brand,
                title=product.title,
                description=product.description,
                category=product.category,
                image_url=product.image_url,
            )
            self._canonicals.append(canonical)
        canonical.merge_product(product)
        canonical.upsert_offer(product, now=now)
        # Register every key of the incoming product so the canonical becomes
        # reachable through identifiers learned from any of its offers.
        for key in identity_keys(product):
            self._by_key.setdefault(key, canonical)
        return canonical, created
