"""Camerino domain package.

Pure, framework-free domain entities and services. Nothing in this package
may import FastAPI, SQLAlchemy, or any other infrastructure dependency:
all logic here must be I/O-free and fully testable with fixtures.
"""

from camerino_domain.identity import (
    CanonicalProduct,
    IdentityKey,
    IdentityKind,
    ProductDeduplicator,
    identity_key,
    normalize_gtin,
)
from camerino_domain.money import Money
from camerino_domain.offer import Offer
from camerino_domain.ports import ProductStore, SourceAdapter
from camerino_domain.product import Availability, ColorRef, Product, normalize_title

__all__ = [
    "Availability",
    "CanonicalProduct",
    "ColorRef",
    "IdentityKey",
    "IdentityKind",
    "Money",
    "Offer",
    "Product",
    "ProductDeduplicator",
    "ProductStore",
    "SourceAdapter",
    "identity_key",
    "normalize_gtin",
    "normalize_title",
]
