"""user activity, notifications, policy_family_members

Revision ID: f1a2b3c4d5e6
Revises: e3f8a1b2c4d5
Create Date: 2026-06-16

Changes:
- Create user_activity table (first_login_at, last_login_at, login_count, has_logged_in)
- Create policy_family_members table (many-to-many policy <-> family_members)
- Create notifications table (UI notifications for partner/admin)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "f1a2b3c4d5e6"
down_revision = "e3f8a1b2c4d5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_activity",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("first_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("login_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("has_logged_in", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "policy_family_members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("policy_id", UUID(as_uuid=True), sa.ForeignKey("policies.id"), nullable=False),
        sa.Column("family_member_id", UUID(as_uuid=True), sa.ForeignKey("family_members.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("policy_id", "family_member_id", name="uq_policy_family_member"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("recipient_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("body", sa.String, nullable=True),
        sa.Column("ref_id", sa.String, nullable=True),
        sa.Column("ref_type", sa.String, nullable=True),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("ix_notifications_recipient", "notifications", ["recipient_user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])


def downgrade():
    op.drop_table("notifications")
    op.drop_table("policy_family_members")
    op.drop_table("user_activity")
