"""users: add member_code and agent_code

Revision ID: f4d5e6a7b1c3
Revises: f3c4d5e6a1b2
Create Date: 2026-07-29

Changes:
- Add member_code (unique, nullable) — set for CUSTOMER-type users going
  forward via MemberService.create_member(), e.g. 'MEM-2026-000042'.
- Add agent_code (unique, nullable) — set when the CLAIMS_AGENT role is
  granted to a user, e.g. 'AGT-2026-000042'.
  Both nullable since most users are neither a member nor an agent. Backfill
  existing rows ordered by created_at, sequence resetting per calendar year
  to match the live generator in app/utils/code_generator.py.
"""
from alembic import op
import sqlalchemy as sa

revision = "f4d5e6a7b1c3"
down_revision = "f3c4d5e6a1b2"
branch_labels = None
depends_on = None


def _backfill(conn, rows, prefix, column, table="users"):
    year_counters: dict = {}
    for row_id, created_at in rows:
        year = created_at.year
        year_counters[year] = year_counters.get(year, 0) + 1
        code = f"{prefix}-{year}-{year_counters[year]:06d}"
        conn.execute(
            sa.text(f"UPDATE {table} SET {column} = :code WHERE id = :id"),
            {"code": code, "id": row_id},
        )


def upgrade() -> None:
    op.add_column("users", sa.Column("member_code", sa.String, nullable=True))
    op.add_column("users", sa.Column("agent_code", sa.String, nullable=True))

    conn = op.get_bind()

    member_rows = conn.execute(sa.text(
        "SELECT id, created_at FROM users WHERE user_type = 'CUSTOMER' ORDER BY created_at"
    )).fetchall()
    _backfill(conn, member_rows, "MEM", "member_code")

    agent_rows = conn.execute(sa.text(
        """
        SELECT u.id, u.created_at FROM users u
        JOIN user_roles ur ON ur.user_id = u.id AND ur.is_active = true
        JOIN roles r ON r.id = ur.role_id
        WHERE r.role_name = 'CLAIMS_AGENT'
        ORDER BY u.created_at
        """
    )).fetchall()
    _backfill(conn, agent_rows, "AGT", "agent_code")

    op.create_unique_constraint("uq_users_member_code", "users", ["member_code"])
    op.create_unique_constraint("uq_users_agent_code", "users", ["agent_code"])


def downgrade() -> None:
    op.drop_constraint("uq_users_agent_code", "users", type_="unique")
    op.drop_constraint("uq_users_member_code", "users", type_="unique")
    op.drop_column("users", "agent_code")
    op.drop_column("users", "member_code")
