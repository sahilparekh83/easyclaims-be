"""float_ledger

Revision ID: e0a1f2b3c4d7
Revises: e0a1f2b3c4d6
Create Date: 2026-07-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'e0a1f2b3c4d7'
down_revision: Union[str, None] = 'e0a1f2b3c4d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('partners', sa.Column('float_balance', sa.BigInteger(), nullable=False, server_default="0"))
    op.add_column('partners', sa.Column('low_float_threshold', sa.BigInteger(), nullable=False, server_default="0"))

    op.create_table(
        "float_transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", UUID(as_uuid=True), sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("balance_after", sa.BigInteger(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("ref_type", sa.String(), nullable=True),
        sa.Column("ref_id", sa.String(), nullable=True),
        sa.Column("is_reconciled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reconciled_by", sa.String(), nullable=True),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_float_transactions_partner_id", "float_transactions", ["partner_id"])
    op.create_index("ix_float_transactions_type", "float_transactions", ["type"])


def downgrade() -> None:
    op.drop_index("ix_float_transactions_type", table_name="float_transactions")
    op.drop_index("ix_float_transactions_partner_id", table_name="float_transactions")
    op.drop_table("float_transactions")
    op.drop_column('partners', 'low_float_threshold')
    op.drop_column('partners', 'float_balance')
