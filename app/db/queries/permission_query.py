from typing import List, Dict
from ..models.permission import Permission, RolePermission
from ..models.roles import Role, UserRole
from ..session import session_scope


class PermissionQuery:
    def list_all(self) -> List[Permission]:
        with session_scope() as session:
            rows = session.query(Permission).order_by(Permission.module, Permission.action).all()
            for r in rows:
                session.expunge(r)
            return rows

    def get_by_module_action(self, module: str, action: str) -> Permission:
        with session_scope() as session:
            row = session.query(Permission).filter(
                Permission.module == module, Permission.action == action
            ).first()
            if row:
                session.expunge(row)
            return row

    def create(self, module: str, action: str, label: str) -> Permission:
        with session_scope() as session:
            row = Permission(module=module, action=action, label=label)
            session.add(row)
            session.flush()
            session.expunge(row)
            return row

    def get_keys_for_role(self, role_id: str) -> List[str]:
        """Return ['partners:view', 'partners:edit', ...] granted to this role."""
        with session_scope() as session:
            rows = (
                session.query(Permission.module, Permission.action)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .filter(RolePermission.role_id == role_id)
                .all()
            )
            return [f"{module}:{action}" for module, action in rows]

    def get_keys_for_roles(self, role_names: List[str]) -> List[str]:
        """Resolve a list of role names (as stored on the JWT) to a flat, deduped
        list of granted permission keys across all of them."""
        if not role_names:
            return []
        with session_scope() as session:
            rows = (
                session.query(Permission.module, Permission.action)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .join(Role, Role.id == RolePermission.role_id)
                .filter(Role.role_name.in_(role_names), Role.is_active == True)
                .distinct()
                .all()
            )
            return [f"{module}:{action}" for module, action in rows]

    def set_role_permissions(self, role_id: str, permission_ids: List[str]) -> None:
        """Replace this role's granted permissions with exactly this set."""
        with session_scope() as session:
            session.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
            for pid in permission_ids:
                session.add(RolePermission(role_id=role_id, permission_id=pid))

    def grant_all_to_role(self, role_id: str) -> None:
        with session_scope() as session:
            all_ids = [p.id for p in session.query(Permission.id).all()]
            session.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
            for pid in all_ids:
                session.add(RolePermission(role_id=role_id, permission_id=pid))
