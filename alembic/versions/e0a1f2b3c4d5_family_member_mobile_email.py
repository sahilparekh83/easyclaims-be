"""family_member_mobile_email

Revision ID: e0a1f2b3c4d5
Revises: 322a1abcc4ff
Create Date: 2026-07-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0a1f2b3c4d5'
down_revision: Union[str, None] = '322a1abcc4ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('family_members', sa.Column('mobile_no', sa.String(), nullable=True))
    op.add_column('family_members', sa.Column('email', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('family_members', 'email')
    op.drop_column('family_members', 'mobile_no')
