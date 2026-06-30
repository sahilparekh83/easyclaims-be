"""policy renewal fields: previous_policy_id and renewal_confidence

Revision ID: b2c3d4e5f6a1
Revises: d31481f19fba
Create Date: 2026-06-30

Changes:
- Add previous_policy_id (UUID FK nullable) to policies
- Add renewal_confidence (VARCHAR nullable: 'high'/'low') to policies
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "b2c3d4e5f6a1"
down_revision = "d31481f19fba"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("policies", sa.Column(
        "previous_policy_id",
        UUID(as_uuid=True),
        sa.ForeignKey("policies.id"),
        nullable=True,
    ))
    op.add_column("policies", sa.Column(
        "renewal_confidence",
        sa.String,
        nullable=True,
    ))


def downgrade():
    op.drop_column("policies", "renewal_confidence")
    op.drop_column("policies", "previous_policy_id")
