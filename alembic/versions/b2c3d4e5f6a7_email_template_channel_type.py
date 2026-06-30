"""add channel_type to email_templates, make subject nullable

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-06-30

Changes:
- Add channel_type column to email_templates (default 'email')
- Make subject nullable (WhatsApp templates don't have a subject)
"""
from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a7"
down_revision = "d31481f19fba"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "email_templates",
        sa.Column("channel_type", sa.String(), nullable=False, server_default="email"),
    )
    op.alter_column("email_templates", "subject", nullable=True)


def downgrade():
    op.alter_column("email_templates", "subject", nullable=False)
    op.drop_column("email_templates", "channel_type")
