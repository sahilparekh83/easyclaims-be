"""merge_heads

Revision ID: 5de232347327
Revises: 4873e1f01972, a1b2c3d4e5f6
Create Date: 2026-06-18 17:14:14.668820

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5de232347327'
down_revision: Union[str, None] = ('4873e1f01972', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
