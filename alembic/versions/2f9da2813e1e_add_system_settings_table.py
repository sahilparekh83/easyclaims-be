"""add_system_settings_table

Revision ID: 2f9da2813e1e
Revises: 5de232347327
Create Date: 2026-06-20 13:07:46.598257

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2f9da2813e1e'
down_revision: Union[str, None] = '5de232347327'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('system_settings',
    sa.Column('key', sa.String(), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('key')
    )


def downgrade() -> None:
    op.drop_table('system_settings')
