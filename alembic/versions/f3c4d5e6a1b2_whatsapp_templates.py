"""whatsapp_templates table

Revision ID: f3c4d5e6a1b2
Revises: f2b3c4d5e6a1
Create Date: 2026-07-18

Changes:
- New whatsapp_templates table holding Meta WhatsApp Cloud API template
  metadata (template name, language, approval status, header type, ordered
  variable list) — separate from email_templates since Meta's approved
  templates are structurally different (fixed copy + positional {{n}}
  placeholders) from the free-form Jinja bodies used for email/Twilio.
  Same partner-override shape as email_templates (partner_id NULL = system
  default, one row per slug per scope).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "f3c4d5e6a1b2"
down_revision = "f2b3c4d5e6a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("partner_id", UUID(as_uuid=True), sa.ForeignKey("partners.id"), nullable=True),
        sa.Column("meta_template_name", sa.String(), nullable=True),
        sa.Column("meta_template_language", sa.String(), nullable=False, server_default="en"),
        sa.Column("meta_template_status", sa.String(), nullable=True),
        sa.Column("header_type", sa.String(), nullable=True),
        sa.Column("variable_order", JSONB, nullable=False, server_default="[]"),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_whatsapp_templates_slug", "whatsapp_templates", ["slug"], unique=False)
    op.create_index(
        "uq_whatsapp_templates_slug_default", "whatsapp_templates", ["slug"],
        unique=True, postgresql_where=sa.text("partner_id IS NULL"),
    )
    op.create_index(
        "uq_whatsapp_templates_slug_partner", "whatsapp_templates", ["slug", "partner_id"],
        unique=True, postgresql_where=sa.text("partner_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_whatsapp_templates_slug_partner", table_name="whatsapp_templates")
    op.drop_index("uq_whatsapp_templates_slug_default", table_name="whatsapp_templates")
    op.drop_index("ix_whatsapp_templates_slug", table_name="whatsapp_templates")
    op.drop_table("whatsapp_templates")
