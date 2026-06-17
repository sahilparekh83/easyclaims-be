"""policy_types master table and policies storage refactor

Revision ID: e3f8a1b2c4d5
Revises: cb78175e0dff
Create Date: 2026-06-16

Changes:
- Create policy_types master table with default seed data
- Add policy_type_id FK, storage_key, file_name to policies
- Drop old policy_type (string) and file_path columns
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

revision = "e3f8a1b2c4d5"
down_revision = "cb78175e0dff"
branch_labels = None
depends_on = None

_DEFAULT_TYPES = [
    ("Health",             "health",             "Medical health insurance"),
    ("Life",               "life",               "Life insurance"),
    ("Term",               "term",               "Term life insurance"),
    ("Motor",              "motor",              "Vehicle insurance"),
    ("Travel",             "travel",             "Travel insurance"),
    ("Home",               "home",               "Home / property insurance"),
    ("Personal Accident",  "personal_accident",  "Personal accident cover"),
    ("Endowment",          "endowment",          "Endowment / savings plan"),
]


def upgrade() -> None:
    # ── 1. Create policy_types table ─────────────────────────────────────────
    op.create_table(
        "policy_types",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("code", sa.String, nullable=False, unique=True),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── 2. Seed default policy types ─────────────────────────────────────────
    conn = op.get_bind()
    type_ids = {}
    for name, code, desc in _DEFAULT_TYPES:
        tid = str(uuid.uuid4())
        type_ids[code] = tid
        conn.execute(
            sa.text(
                "INSERT INTO policy_types (id, name, code, description) "
                "VALUES (:id, :name, :code, :desc)"
            ),
            {"id": tid, "name": name, "code": code, "desc": desc},
        )

    # ── 3. Add new columns to policies (nullable while migrating) ────────────
    op.add_column("policies", sa.Column(
        "policy_type_id", UUID(as_uuid=True),
        sa.ForeignKey("policy_types.id"),
        nullable=True,
    ))
    op.add_column("policies", sa.Column("storage_key", sa.String, nullable=True))
    op.add_column("policies", sa.Column("file_name", sa.String, nullable=True))

    # ── 4. Migrate existing data: map old string to new FK ───────────────────
    # Map case-insensitive name/code to the seeded UUIDs
    name_to_id = {n.lower(): tid for (n, c, _), tid in zip(_DEFAULT_TYPES, type_ids.values())}
    code_to_id = {c: tid for (_, c, _), tid in zip(_DEFAULT_TYPES, type_ids.values())}
    fallback_id = type_ids["health"]

    rows = conn.execute(sa.text("SELECT id, policy_type, file_path FROM policies WHERE is_deleted = false")).fetchall()
    for row in rows:
        pt_str = (row[1] or "").strip().lower()
        matched_id = name_to_id.get(pt_str) or code_to_id.get(pt_str) or fallback_id
        # Migrate file_path → storage_key, file_name
        old_path = row[2] or ""
        file_name = old_path.split("/")[-1] if old_path else None
        conn.execute(
            sa.text(
                "UPDATE policies SET policy_type_id = :ptid, "
                "storage_key = :sk, file_name = :fn WHERE id = :id"
            ),
            {"ptid": matched_id, "sk": old_path or None, "fn": file_name, "id": str(row[0])},
        )

    # ── 5. Make policy_type_id NOT NULL now that all rows are filled ─────────
    op.alter_column("policies", "policy_type_id", nullable=False)

    # ── 6. Drop old columns ──────────────────────────────────────────────────
    op.drop_column("policies", "policy_type")
    op.drop_column("policies", "file_path")


def downgrade() -> None:
    op.add_column("policies", sa.Column("policy_type", sa.String, nullable=True))
    op.add_column("policies", sa.Column("file_path", sa.String, nullable=True))

    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE policies p SET policy_type = pt.name, file_path = p.storage_key "
        "FROM policy_types pt WHERE p.policy_type_id = pt.id"
    ))

    op.drop_column("policies", "file_name")
    op.drop_column("policies", "storage_key")
    op.drop_column("policies", "policy_type_id")
    op.drop_table("policy_types")
