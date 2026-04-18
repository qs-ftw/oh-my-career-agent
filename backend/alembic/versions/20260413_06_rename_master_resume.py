"""Rename Master Resume to role-specific names

Revision ID: 20260413_06
Revises: 20260413_05
"""
from alembic import op
from sqlalchemy import text

revision = "20260413_06"
down_revision = "20260413_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update resumes named "Master Resume" to use the role name from target_roles
    op.execute(
        text("""
            UPDATE resumes r
            SET resume_name = tr.role_name || ' - 主简历'
            FROM target_roles tr
            WHERE r.target_role_id = tr.id
              AND r.resume_name = 'Master Resume'
        """)
    )


def downgrade() -> None:
    # Revert role-specific names back to "Master Resume"
    op.execute(
        text("""
            UPDATE resumes
            SET resume_name = 'Master Resume'
            WHERE resume_name LIKE '% - 主简历'
        """)
    )
