"""Add apply metadata columns to update_suggestions.

Revision ID: 20260413_04
Revises: 20260413_03
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260413_04"
down_revision = "20260413_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "update_suggestions",
        sa.Column("applied_resume_version_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "update_suggestions",
        sa.Column("review_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "update_suggestions",
        sa.Column("apply_result_json", postgresql.JSONB(), nullable=True),
    )
    op.create_foreign_key(
        "fk_update_suggestions_applied_version",
        "update_suggestions",
        "resume_versions",
        ["applied_resume_version_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_update_suggestions_applied_version", "update_suggestions", type_="foreignkey")
    op.drop_column("update_suggestions", "apply_result_json")
    op.drop_column("update_suggestions", "review_notes")
    op.drop_column("update_suggestions", "applied_resume_version_id")
