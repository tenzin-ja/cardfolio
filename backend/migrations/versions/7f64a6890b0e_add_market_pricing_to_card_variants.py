"""add market pricing to card variants

Revision ID: 7f64a6890b0e
Revises: b947a39991a6
Create Date: 2026-08-16 14:30:24.317874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f64a6890b0e'
down_revision: Union[str, Sequence[str], None] = 'b947a39991a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "card_variants",
        sa.Column(
            "market_price",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
    )

    op.add_column(
        "card_variants",
        sa.Column(
            "market_price_source",
            sa.String(length=50),
            nullable=True,
        ),
    )

    op.add_column(
        "card_variants",
        sa.Column(
            "market_price_updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "card_variants",
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default=sa.text("'USD'"),
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("card_variants", "currency")
    op.drop_column("card_variants", "market_price_updated_at")
    op.drop_column("card_variants", "market_price_source")
    op.drop_column("card_variants", "market_price")
    # ### end Alembic commands ###
