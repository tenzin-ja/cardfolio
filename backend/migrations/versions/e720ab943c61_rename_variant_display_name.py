"""Rename display_name to variant_name.

Revision ID: e720ab943c61
Revises: c1544ded4c34
"""

from alembic import op


revision = "e720ab943c61"
down_revision = "c1544ded4c34"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the existing column so any saved names stay intact.
    op.alter_column("card_variants", "display_name", new_column_name="variant_name")


def downgrade() -> None:
    op.alter_column("card_variants", "variant_name", new_column_name="display_name")
