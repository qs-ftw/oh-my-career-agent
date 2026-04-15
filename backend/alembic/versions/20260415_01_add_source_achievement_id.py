"""add source_achievement_id to update_suggestions

Revision ID: 20260415_01
Revises: da4d2ca574d9
Create Date: 2026-04-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260415_01'
down_revision: Union[str, None] = 'da4d2ca574d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('update_suggestions', sa.Column(
        'source_achievement_id',
        postgresql.UUID(as_uuid=True),
        nullable=True,
    ))
    op.create_foreign_key(
        'fk_update_suggestions_source_achievement_id',
        'update_suggestions', 'achievements',
        ['source_achievement_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_update_suggestions_source_achievement_id',
        'update_suggestions',
        type_='foreignkey',
    )
    op.drop_column('update_suggestions', 'source_achievement_id')
