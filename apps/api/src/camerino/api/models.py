"""ORM models for the product catalog.

The canonical/offer split mirrors the domain: one CanonicalProductRow per
garment, N OfferRow per shop listing. Identity key columns are precomputed
by the domain's deterministic key functions so dedup lookups are plain
indexed equality queries.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from camerino.api.db import Base

# JSONB on PostgreSQL, plain JSON elsewhere (SQLite in unit tests).
PortableJSON = JSON().with_variant(JSONB(), "postgresql")


def _uuid() -> str:
    return str(uuid.uuid4())


class CanonicalProductRow(Base):
    """One garment, aggregated across shops."""

    __tablename__ = "canonical_products"
    __table_args__ = (
        Index("ix_canonical_products_brand_mpn_key", "brand_mpn_key"),
        Index("ix_canonical_products_brand_sku_key", "brand_sku_key"),
        Index("ix_canonical_products_fuzzy_key", "fuzzy_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    brand: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(512), default="")
    image_url: Mapped[str] = mapped_column(String(2048), default="")
    gtin: Mapped[str | None] = mapped_column(String(14), unique=True, nullable=True)
    mpn: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(255), nullable=True)
    color_primary_hex: Mapped[str | None] = mapped_column(String(7), nullable=True)
    brand_mpn_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    brand_sku_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    fuzzy_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    offers: Mapped[list["OfferRow"]] = relationship(
        back_populates="canonical", cascade="all, delete-orphan"
    )


class OfferRow(Base):
    """One shop's listing of a canonical product."""

    __tablename__ = "offers"
    __table_args__ = (
        UniqueConstraint("source_id", "url", name="uq_offers_source_url"),
        Index("ix_offers_canonical_product_id", "canonical_product_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    canonical_product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("canonical_products.id", ondelete="CASCADE")
    )
    source_id: Mapped[str] = mapped_column(String(255))
    external_id: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(2048))
    affiliate_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    image_url: Mapped[str] = mapped_column(String(2048), default="")
    price_minor: Mapped[int] = mapped_column()
    currency: Mapped[str] = mapped_column(String(3))
    availability: Mapped[str] = mapped_column(String(32))
    raw: Mapped[dict[str, Any]] = mapped_column(PortableJSON, default=dict)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    canonical: Mapped[CanonicalProductRow] = relationship(back_populates="offers")
