"""Shared product fixtures for domain tests."""

from collections.abc import Callable
from typing import Any

import pytest

from camerino.domain.money import Money
from camerino.domain.product import Availability, Product

ProductFactory = Callable[..., Product]


@pytest.fixture
def make_product() -> ProductFactory:
    """Factory fixture building a valid Product with overridable fields."""

    def factory(**overrides: Any) -> Product:
        defaults: dict[str, Any] = {
            "id": "SKU-001",
            "source_id": "shop-a",
            "brand": "Acme",
            "title": "Wool Coat Navy",
            "description": "A navy wool coat.",
            "price": Money(amount_minor=19900, currency="EUR"),
            "availability": Availability.IN_STOCK,
            "image_url": "https://cdn.example.com/coat.jpg",
            "product_url": "https://shop-a.example.com/products/wool-coat-navy",
            "category": "Apparel & Accessories > Clothing > Outerwear > Coats & Jackets",
        }
        defaults.update(overrides)
        return Product(**defaults)

    return factory
