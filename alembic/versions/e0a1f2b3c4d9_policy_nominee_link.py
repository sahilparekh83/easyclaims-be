"""policy_nominee_link

Revision ID: e0a1f2b3c4d9
Revises: e0a1f2b3c4d8
Create Date: 2026-07-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'e0a1f2b3c4d9'
down_revision: Union[str, None] = 'e0a1f2b3c4d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "policy_nominees",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("policy_id", UUID(as_uuid=True), sa.ForeignKey("policies.id"), nullable=False),
        sa.Column("nominee_id", UUID(as_uuid=True), sa.ForeignKey("nominees.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("policy_id", "nominee_id", name="uq_policy_nominee"),
    )


def downgrade() -> None:
    op.drop_table("policy_nominees")
