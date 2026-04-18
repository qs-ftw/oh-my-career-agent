"""Add PDF export metadata fields to jd_resume_tasks.

Revision ID: 20260413_05
Revises: 20260413_04
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa

revision = "20260413_05"
down_revision = "20260413_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No schema changes needed - PDF is generated on-demand
    # This migration exists to maintain the revision chain
    pass


def downgrade() -> None:
    pass
