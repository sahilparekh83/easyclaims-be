"""partner_card_branding

Revision ID: e0a1f2b3c4e2
Revises: e0a1f2b3c4e1
Create Date: 2026-07-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0a1f2b3c4e2'
down_revision: Union[str, None] = 'e0a1f2b3c4e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('partners', sa.Column('card_logo_key', sa.String(), nullable=True))
    op.add_column('partners', sa.Column('card_color', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('partners', 'card_color')
    op.drop_column('partners', 'card_logo_key')
