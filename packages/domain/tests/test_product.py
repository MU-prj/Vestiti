"""Product entity validation tests."""

from collections.abc import Callable

import pytest

from camerino.domain.product import Availability, Lab, Product

ProductFactory = Callable[..., Product]


def test_product_holds_normalized_fields(make_product: ProductFactory) -> None:
    product = make_product(gtin="4006381333931", color_primary_hex="#1A2B3C")
    assert product.brand == "Acme"
    assert product.availability is Availability.IN_STOCK
    assert product.color_primary_hex == "#1a2b3c"


@pytest.mark.parametrize("field", ["id", "source_id", "brand", "title", "product_url"])
def test_product_rejects_blank_required_fields(make_product: ProductFactory, field: str) -> None:
    with pytest.raises(ValueError, match=field):
        make_product(**{field: "  "})


@pytest.mark.parametrize("bad_hex", ["1a2b3c", "#12", "#xyzxyz", "#1a2b3c4d"])
def test_product_rejects_malformed_hex_colors(make_product: ProductFactory, bad_hex: str) -> None:
    with pytest.raises(ValueError, match="color_primary_hex"):
        make_product(color_primary_hex=bad_hex)


def test_lab_is_immutable(make_product: ProductFactory) -> None:
    lab = Lab(l_star=53.2, a_star=80.1, b_star=67.2)
    product = make_product(color_primary_hex="#ff0000", color_primary_lab=lab)
    assert product.color_primary_lab == Lab(l_star=53.2, a_star=80.1, b_star=67.2)
    with pytest.raises(AttributeError):
        lab.l_star = 0.0  # type: ignore[misc]


def test_product_is_frozen(make_product: ProductFactory) -> None:
    product = make_product()
    with pytest.raises(AttributeError):
        product.title = "new"  # type: ignore[misc]
