"""partner_types master table + partner_type_id FK on partners

Revision ID: e0a1f2b3c4e4
Revises: e0a1f2b3c4e3
Create Date: 2026-07-08

Changes:
- Create partner_types master table with seed data (13 onboarding partner types)
- Add partner_type_id FK to partners, backfilled by matching the existing
  partner_type string (case-insensitive) to a seeded type
- partner_type (string) column is kept for backward-compatible display/reporting,
  normalized to the canonical seeded name during backfill
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

revision = "e0a1f2b3c4e4"
down_revision = "e0a1f2b3c4e3"
branch_labels = None
depends_on = None

_DEFAULT_TYPES = [
    ("Individual",                 "individual",                 "Individual partner"),
    ("Channel Partner",            "channel_partner",            "Channel partner"),
    ("Insurance Broker",           "insurance_broker",           "Licensed insurance broker"),
    ("Corporate Agent",            "corporate_agent",            "Corporate insurance agent"),
    ("Insurance Marketing Firm",   "insurance_marketing_firm",   "Insurance marketing firm (IMF)"),
    ("Retail Agent",               "retail_agent",               "Retail insurance agent"),
    ("OEM",                        "oem",                        "Original equipment manufacturer"),
    ("NBFC",                       "nbfc",                        "Non-banking financial company"),
    ("Fintech",                    "fintech",                    "Fintech partner"),
    ("Association",                "association",                "Association / trade body"),
    ("Affinity Partner",           "affinity_partner",           "Affinity partner"),
    ("Corporate Employer",         "corporate_employer",         "Corporate employer"),
    ("Other",                      "other",                      "Other partner type"),
]

# Best-effort mapping from legacy free-text values to the new seeded codes.
_LEGACY_ALIASES = {
    "broker": "insurance_broker",
    "corporate": "corporate_agent",
    "ngo": "other",
}


def upgrade() -> None:
    # ── 1. Create partner_types table ────────────────────────────────────────
    op.create_table(
        "partner_types",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("code", sa.String, nullable=False, unique=True),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── 2. Seed default partner types ────────────────────────────────────────
    conn = op.get_bind()
    code_to_id = {}
    name_to_id = {}
    for name, code, desc in _DEFAULT_TYPES:
        tid = str(uuid.uuid4())
        code_to_id[code] = tid
        name_to_id[name.lower()] = tid
        conn.execute(
            sa.text(
                "INSERT INTO partner_types (id, name, code, description) "
                "VALUES (:id, :name, :code, :desc)"
            ),
            {"id": tid, "name": name, "code": code, "desc": desc},
        )

    # ── 3. Add partner_type_id column to partners (nullable while migrating) ─
    op.add_column("partners", sa.Column(
        "partner_type_id", UUID(as_uuid=True),
        sa.ForeignKey("partner_types.id"),
        nullable=True,
    ))

    # ── 4. Backfill: map existing free-text partner_type to the new FK ───────
    fallback_id = code_to_id["other"]
    rows = conn.execute(sa.text("SELECT id, partner_type FROM partners")).fetchall()
    for row in rows:
        raw = (row[1] or "").strip().lower()
        code = _LEGACY_ALIASES.get(raw, raw.replace(" ", "_"))
        matched_id = code_to_id.get(code) or name_to_id.get(raw) or fallback_id
        conn.execute(
            sa.text("UPDATE partners SET partner_type_id = :ptid WHERE id = :id"),
            {"ptid": matched_id, "id": row[0]},
        )

    # ── 5. Normalize the display string column to the canonical seeded name ──
    conn.execute(sa.text(
        "UPDATE partners p SET partner_type = pt.name "
        "FROM partner_types pt WHERE p.partner_type_id = pt.id"
    ))

    # ── 6. Make partner_type_id NOT NULL now that all rows are filled ────────
    op.alter_column("partners", "partner_type_id", nullable=False)


def downgrade() -> None:
    op.drop_column("partners", "partner_type_id")
    op.drop_table("partner_types")
