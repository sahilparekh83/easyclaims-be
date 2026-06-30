"""partner_change_request_table

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-06-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d4e5f6a7b8c9"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "partner_change_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("requested_fields", postgresql.JSONB(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_partner_change_requests_partner_id",
                    "partner_change_requests", ["partner_id"])
    op.create_index("ix_partner_change_requests_status",
                    "partner_change_requests", ["status"])


def downgrade():
    op.drop_index("ix_partner_change_requests_status", table_name="partner_change_requests")
    op.drop_index("ix_partner_change_requests_partner_id", table_name="partner_change_requests")
    op.drop_table("partner_change_requests")
