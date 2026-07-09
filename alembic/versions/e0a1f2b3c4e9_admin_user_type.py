"""usertype: add ADMIN value — internal admin-panel staff who are not SUPERADMIN

Revision ID: e0a1f2b3c4e9
Revises: e0a1f2b3c4e8
Create Date: 2026-07-08

Changes:
- Adds 'ADMIN' to the usertype enum. Users of this type log into the admin
  portal like SUPERADMIN, but get NO automatic access — what they can see and
  do is entirely governed by the roles/permissions assigned to them (unlike
  SUPERADMIN, which always bypasses the permission grid).
"""
from alembic import op

revision = "e0a1f2b3c4e9"
down_revision = "e0a1f2b3c4e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE usertype ADD VALUE IF NOT EXISTS 'ADMIN'")


def downgrade() -> None:
    # Postgres does not support removing enum values — no-op downgrade.
    pass
