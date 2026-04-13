"""Add review artifact columns to jd_resume_tasks.

Revision ID: 20260413_03
Revises: 20260413_02
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260413_03"
down_revision = "20260413_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jd_resume_tasks",
        sa.Column("review_report_json", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "jd_resume_tasks",
        sa.Column("evidence_matrix_json", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "jd_resume_tasks",
        sa.Column("interview_plan_json", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "jd_resume_tasks",
        sa.Column("decision_summary", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("jd_resume_tasks", "decision_summary")
    op.drop_column("jd_resume_tasks", "interview_plan_json")
    op.drop_column("jd_resume_tasks", "evidence_matrix_json")
    op.drop_column("jd_resume_tasks", "review_report_json")
