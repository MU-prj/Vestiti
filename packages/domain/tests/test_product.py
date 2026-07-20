"""Tests for the Product entity and its value objects."""

import pytest

from camerino_domain.money import Money
from camerino_domain.product import Availability, ColorRef, Product, normalize_title


def make_product(**overrides: object) -> Product:
    defaults: dict[str, object] = {
        "id": "prod-1",
        "brand": "Nike",
        "title": "Air Max 90",
        "description": "Classic sneaker.",
        "price": Money.of("139.99", "EUR"),
        "availability": Availability.IN_STOCK,
        "image_url": "https://cdn.example.com/airmax90.jpg",
        "product_url": "https://shop.example.com/airmax90",
        "source_id": "shop-example",
    }
    defaults.update(overrides)
    return Product(**defaults)  # type: ignore[arg-type]


def test_product_constructs_with_required_fields() -> None:
    product = make_product()
    assert product.brand == "Nike"
    assert product.gtin is None
    assert product.raw == {}


@pytest.mark.parametrize("field", ["id", "brand", "title", "source_id"])
def test_product_rejects_blank_required_fields(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        make_product(**{field: "   "})


@pytest.mark.parametrize("amount", ["0", "0.00"])
def test_product_rejects_non_positive_price(amount: str) -> None:
    with pytest.raises(ValueError, match="price"):
        make_product(price=Money.of(amount, "EUR"))


def test_availability_parses_from_feed_strings() -> None:
    assert Availability("in_stock") is Availability.IN_STOCK
    assert Availability("out_of_stock") is Availability.OUT_OF_STOCK
    assert Availability("preorder") is Availability.PREORDER


def test_color_ref_normalizes_hex_to_lowercase() -> None:
    assert ColorRef("#FFAA00").hex == "#ffaa00"


@pytest.mark.parametrize("bad_hex", ["ffaa00", "#ffaa0", "#ggaa00", ""])
def test_color_ref_rejects_malformed_hex(bad_hex: str) -> None:
    with pytest.raises(ValueError, match="hex"):
        ColorRef(bad_hex)


def test_color_ref_carries_optional_lab_coordinates() -> None:
    color = ColorRef("#336699", lab=(41.4, 2.1, -30.7))
    assert color.lab == (41.4, 2.1, -30.7)


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [
        ("  NIKE Air-Max 90 (White) ", "nike air max 90 white"),
        ("T-Shirt   Basic", "t shirt basic"),
        ("Écharpe Légère", "écharpe légère"),
        ("UPPER/lower_case", "upper lower case"),
    ],
)
def test_normalize_title_lowercases_and_strips_punctuation(raw: str, normalized: str) -> None:
    assert normalize_title(raw) == normalized
