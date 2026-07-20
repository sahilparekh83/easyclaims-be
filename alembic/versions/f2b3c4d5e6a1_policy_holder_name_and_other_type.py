"""policy_holder_name column + 'Other Insurance' fallback policy type

Revision ID: f2b3c4d5e6a1
Revises: e0a1f2b3c4ea
Create Date: 2026-07-18

Changes:
- Add policies.policy_holder_name (AI-extracted insured name, promoted from
  extracted_fields JSONB to a real column for search/reporting).
- Seed a fallback "Other Insurance" policy_type (idempotent) so category
  auto-detection always has a guaranteed-active row to fall back to when the
  AI's answer doesn't match any existing category — policy_type_id stays
  NOT NULL, so this fallback is required rather than making the FK nullable.
"""
from alembic import op
import sqlalchemy as sa
import uuid

revision = "f2b3c4d5e6a1"
down_revision = "e0a1f2b3c4ea"
branch_labels = None
depends_on = None

_FALLBACK_CODE = "other_insurance"
_FALLBACK_NAME = "Other Insurance"
_FALLBACK_DESC = "Uncategorized / other insurance products"


def upgrade() -> None:
    op.add_column("policies", sa.Column("policy_holder_name", sa.String, nullable=True))

    conn = op.get_bind()
    exists = conn.execute(
        sa.text("SELECT id FROM policy_types WHERE code = :code"),
        {"code": _FALLBACK_CODE},
    ).first()
    if not exists:
        conn.execute(
            sa.text(
                "INSERT INTO policy_types (id, name, code, description, is_active) "
                "VALUES (:id, :name, :code, :desc, true)"
            ),
            {"id": str(uuid.uuid4()), "name": _FALLBACK_NAME, "code": _FALLBACK_CODE, "desc": _FALLBACK_DESC},
        )


def downgrade() -> None:
    op.drop_column("policies", "policy_holder_name")
    # Intentionally does not delete the seeded policy_types row — it may already
    # be referenced by policies.policy_type_id.
