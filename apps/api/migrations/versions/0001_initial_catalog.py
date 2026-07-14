"""Initial catalog tables: canonical_products and offers.

Revision ID: 0001
Revises:
Create Date: 2026-07-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "canonical_products",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("brand", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=512), nullable=False),
        sa.Column("image_url", sa.String(length=2048), nullable=False),
        sa.Column("gtin", sa.String(length=14), nullable=True, unique=True),
        sa.Column("mpn", sa.String(length=255), nullable=True),
        sa.Column("sku", sa.String(length=255), nullable=True),
        sa.Column("color_primary_hex", sa.String(length=7), nullable=True),
        sa.Column("brand_mpn_key", sa.String(length=512), nullable=True),
        sa.Column("brand_sku_key", sa.String(length=512), nullable=True),
        sa.Column("fuzzy_key", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_canonical_products_brand_mpn_key", "canonical_products", ["brand_mpn_key"])
    op.create_index("ix_canonical_products_brand_sku_key", "canonical_products", ["brand_sku_key"])
    op.create_index("ix_canonical_products_fuzzy_key", "canonical_products", ["fuzzy_key"])

    op.create_table(
        "offers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "canonical_product_id",
            sa.String(length=36),
            sa.ForeignKey("canonical_products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("affiliate_url", sa.String(length=2048), nullable=True),
        sa.Column("image_url", sa.String(length=2048), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("availability", sa.String(length=32), nullable=False),
        sa.Column("raw", postgresql.JSONB(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_id", "url", name="uq_offers_source_url"),
    )
    op.create_index("ix_offers_canonical_product_id", "offers", ["canonical_product_id"])


def downgrade() -> None:
    op.drop_index("ix_offers_canonical_product_id", table_name="offers")
    op.drop_table("offers")
    op.drop_index("ix_canonical_products_fuzzy_key", table_name="canonical_products")
    op.drop_index("ix_canonical_products_brand_sku_key", table_name="canonical_products")
    op.drop_index("ix_canonical_products_brand_mpn_key", table_name="canonical_products")
    op.drop_table("canonical_products")
