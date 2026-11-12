"""Create daily collection value snapshots.

Revision ID: f18c0a92d613
Revises: 7500aa297ad8
"""
from alembic import op
import sqlalchemy as sa

revision = "f18c0a92d613"
down_revision = "7500aa297ad8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "collection_value_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("total_quantity", sa.BigInteger(), nullable=False),
        sa.Column("priced_quantity", sa.BigInteger(), nullable=False),
        sa.Column("unpriced_quantity", sa.BigInteger(), nullable=False),
        sa.Column("estimated_value", sa.Numeric(30, 2), nullable=True),
        sa.UniqueConstraint("user_id", "snapshot_date", "currency",
                            name="uq_collection_value_snapshots_user_day_currency"),
        sa.CheckConstraint("total_quantity >= 0 AND priced_quantity >= 0 AND unpriced_quantity >= 0",
                           name="ck_collection_value_snapshots_nonnegative_quantities"),
        sa.CheckConstraint("total_quantity = priced_quantity + unpriced_quantity",
                           name="ck_collection_value_snapshots_quantity_coverage"),
        sa.CheckConstraint("estimated_value >= 0", name="ck_collection_value_snapshots_nonnegative_value"),
        sa.CheckConstraint(
            "((total_quantity = 0 OR priced_quantity > 0) AND estimated_value IS NOT NULL) "
            "OR (total_quantity > 0 AND priced_quantity = 0 AND estimated_value IS NULL)",
            name="ck_collection_value_snapshots_value_presence",
        ),
    )


def downgrade() -> None:
    op.drop_table("collection_value_snapshots")
