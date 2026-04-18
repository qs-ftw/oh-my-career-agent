"""Add interview_stories table.

Revision ID: 20260413_02
Revises: 20260413_01
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260413_02"
down_revision = "20260413_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "interview_stories",
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("theme", sa.String(length=128), nullable=False, server_default="general"),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_ref_id", sa.UUID(), nullable=True),
        sa.Column("story_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("best_for_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_interview_stories_workspace_id", "interview_stories", ["workspace_id"])
    op.create_index("ix_interview_stories_user_id", "interview_stories", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_interview_stories_user_id")
    op.drop_index("ix_interview_stories_workspace_id")
    op.drop_table("interview_stories")
