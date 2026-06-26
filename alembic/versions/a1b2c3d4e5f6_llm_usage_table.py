"""add llm_usage table for AI billing tracking

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-06-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "a1b2c3d4e5f6"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "llm_usage",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_name", sa.String, nullable=False),
        sa.Column("model_name", sa.String, nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("reference_id", sa.String, nullable=True),
        sa.Column("reference_type", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_llm_usage_agent_name", "llm_usage", ["agent_name"])
    op.create_index("ix_llm_usage_created_at", "llm_usage", ["created_at"])


def downgrade():
    op.drop_index("ix_llm_usage_created_at", "llm_usage")
    op.drop_index("ix_llm_usage_agent_name", "llm_usage")
    op.drop_table("llm_usage")
