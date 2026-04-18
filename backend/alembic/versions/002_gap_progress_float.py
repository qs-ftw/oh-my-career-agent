"""Change gap_items.progress from integer to float.

Revision ID: 002_gap_float
Revises: dc1046711b25
Create Date: 2026-04-12
"""

from alembic import op
import sqlalchemy as sa

revision = "002_gap_float"
down_revision = "dc1046711b25"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "gap_items",
        "progress",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "gap_items",
        "progress",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=False,
    )
