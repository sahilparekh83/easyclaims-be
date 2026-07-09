"""permissions + role_permissions — dynamic per-module RBAC

Revision ID: e0a1f2b3c4e8
Revises: e0a1f2b3c4e7
Create Date: 2026-07-08

Changes:
- Create permissions table (fixed Module x Action catalog)
- Create role_permissions table (which boxes are checked per role)
- Seed the catalog from the modules list
- Grant every permission to the existing SUPERADMIN role so nothing breaks
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

revision = "e0a1f2b3c4e8"
down_revision = "e0a1f2b3c4e7"
branch_labels = None
depends_on = None

_MODULES = {
    "dashboard":       "Dashboard",
    "partners":        "Partners",
    "members":         "Members",
    "plans":           "Membership Plans",
    "policies":        "Policies",
    "policy_types":    "Policy Types",
    "partner_types":   "Partner Types",
    "finance":         "Finance",
    "tickets":         "Tickets",
    "notifications":   "Notifications",
    "email_templates": "Email Templates",
    "audit_logs":      "Audit Logs",
    "settings":        "Settings",
    "cron":            "Automation (Cron)",
    "ai":              "AI Tools",
    "roles":           "Roles & Permissions",
    "users":           "Admin Users",
}
_ACTIONS = {
    "view":   "View",
    "add":    "Add",
    "edit":   "Edit",
    "delete": "Delete",
}


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("module", sa.String, nullable=False),
        sa.Column("action", sa.String, nullable=False),
        sa.Column("label", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("module", "action", name="uq_permission_module_action"),
    )
    op.create_table(
        "role_permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("permission_id", UUID(as_uuid=True), sa.ForeignKey("permissions.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    conn = op.get_bind()
    permission_ids = []
    for module, module_label in _MODULES.items():
        for action, action_label in _ACTIONS.items():
            pid = str(uuid.uuid4())
            permission_ids.append(pid)
            conn.execute(
                sa.text(
                    "INSERT INTO permissions (id, module, action, label) "
                    "VALUES (:id, :module, :action, :label)"
                ),
                {"id": pid, "module": module, "action": action,
                 "label": f"{action_label} {module_label}"},
            )

    superadmin = conn.execute(
        sa.text("SELECT id FROM roles WHERE role_name = 'SUPERADMIN'")
    ).fetchone()
    if superadmin:
        role_id = superadmin[0]
        for pid in permission_ids:
            conn.execute(
                sa.text(
                    "INSERT INTO role_permissions (id, role_id, permission_id) "
                    "VALUES (:id, :role_id, :permission_id)"
                ),
                {"id": str(uuid.uuid4()), "role_id": role_id, "permission_id": pid},
            )


def downgrade() -> None:
    op.drop_table("role_permissions")
    op.drop_table("permissions")
