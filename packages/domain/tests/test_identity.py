"""Cross-merchant product identity resolution (dedup) tests."""

from collections.abc import Callable
from datetime import UTC, datetime

from camerino.domain.identity import (
    IdentityIndex,
    identity_keys,
    normalize_brand,
    normalize_title,
)
from camerino.domain.money import Money
from camerino.domain.product import Availability, Product

ProductFactory = Callable[..., Product]

NOW = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
VALID_EAN13 = "4006381333931"
OTHER_EAN13 = "4006381333818"


class TestNormalization:
    def test_brand_normalization_is_case_and_space_insensitive(self) -> None:
        assert normalize_brand(" ACME  Studio ") == normalize_brand("acme studio")

    def test_title_normalization_strips_punctuation_and_case(self) -> None:
        assert normalize_title("Wool-Coat, Navy!") == normalize_title("wool coat navy")


class TestIdentityKeys:
    def test_gtin_key_has_highest_precedence(self, make_product: ProductFactory) -> None:
        product = make_product(gtin=VALID_EAN13, mpn="M1", sku="S1")
        kinds = [key.kind for key in identity_keys(product)]
        assert kinds[0] == "gtin"
        assert kinds == ["gtin", "brand_mpn", "brand_sku", "fuzzy"]

    def test_missing_identifiers_are_skipped(self, make_product: ProductFactory) -> None:
        product = make_product()
        kinds = [key.kind for key in identity_keys(product)]
        assert kinds == ["fuzzy"]

    def test_invalid_gtin_yields_no_gtin_key(self, make_product: ProductFactory) -> None:
        product = make_product(gtin="not-a-gtin")
        kinds = [key.kind for key in identity_keys(product)]
        assert "gtin" not in kinds


class TestIdentityIndex:
    def test_same_gtin_from_two_shops_collapses_into_one_canonical(
        self, make_product: ProductFactory
    ) -> None:
        """DoD phase 1: two offers with the same GTIN collapse into one CanonicalProduct."""
        index = IdentityIndex()
        first, created_first = index.add(
            make_product(source_id="shop-a", gtin=VALID_EAN13), now=NOW
        )
        second, created_second = index.add(
            make_product(
                id="OTHER-9",
                source_id="shop-b",
                gtin=VALID_EAN13,
                title="Navy Wool Coat (FW26)",
                product_url="https://shop-b.example.com/p/9",
                price=Money(amount_minor=17900, currency="EUR"),
            ),
            now=NOW,
        )
        assert created_first is True
        assert created_second is False
        assert first is second
        assert len(index.canonicals) == 1
        assert len(first.offers) == 2
        prices = sorted(offer.price.amount_minor for offer in first.offers)
        assert prices == [17900, 19900]

    def test_brand_and_mpn_match_when_gtin_is_missing(self, make_product: ProductFactory) -> None:
        index = IdentityIndex()
        index.add(make_product(source_id="shop-a", mpn="COAT-77"), now=NOW)
        canonical, created = index.add(
            make_product(
                id="X",
                source_id="shop-b",
                mpn="COAT-77",
                title="Completely Different Listing Title",
                product_url="https://shop-b.example.com/p/x",
            ),
            now=NOW,
        )
        assert created is False
        assert len(canonical.offers) == 2

    def test_brand_and_sku_match_as_third_fallback(self, make_product: ProductFactory) -> None:
        index = IdentityIndex()
        index.add(make_product(source_id="shop-a", sku="S-42"), now=NOW)
        _, created = index.add(
            make_product(
                id="Y",
                source_id="shop-b",
                sku="S-42",
                title="Another Title Entirely",
                product_url="https://shop-b.example.com/p/y",
            ),
            now=NOW,
        )
        assert created is False

    def test_fuzzy_match_on_normalized_brand_title_color(
        self, make_product: ProductFactory
    ) -> None:
        index = IdentityIndex()
        index.add(make_product(source_id="shop-a", color_primary_hex="#1a2b3c"), now=NOW)
        _, created = index.add(
            make_product(
                id="Z",
                source_id="shop-b",
                title="  WOOL coat: Navy ",
                color_primary_hex="#1a2b3c",
                product_url="https://shop-b.example.com/p/z",
            ),
            now=NOW,
        )
        assert created is False

    def test_different_gtins_stay_distinct_even_with_same_title(
        self, make_product: ProductFactory
    ) -> None:
        index = IdentityIndex()
        index.add(make_product(source_id="shop-a", gtin=VALID_EAN13), now=NOW)
        _, created = index.add(
            make_product(
                id="W",
                source_id="shop-b",
                gtin=OTHER_EAN13,
                product_url="https://shop-b.example.com/p/w",
            ),
            now=NOW,
        )
        assert created is True
        assert len(index.canonicals) == 2

    def test_different_brands_do_not_fuzzy_match(self, make_product: ProductFactory) -> None:
        index = IdentityIndex()
        index.add(make_product(source_id="shop-a"), now=NOW)
        _, created = index.add(
            make_product(
                id="V",
                source_id="shop-b",
                brand="OtherBrand",
                product_url="https://shop-b.example.com/p/v",
            ),
            now=NOW,
        )
        assert created is True

    def test_reingesting_same_offer_updates_instead_of_duplicating(
        self, make_product: ProductFactory
    ) -> None:
        index = IdentityIndex()
        canonical, _ = index.add(make_product(gtin=VALID_EAN13), now=NOW)
        later = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)
        index.add(
            make_product(
                gtin=VALID_EAN13,
                price=Money(amount_minor=14900, currency="EUR"),
                availability=Availability.OUT_OF_STOCK,
            ),
            now=later,
        )
        assert len(canonical.offers) == 1
        offer = canonical.offers[0]
        assert offer.price.amount_minor == 14900
        assert offer.availability is Availability.OUT_OF_STOCK
        assert offer.last_seen_at == later

    def test_merge_fills_missing_identifiers_on_canonical(
        self, make_product: ProductFactory
    ) -> None:
        index = IdentityIndex()
        canonical, _ = index.add(make_product(mpn="COAT-77"), now=NOW)
        assert canonical.gtin is None
        index.add(
            make_product(
                id="Q",
                source_id="shop-b",
                mpn="COAT-77",
                gtin=VALID_EAN13,
                product_url="https://shop-b.example.com/p/q",
            ),
            now=NOW,
        )
        assert canonical.gtin == "04006381333931"
        # The canonical is now also reachable by its newly learned GTIN key.
        found, created = index.add(
            make_product(
                id="R",
                source_id="shop-c",
                gtin=VALID_EAN13,
                brand="RelabeledBrand",
                title="Relabeled listing",
                product_url="https://shop-c.example.com/p/r",
            ),
            now=NOW,
        )
        assert created is False
        assert found is canonical
