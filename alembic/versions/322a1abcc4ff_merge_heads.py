"""merge heads

Revision ID: 322a1abcc4ff
Revises: b2c3d4e5f6a1, d4e5f6a7b8c9
Create Date: 2026-06-30 17:34:54.274615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '322a1abcc4ff'
down_revision: Union[str, None] = ('b2c3d4e5f6a1', 'd4e5f6a7b8c9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
