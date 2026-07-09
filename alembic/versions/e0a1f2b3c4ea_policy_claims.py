"""policy_claims, policy_claim_documents, claim_activity_logs

Revision ID: e0a1f2b3c4ea
Revises: e0a1f2b3c4e9
Create Date: 2026-07-08

Changes:
- New, self-contained claims pipeline — does NOT touch tickets/ticket_query.py
  or anything in the existing AI-ticket flow.
- Adds a 'claims' permission module (view/add/edit/delete) to the existing
  RBAC grid, granted in full to SUPERADMIN and as view+edit to CLAIMS_AGENT
  (mirroring the tickets grant made earlier).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

revision = "e0a1f2b3c4ea"
down_revision = "e0a1f2b3c4e9"
branch_labels = None
depends_on = None

_ACTIONS = {
    "view":   "View",
    "add":    "Add",
    "edit":   "Edit",
    "delete": "Delete",
}
_MODULE_LABEL = "Claim Tickets"


def upgrade() -> None:
    op.create_table(
        "policy_claims",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("claim_number", sa.String, nullable=False, unique=True),
        sa.Column("policy_id", UUID(as_uuid=True), sa.ForeignKey("policies.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("partner_id", UUID(as_uuid=True), sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("family_member_id", UUID(as_uuid=True), sa.ForeignKey("family_members.id"), nullable=True),
        sa.Column("incident_date", sa.Date, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("claimed_amount", sa.BigInteger, nullable=True),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("assigned_agent_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "policy_claim_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("claim_id", UUID(as_uuid=True), sa.ForeignKey("policy_claims.id"), nullable=False),
        sa.Column("doc_type", sa.String, nullable=False, server_default="Other"),
        sa.Column("storage_key", sa.String, nullable=False),
        sa.Column("file_name", sa.String, nullable=False),
        sa.Column("uploaded_by", sa.String, nullable=False, server_default="member"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "claim_activity_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("claim_id", UUID(as_uuid=True), sa.ForeignKey("policy_claims.id"), nullable=False),
        sa.Column("actor_type", sa.String, nullable=False, server_default="system"),
        sa.Column("actor_name", sa.String, nullable=True),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("old_status", sa.String, nullable=True),
        sa.Column("new_status", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Seed 'claims' permissions + grant to SUPERADMIN (all) and CLAIMS_AGENT (view+edit) ──
    conn = op.get_bind()
    perm_ids = {}
    for action, action_label in _ACTIONS.items():
        pid = str(uuid.uuid4())
        perm_ids[action] = pid
        conn.execute(
            sa.text(
                "INSERT INTO permissions (id, module, action, label) "
                "VALUES (:id, 'claims', :action, :label)"
            ),
            {"id": pid, "action": action, "label": f"{action_label} {_MODULE_LABEL}"},
        )

    superadmin = conn.execute(sa.text("SELECT id FROM roles WHERE role_name = 'SUPERADMIN'")).fetchone()
    if superadmin:
        for pid in perm_ids.values():
            conn.execute(
                sa.text("INSERT INTO role_permissions (id, role_id, permission_id) VALUES (:id, :role_id, :pid)"),
                {"id": str(uuid.uuid4()), "role_id": superadmin[0], "pid": pid},
            )

    claims_agent = conn.execute(sa.text("SELECT id FROM roles WHERE role_name = 'CLAIMS_AGENT'")).fetchone()
    if claims_agent:
        for action in ("view", "edit"):
            conn.execute(
                sa.text("INSERT INTO role_permissions (id, role_id, permission_id) VALUES (:id, :role_id, :pid)"),
                {"id": str(uuid.uuid4()), "role_id": claims_agent[0], "pid": perm_ids[action]},
            )


def downgrade() -> None:
    op.execute(sa.text(
        "DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE module = 'claims')"
    ))
    op.execute(sa.text("DELETE FROM permissions WHERE module = 'claims'"))
    op.drop_table("claim_activity_logs")
    op.drop_table("policy_claim_documents")
    op.drop_table("policy_claims")
