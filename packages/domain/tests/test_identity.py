"""Tests for cross-merchant product identity resolution and deduplication."""

from datetime import UTC, datetime

import pytest

from camerino_domain.identity import (
    IdentityKind,
    ProductDeduplicator,
    identity_key,
    normalize_gtin,
)
from camerino_domain.money import Money
from camerino_domain.product import Availability, ColorRef, Product

NOW = datetime(2026, 7, 12, 12, 0, tzinfo=UTC)


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


class TestNormalizeGtin:
    def test_pads_gtin13_to_14_digits(self) -> None:
        assert normalize_gtin("0885909950805") == "00885909950805"

    def test_strips_spaces_and_dashes(self) -> None:
        assert normalize_gtin("0 885909-950805") == "00885909950805"

    @pytest.mark.parametrize("raw", ["1234567", "123456789012345", "abcdefgh", ""])
    def test_rejects_invalid_gtins(self, raw: str) -> None:
        assert normalize_gtin(raw) is None


class TestIdentityKey:
    def test_prefers_gtin_over_everything(self) -> None:
        product = make_product(gtin="0885909950805", mpn="AM90-W", sku="SKU-1")
        key = identity_key(product)
        assert key.kind is IdentityKind.GTIN
        assert key.value == ("00885909950805",)

    def test_falls_back_to_brand_and_mpn(self) -> None:
        product = make_product(mpn="AM90-W", sku="SKU-1")
        key = identity_key(product)
        assert key.kind is IdentityKind.BRAND_MPN
        assert key.value == ("nike", "am90-w")

    def test_falls_back_to_brand_and_sku(self) -> None:
        product = make_product(sku="SKU-1")
        key = identity_key(product)
        assert key.kind is IdentityKind.BRAND_SKU
        assert key.value == ("nike", "sku-1")

    def test_falls_back_to_fuzzy_brand_title_color(self) -> None:
        product = make_product(color_primary=ColorRef("#FFFFFF"))
        key = identity_key(product)
        assert key.kind is IdentityKind.FUZZY
        assert key.value == ("nike", "air max 90", "#ffffff")

    def test_fuzzy_key_without_color_uses_empty_slot(self) -> None:
        key = identity_key(make_product())
        assert key.kind is IdentityKind.FUZZY
        assert key.value == ("nike", "air max 90", "")

    def test_invalid_gtin_falls_through_to_next_rule(self) -> None:
        product = make_product(gtin="not-a-gtin", mpn="AM90-W")
        assert identity_key(product).kind is IdentityKind.BRAND_MPN

    def test_brand_matching_is_case_insensitive(self) -> None:
        a = identity_key(make_product(brand="NIKE", mpn="AM90-W"))
        b = identity_key(make_product(brand="nike", mpn="am90-w"))
        assert a == b


class TestProductDeduplicator:
    def test_two_offers_with_same_gtin_collapse_into_one_canonical(self) -> None:
        """DoD fase 1: stesso GTIN da due negozi -> un CanonicalProduct, due Offer."""
        dedup = ProductDeduplicator()
        first = make_product(
            id="p-a",
            gtin="0885909950805",
            source_id="store-a",
            price=Money.of("139.99", "EUR"),
        )
        second = make_product(
            id="p-b",
            gtin="00885909950805",
            source_id="store-b",
            price=Money.of("129.00", "EUR"),
            product_url="https://other.example.com/am90",
        )

        canonical_a = dedup.add(first, now=NOW)
        canonical_b = dedup.add(second, now=NOW)

        assert canonical_a is canonical_b
        assert len(dedup.canonical_products()) == 1
        offers = canonical_a.offers
        assert len(offers) == 2
        assert {offer.source_id for offer in offers} == {"store-a", "store-b"}
        assert {offer.final_price for offer in offers} == {
            Money.of("139.99", "EUR"),
            Money.of("129.00", "EUR"),
        }

    def test_different_gtins_stay_separate(self) -> None:
        dedup = ProductDeduplicator()
        dedup.add(make_product(id="p-a", gtin="0885909950805"), now=NOW)
        dedup.add(make_product(id="p-b", gtin="0885909950812"), now=NOW)
        assert len(dedup.canonical_products()) == 2

    def test_brand_mpn_collapses_without_gtin(self) -> None:
        dedup = ProductDeduplicator()
        dedup.add(make_product(id="p-a", mpn="AM90-W", source_id="store-a"), now=NOW)
        canonical = dedup.add(make_product(id="p-b", mpn="am90-w", source_id="store-b"), now=NOW)
        assert len(dedup.canonical_products()) == 1
        assert len(canonical.offers) == 2

    def test_fuzzy_requires_matching_color(self) -> None:
        dedup = ProductDeduplicator()
        dedup.add(
            make_product(id="p-a", color_primary=ColorRef("#ffffff"), source_id="a"),
            now=NOW,
        )
        dedup.add(
            make_product(id="p-b", color_primary=ColorRef("#000000"), source_id="b"),
            now=NOW,
        )
        assert len(dedup.canonical_products()) == 2

    def test_same_source_reappearing_updates_offer_instead_of_duplicating(self) -> None:
        dedup = ProductDeduplicator()
        later = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
        dedup.add(make_product(gtin="0885909950805", source_id="store-a"), now=NOW)
        canonical = dedup.add(
            make_product(
                gtin="0885909950805",
                source_id="store-a",
                price=Money.of("99.00", "EUR"),
                availability=Availability.OUT_OF_STOCK,
            ),
            now=later,
        )
        assert len(canonical.offers) == 1
        offer = canonical.offers[0]
        assert offer.final_price == Money.of("99.00", "EUR")
        assert offer.availability is Availability.OUT_OF_STOCK
        assert offer.last_seen_at == later

    def test_canonical_keeps_first_seen_representative_data(self) -> None:
        dedup = ProductDeduplicator()
        canonical = dedup.add(
            make_product(gtin="0885909950805", title="Air Max 90", source_id="a"),
            now=NOW,
        )
        dedup.add(
            make_product(gtin="0885909950805", title="AIR MAX 90 SNEAKER!!", source_id="b"),
            now=NOW,
        )
        assert canonical.title == "Air Max 90"
