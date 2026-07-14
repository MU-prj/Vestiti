"""Camerino domain package: pure entities and business logic, zero I/O."""

from camerino.domain.identity import (
    CanonicalProduct,
    IdentityIndex,
    IdentityKey,
    identity_keys,
    normalize_gtin,
)
from camerino.domain.money import Money
from camerino.domain.offer import Offer
from camerino.domain.product import Availability, Lab, Product

__version__ = "0.1.0"

__all__ = [
    "Availability",
    "CanonicalProduct",
    "IdentityIndex",
    "IdentityKey",
    "Lab",
    "Money",
    "Offer",
    "Product",
    "identity_keys",
    "normalize_gtin",
]
