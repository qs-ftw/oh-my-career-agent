"""Add candidate_profiles table.

Revision ID: 20260413_01
Revises: 002_gap_float
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260413_01"
down_revision = "002_gap_float"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candidate_profiles",
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("headline", sa.String(length=256), nullable=False, server_default=""),
        sa.Column("exit_story", sa.Text(), nullable=False, server_default=""),
        sa.Column("superpowers_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("proof_points_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("compensation_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("location_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("preferences_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("constraints_json", postgresql.JSONB(), nullable=False, server_default="{}"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_candidate_profiles_workspace_id", "candidate_profiles", ["workspace_id"])
    op.create_index("ix_candidate_profiles_user_id", "candidate_profiles", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_candidate_profiles_user_id")
    op.drop_index("ix_candidate_profiles_workspace_id")
    op.drop_table("candidate_profiles")
