"""Mock source adapter: deterministic fixture catalog for CI, tests and dev."""

from collections.abc import AsyncIterator, Sequence

from camerino.adapters.source import SourceAdapter
from camerino.domain import Availability, Money, Product

# Valid EAN-13 codes used by the fixture catalog.
FIXTURE_GTIN_COAT = "4006381333931"
FIXTURE_GTIN_DRESS = "4006381333818"


def fixture_catalog(source_id: str, *, price_offset_minor: int = 0) -> list[Product]:
    """A small deterministic catalog for one mock shop.

    The same GTINs are emitted regardless of `source_id`, so ingesting two
    mock shops exercises cross-merchant dedup; `price_offset_minor` makes
    prices differ per shop.
    """
    base = f"https://{source_id}.example.com/products"
    return [
        Product(
            id="coat-navy",
            source_id=source_id,
            brand="Acme",
            title="Wool Coat Navy",
            description="A tailored navy wool coat.",
            price=Money(amount_minor=19900 + price_offset_minor, currency="EUR"),
            availability=Availability.IN_STOCK,
            image_url=f"{base}/coat-navy.jpg",
            product_url=f"{base}/coat-navy",
            category="Apparel & Accessories > Clothing > Outerwear > Coats & Jackets",
            gtin=FIXTURE_GTIN_COAT,
            mpn="ACM-COAT-NVY",
            color_primary_hex="#1f2a44",
        ),
        Product(
            id="dress-terracotta",
            source_id=source_id,
            brand="Acme",
            title="Midi Dress Terracotta",
            description="A flowing terracotta midi dress.",
            price=Money(amount_minor=8900 + price_offset_minor, currency="EUR"),
            availability=Availability.IN_STOCK,
            image_url=f"{base}/dress-terracotta.jpg",
            product_url=f"{base}/dress-terracotta",
            category="Apparel & Accessories > Clothing > Dresses",
            gtin=FIXTURE_GTIN_DRESS,
            mpn="ACM-DRS-TRC",
            color_primary_hex="#c8553d",
        ),
        Product(
            id="scarf-sage",
            source_id=source_id,
            brand="Verde",
            title="Silk Scarf Sage",
            description="A sage green silk scarf.",
            price=Money(amount_minor=3900 + price_offset_minor, currency="EUR"),
            availability=Availability.OUT_OF_STOCK,
            image_url=f"{base}/scarf-sage.jpg",
            product_url=f"{base}/scarf-sage",
            category="Apparel & Accessories > Clothing Accessories > Scarves & Shawls",
            sku="VRD-SCF-SGE",
            color_primary_hex="#9caf88",
        ),
    ]


class MockSourceAdapter(SourceAdapter):
    """SourceAdapter emitting a fixed, deterministic catalog. CI-safe: no I/O."""

    def __init__(self, source_id: str, products: Sequence[Product] | None = None) -> None:
        self._source_id = source_id
        self._products = list(products) if products is not None else fixture_catalog(source_id)

    @property
    def source_id(self) -> str:
        return self._source_id

    async def fetch(self) -> AsyncIterator[Product]:
        for product in self._products:
            yield product
