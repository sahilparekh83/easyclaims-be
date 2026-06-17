"""add_partner_to_enums

Revision ID: cb78175e0dff
Revises: 4a49ac2055a9
Create Date: 2026-06-16 16:46:36.344939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cb78175e0dff'
down_revision: Union[str, None] = '4a49ac2055a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE usertype ADD VALUE IF NOT EXISTS 'PARTNER'")
    op.execute("ALTER TYPE roletype ADD VALUE IF NOT EXISTS 'PARTNER'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; downgrade is a no-op
    pass
