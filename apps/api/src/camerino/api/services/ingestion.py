"""Ingestion pipeline: SourceAdapter -> normalized Product -> deduped catalog.

The SQL lookup mirrors the domain's IdentityIndex exactly: identity keys are
computed by the same deterministic functions, checked strongest-first, and a
weak match is rejected when a stronger identifier disagrees
(camerino.domain.identity.conflicts_on_stronger_key).
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from camerino.adapters.source import SourceAdapter
from camerino.api.models import CanonicalProductRow, OfferRow
from camerino.domain import Product, identity_keys
from camerino.domain.identity import KeyKind, conflicts_on_stronger_key

_KEY_COLUMNS: dict[KeyKind, str] = {
    "gtin": "gtin",
    "brand_mpn": "brand_mpn_key",
    "brand_sku": "brand_sku_key",
    "fuzzy": "fuzzy_key",
}


@dataclass(slots=True)
class IngestStats:
    """Counters describing one ingestion pass."""

    products_seen: int = 0
    canonicals_created: int = 0
    offers_created: int = 0
    offers_updated: int = 0


def _find_canonical(session: Session, product: Product) -> CanonicalProductRow | None:
    """Resolve the canonical row for a product, strongest key first."""
    for key in identity_keys(product):
        column = getattr(CanonicalProductRow, _KEY_COLUMNS[key.kind])
        candidate = session.scalars(select(CanonicalProductRow).where(column == key.value)).first()
        if candidate is not None and not conflicts_on_stronger_key(product, candidate, key.kind):
            return candidate
    return None


def _apply_identity_keys(row: CanonicalProductRow, product: Product) -> None:
    """Fill identity key columns the row is missing (never overwrite)."""
    for key in identity_keys(product):
        column = _KEY_COLUMNS[key.kind]
        if getattr(row, column) is None:
            setattr(row, column, key.value)


def _merge_descriptive_fields(row: CanonicalProductRow, product: Product) -> None:
    """Fill descriptive fields and identifiers the row is missing."""
    if row.mpn is None and product.mpn is not None:
        row.mpn = product.mpn
    if row.sku is None and product.sku is not None:
        row.sku = product.sku
    if row.color_primary_hex is None and product.color_primary_hex is not None:
        row.color_primary_hex = product.color_primary_hex
    if not row.description and product.description:
        row.description = product.description
    if not row.category and product.category:
        row.category = product.category
    if not row.image_url and product.image_url:
        row.image_url = product.image_url


def _upsert_offer(
    session: Session,
    canonical: CanonicalProductRow,
    product: Product,
    now: datetime,
    stats: IngestStats,
) -> None:
    offer = session.scalars(
        select(OfferRow).where(
            OfferRow.source_id == product.source_id, OfferRow.url == product.product_url
        )
    ).first()
    if offer is None:
        offer = OfferRow(
            canonical_product_id=canonical.id,
            source_id=product.source_id,
            external_id=product.id,
            url=product.product_url,
            affiliate_url=product.affiliate_url,
            image_url=product.image_url,
            price_minor=product.price.amount_minor,
            currency=product.price.currency,
            availability=product.availability.value,
            raw=dict(product.raw),
            first_seen_at=now,
            last_seen_at=now,
        )
        session.add(offer)
        stats.offers_created += 1
    else:
        offer.price_minor = product.price.amount_minor
        offer.currency = product.price.currency
        offer.availability = product.availability.value
        offer.affiliate_url = product.affiliate_url
        offer.raw = dict(product.raw)
        offer.last_seen_at = now
        stats.offers_updated += 1


def ingest_product(
    session: Session, product: Product, *, now: datetime, stats: IngestStats
) -> CanonicalProductRow:
    """Merge one product into the catalog."""
    stats.products_seen += 1
    canonical = _find_canonical(session, product)
    if canonical is None:
        canonical = CanonicalProductRow(
            brand=product.brand,
            title=product.title,
            created_at=now,
            updated_at=now,
        )
        session.add(canonical)
        stats.canonicals_created += 1
    _merge_descriptive_fields(canonical, product)
    _apply_identity_keys(canonical, product)
    canonical.updated_at = now
    # Ensure canonical.id is assigned before the offer references it.
    session.flush()
    _upsert_offer(session, canonical, product, now, stats)
    return canonical


async def ingest_source(
    session: Session, adapter: SourceAdapter, *, now: datetime | None = None
) -> IngestStats:
    """Ingest a source adapter's full catalog into the database session."""
    stats = IngestStats()
    timestamp = now or datetime.now(tz=UTC)
    async for product in adapter.fetch():
        ingest_product(session, product, now=timestamp, stats=stats)
    return stats
