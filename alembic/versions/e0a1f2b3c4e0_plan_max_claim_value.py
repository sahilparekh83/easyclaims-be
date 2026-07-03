"""plan_max_claim_value

Revision ID: e0a1f2b3c4e0
Revises: e0a1f2b3c4d9
Create Date: 2026-07-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0a1f2b3c4e0'
down_revision: Union[str, None] = 'e0a1f2b3c4d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('membership_plans', sa.Column('max_claim_value', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column('membership_plans', 'max_claim_value')
