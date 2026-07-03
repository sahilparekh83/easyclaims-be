"""motor_policy_fields

Revision ID: e0a1f2b3c4d8
Revises: e0a1f2b3c4d7
Create Date: 2026-07-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'e0a1f2b3c4d8'
down_revision: Union[str, None] = 'e0a1f2b3c4d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('policies', sa.Column('vehicle_number', sa.String(), nullable=True))
    op.add_column('policies', sa.Column('vehicle_type', sa.String(), nullable=True))
    op.add_column('policies', sa.Column('vehicle_owner_family_member_id', UUID(as_uuid=True),
                                        sa.ForeignKey('family_members.id'), nullable=True))


def downgrade() -> None:
    op.drop_column('policies', 'vehicle_owner_family_member_id')
    op.drop_column('policies', 'vehicle_type')
    op.drop_column('policies', 'vehicle_number')
