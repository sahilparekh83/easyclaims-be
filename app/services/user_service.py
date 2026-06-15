import logging
from typing import Optional, List
from fastapi import HTTPException
from ..db.queries.user_query import UserQuery
from ..db.queries.role_query import RoleQuery
from ..db.models.user import User
from ..schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self):
        self.user_query = UserQuery()
        self.role_query = RoleQuery()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.user_query.get_user_by_email(email)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        user = self.user_query.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.user_query.list_users(skip=skip, limit=limit)

    def create_user(self, data: UserCreate) -> User:
        existing = self.user_query.get_user_by_email(str(data.email))
        if existing:
            raise HTTPException(status_code=409, detail="User with this email already exists")
        user = self.user_query.create_user(
            email=str(data.email),
            name=data.name or "",
            user_type=data.user_type,
        )
        default_role = self.role_query.get_role_by_name(data.user_type.value)
        if default_role:
            self.role_query.assign_role(str(user.id), str(default_role.id))
        return user

    def update_user(self, user_id: str, data: UserUpdate) -> User:
        update_data = data.model_dump(exclude_none=True)
        user = self.user_query.update_user(user_id, **update_data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def delete_user(self, user_id: str) -> None:
        deleted = self.user_query.soft_delete_user(user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")

    def get_user_roles(self, user_id: str) -> List[str]:
        return self.role_query.get_user_roles(user_id)
