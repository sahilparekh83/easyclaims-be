"""membership_plans: fee slabs + basic/advanced feature lists + co-powered flag

Revision ID: e0a1f2b3c4e5
Revises: e0a1f2b3c4e4
Create Date: 2026-07-08

Changes:
- Add fee_slabs JSONB (Advanced Assistance Service Fee slab table)
- Add basic_features_note, basic_features JSONB (Basic Assistance Services list)
- Add advanced_features_note, advanced_features JSONB (Advanced Assistance Service list)
- Add co_powered_by_easyclaims boolean (branding footer shown on plan cards)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "e0a1f2b3c4e5"
down_revision = "e0a1f2b3c4e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("membership_plans", sa.Column(
        "fee_slabs", JSONB, nullable=False, server_default="[]",
    ))
    op.add_column("membership_plans", sa.Column(
        "basic_features_note", sa.String, nullable=False, server_default="",
    ))
    op.add_column("membership_plans", sa.Column(
        "basic_features", JSONB, nullable=False, server_default="[]",
    ))
    op.add_column("membership_plans", sa.Column(
        "advanced_features_note", sa.String, nullable=False, server_default="",
    ))
    op.add_column("membership_plans", sa.Column(
        "advanced_features", JSONB, nullable=False, server_default="[]",
    ))
    op.add_column("membership_plans", sa.Column(
        "co_powered_by_easyclaims", sa.Boolean, nullable=False, server_default="true",
    ))


def downgrade() -> None:
    op.drop_column("membership_plans", "co_powered_by_easyclaims")
    op.drop_column("membership_plans", "advanced_features")
    op.drop_column("membership_plans", "advanced_features_note")
    op.drop_column("membership_plans", "basic_features")
    op.drop_column("membership_plans", "basic_features_note")
    op.drop_column("membership_plans", "fee_slabs")
