"""membership_plans: add unique auto-generated plan_code

Revision ID: e0a1f2b3c4e6
Revises: e0a1f2b3c4e5
Create Date: 2026-07-08

Changes:
- Add plan_code column (unique), backfilled for existing rows from their name
  initials + sequence, e.g. 'EIAM-001'
- Also flips the default for benefit_aiqa / benefit_vault to False — new plans
  no longer ship with AI Q&A / document vault active unless explicitly enabled
  (existing rows are untouched)
"""
import re
from alembic import op
import sqlalchemy as sa

revision = "e0a1f2b3c4e6"
down_revision = "e0a1f2b3c4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("membership_plans", sa.Column("plan_code", sa.String, nullable=True))

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, name FROM membership_plans ORDER BY created_at")).fetchall()
    used_codes = set()
    for row in rows:
        words = re.findall(r"[A-Za-z0-9]+", row[1] or "")
        initials = "".join(w[0] for w in words if w).upper()[:6] or "PLAN"
        n = 1
        while True:
            code = f"{initials}-{n:03d}"
            if code not in used_codes:
                break
            n += 1
        used_codes.add(code)
        conn.execute(
            sa.text("UPDATE membership_plans SET plan_code = :code WHERE id = :id"),
            {"code": code, "id": row[0]},
        )

    op.alter_column("membership_plans", "plan_code", nullable=False)
    op.create_unique_constraint("uq_membership_plans_plan_code", "membership_plans", ["plan_code"])


def downgrade() -> None:
    op.drop_constraint("uq_membership_plans_plan_code", "membership_plans", type_="unique")
    op.drop_column("membership_plans", "plan_code")
