"""Generic affiliate feed adapter (Awin/CJ/Impact-style CSV or flat XML).

Column names differ per network, so the mapping is configuration: a
preset for Awin ships here, other networks only need a new mapping.
The affiliate deep link is kept on ``Product.affiliate_url`` (disclosure
is rendered wherever that link is shown — hard invariant #5).
"""

from __future__ import annotations

import csv
import io
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal
from xml.etree import ElementTree

import httpx

from camerino_domain import Availability, Money, Product

FeedFormat = Literal["csv", "xml"]


@dataclass(frozen=True, slots=True)
class AffiliateFieldMapping:
    """Maps a network's column/tag names onto the normalized Product fields."""

    id: str
    title: str
    description: str
    brand: str
    price: str
    currency: str
    affiliate_url: str
    image_url: str
    availability: str
    product_url: str | None = None
    gtin: str | None = None
    mpn: str | None = None
    sku: str | None = None
    in_stock_values: frozenset[str] = frozenset({"1", "true", "yes", "y", "in stock", "in_stock"})


AWIN_MAPPING = AffiliateFieldMapping(
    id="aw_product_id",
    title="product_name",
    description="description",
    brand="brand_name",
    price="search_price",
    currency="currency",
    affiliate_url="aw_deep_link",
    product_url="merchant_deep_link",
    image_url="merchant_image_url",
    availability="in_stock",
    gtin="ean",
    mpn="mpn",
    sku="merchant_product_id",
)


class AffiliateFeedAdapter:
    """SourceAdapter over an affiliate network product feed."""

    def __init__(
        self,
        source_id: str,
        loader: Callable[[], Awaitable[str]],
        mapping: AffiliateFieldMapping,
        feed_format: FeedFormat,
        *,
        xml_record_tag: str = "product",
    ) -> None:
        self._source_id = source_id
        self._loader = loader
        self._mapping = mapping
        self._format: FeedFormat = feed_format
        self._xml_record_tag = xml_record_tag
        self.skipped_records = 0

    @classmethod
    def from_content(
        cls,
        source_id: str,
        content: str,
        mapping: AffiliateFieldMapping,
        feed_format: FeedFormat,
        *,
        xml_record_tag: str = "product",
    ) -> AffiliateFeedAdapter:
        async def loader() -> str:
            return content

        return cls(source_id, loader, mapping, feed_format, xml_record_tag=xml_record_tag)

    @classmethod
    def from_url(
        cls,
        source_id: str,
        url: str,
        mapping: AffiliateFieldMapping,
        feed_format: FeedFormat,
        *,
        client: httpx.AsyncClient | None = None,
        xml_record_tag: str = "product",
    ) -> AffiliateFeedAdapter:
        async def loader() -> str:
            http = client or httpx.AsyncClient()
            try:
                response = await http.get(url)
                response.raise_for_status()
                return response.text
            finally:
                if client is None:
                    await http.aclose()

        return cls(source_id, loader, mapping, feed_format, xml_record_tag=xml_record_tag)

    @property
    def source_id(self) -> str:
        return self._source_id

    async def fetch_products(self) -> AsyncIterator[Product]:
        content = await self._loader()
        self.skipped_records = 0
        if self._format == "csv":
            records = _parse_csv(content)
        else:
            records = _parse_xml(content, self._xml_record_tag)
        for record in records:
            product = self._to_product(record)
            if product is None:
                self.skipped_records += 1
                continue
            yield product

    def _to_product(self, record: dict[str, str]) -> Product | None:
        mapping = self._mapping

        def column(name: str | None) -> str:
            return record.get(name, "").strip() if name else ""

        try:
            price = Money(Decimal(column(mapping.price)), column(mapping.currency))
        except (InvalidOperation, ValueError):
            return None
        availability = (
            Availability.IN_STOCK
            if column(mapping.availability).casefold() in mapping.in_stock_values
            else Availability.OUT_OF_STOCK
        )
        affiliate_url = column(mapping.affiliate_url)
        product_url = column(mapping.product_url) or affiliate_url
        try:
            return Product(
                id=column(mapping.id),
                brand=column(mapping.brand),
                title=column(mapping.title),
                description=column(mapping.description),
                price=price,
                availability=availability,
                image_url=column(mapping.image_url),
                product_url=product_url,
                source_id=self._source_id,
                gtin=column(mapping.gtin) or None,
                mpn=column(mapping.mpn) or None,
                sku=column(mapping.sku) or None,
                affiliate_url=affiliate_url or None,
                raw=dict(record),
            )
        except ValueError:
            return None


def _parse_csv(content: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content))
    return [
        {key: (value or "").strip() for key, value in row.items() if key is not None}
        for row in reader
    ]


def _parse_xml(content: str, record_tag: str) -> list[dict[str, str]]:
    root = ElementTree.fromstring(content)
    records: list[dict[str, str]] = []
    for element in root.iter(record_tag):
        records.append({child.tag: (child.text or "").strip() for child in element})
    return records
