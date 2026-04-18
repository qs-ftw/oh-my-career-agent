"""add education table and FK columns

Revision ID: 20260417_01
Revises: 20260416_01
Create Date: 2026-04-17
"""
from alembic import op
import sqlalchemy as sa

revision = "20260417_01"
down_revision = "20260416_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "educations",
        sa.Column("profile_id", sa.UUID(), nullable=False),
        sa.Column("institution_name", sa.String(200), nullable=False),
        sa.Column("institution_url", sa.String(500), nullable=False, server_default=""),
        sa.Column("degree", sa.String(50), nullable=False, server_default=""),
        sa.Column("field_of_study", sa.String(200), nullable=False, server_default=""),
        sa.Column("location", sa.String(100), nullable=False, server_default=""),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("gpa", sa.String(20), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["career_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_educations_profile_id"), "educations", ["profile_id"], unique=False)

    op.add_column("projects", sa.Column("education_id", sa.UUID(), nullable=True))
    op.create_foreign_key(None, "projects", "educations", ["education_id"], ["id"], ondelete="SET NULL")
    op.create_index(op.f("ix_projects_education_id"), "projects", ["education_id"], unique=False)

    op.add_column("achievements", sa.Column("education_id", sa.UUID(), nullable=True))
    op.create_foreign_key(None, "achievements", "educations", ["education_id"], ["id"], ondelete="SET NULL")
    op.create_index(op.f("ix_achievements_education_id"), "achievements", ["education_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_achievements_education_id"), table_name="achievements")
    op.drop_column("achievements", "education_id")
    op.drop_index(op.f("ix_projects_education_id"), table_name="projects")
    op.drop_column("projects", "education_id")
    op.drop_index(op.f("ix_educations_profile_id"), table_name="educations")
    op.drop_table("educations")
