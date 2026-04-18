"""add interactive analysis fields to achievements

Revision ID: 20260416_01
Revises: 6c3da8c67690
Create Date: 2026-04-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260416_01"
down_revision = "6c3da8c67690"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("achievements", sa.Column("analysis_chat", JSONB, nullable=True))
    op.add_column("achievements", sa.Column("enrichment_suggestions", JSONB, nullable=True))
    op.add_column("achievements", sa.Column("polished_content", JSONB, nullable=True))
    op.add_column("achievements", sa.Column("display_format", sa.String(20), nullable=False, server_default="raw"))


def downgrade() -> None:
    op.drop_column("achievements", "display_format")
    op.drop_column("achievements", "polished_content")
    op.drop_column("achievements", "enrichment_suggestions")
    op.drop_column("achievements", "analysis_chat")
