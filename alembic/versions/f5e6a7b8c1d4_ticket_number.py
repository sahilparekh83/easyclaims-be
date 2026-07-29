"""tickets: add ticket_number

Revision ID: f5e6a7b8c1d4
Revises: f4d5e6a7b1c3
Create Date: 2026-07-29

Changes:
- Add ticket_number (unique, not null after backfill), e.g. 'TCK-2026-000042'.
  Generated going forward inside TicketQuery.create() for every ticket.
  Backfill existing rows ordered by created_at, sequence resetting per
  calendar year to match the live generator in app/utils/code_generator.py.
"""
from alembic import op
import sqlalchemy as sa

revision = "f5e6a7b8c1d4"
down_revision = "f4d5e6a7b1c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("ticket_number", sa.String, nullable=True))

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, created_at FROM tickets ORDER BY created_at")).fetchall()
    year_counters: dict = {}
    for row_id, created_at in rows:
        year = created_at.year
        year_counters[year] = year_counters.get(year, 0) + 1
        code = f"TCK-{year}-{year_counters[year]:06d}"
        conn.execute(
            sa.text("UPDATE tickets SET ticket_number = :code WHERE id = :id"),
            {"code": code, "id": row_id},
        )

    op.alter_column("tickets", "ticket_number", nullable=False)
    op.create_unique_constraint("uq_tickets_ticket_number", "tickets", ["ticket_number"])


def downgrade() -> None:
    op.drop_constraint("uq_tickets_ticket_number", "tickets", type_="unique")
    op.drop_column("tickets", "ticket_number")
