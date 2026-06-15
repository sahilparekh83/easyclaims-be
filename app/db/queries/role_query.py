from typing import Optional, List
from ..models.roles import Role, UserRole
from ..session import session_scope


class RoleQuery:
    def list_roles(self) -> List[Role]:
        with session_scope() as session:
            roles = session.query(Role).filter(Role.is_active == True).all()
            for r in roles:
                session.expunge(r)
            return roles

    def get_role_by_name(self, role_name: str) -> Optional[Role]:
        with session_scope() as session:
            role = session.query(Role).filter(Role.role_name == role_name).first()
            if role:
                session.expunge(role)
            return role

    def get_role_by_id(self, role_id: str) -> Optional[Role]:
        with session_scope() as session:
            role = session.query(Role).filter(Role.id == role_id).first()
            if role:
                session.expunge(role)
            return role

    def create_role(self, role_name: str, role_type: str) -> Role:
        with session_scope() as session:
            role = Role(role_name=role_name, role_type=role_type)
            session.add(role)
            session.flush()
            session.expunge(role)
            return role

    def get_user_roles(self, user_id: str) -> List[str]:
        with session_scope() as session:
            rows = (
                session.query(UserRole)
                .filter(UserRole.user_id == user_id, UserRole.is_active == True)
                .all()
            )
            role_ids = [str(r.role_id) for r in rows]

        role_names = []
        with session_scope() as session:
            for role_id in role_ids:
                role = session.query(Role).filter(Role.id == role_id).first()
                if role:
                    role_names.append(role.role_name)
        return role_names

    def assign_role(self, user_id: str, role_id: str, assigned_by: Optional[str] = None) -> UserRole:
        with session_scope() as session:
            existing = (
                session.query(UserRole)
                .filter(UserRole.user_id == user_id, UserRole.role_id == role_id)
                .first()
            )
            if existing:
                existing.is_active = True
                session.expunge(existing)
                return existing
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                assigned_by=assigned_by,
            )
            session.add(user_role)
            session.flush()
            session.expunge(user_role)
            return user_role

    def remove_role(self, user_id: str, role_id: str) -> bool:
        with session_scope() as session:
            user_role = (
                session.query(UserRole)
                .filter(UserRole.user_id == user_id, UserRole.role_id == role_id)
                .first()
            )
            if not user_role:
                return False
            user_role.is_active = False
            return True

    def seed_roles(self, roles_data: list) -> None:
        for item in roles_data:
            existing = self.get_role_by_name(item["role_name"])
            if not existing:
                self.create_role(item["role_name"], item["role_type"])
