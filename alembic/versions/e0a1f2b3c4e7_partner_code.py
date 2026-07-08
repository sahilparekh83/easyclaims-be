"""partners: add unique auto-generated partner_code

Revision ID: e0a1f2b3c4e7
Revises: e0a1f2b3c4e6
Create Date: 2026-07-08

Changes:
- Add partner_code column (unique), backfilled for existing rows with a fixed
  'ECPTR' prefix + sequential number (e.g. 'ECPTR-0001'), ordered by created_at
"""
from alembic import op
import sqlalchemy as sa

revision = "e0a1f2b3c4e7"
down_revision = "e0a1f2b3c4e6"
branch_labels = None
depends_on = None

_PREFIX = "ECPTR"


def upgrade() -> None:
    op.add_column("partners", sa.Column("partner_code", sa.String, nullable=True))

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id FROM partners ORDER BY created_at")).fetchall()
    for i, row in enumerate(rows, start=1):
        code = f"{_PREFIX}-{i:04d}"
        conn.execute(
            sa.text("UPDATE partners SET partner_code = :code WHERE id = :id"),
            {"code": code, "id": row[0]},
        )

    op.alter_column("partners", "partner_code", nullable=False)
    op.create_unique_constraint("uq_partners_partner_code", "partners", ["partner_code"])


def downgrade() -> None:
    op.drop_constraint("uq_partners_partner_code", "partners", type_="unique")
    op.drop_column("partners", "partner_code")
