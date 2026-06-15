from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr
from ..constants import UserType


class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    user_type: UserType = UserType.CUSTOMER


class UserUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class RoleResponse(BaseModel):
    id: UUID
    role_name: str
    role_type: str
    is_active: bool

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: Optional[str]
    user_type: UserType
    is_active: bool
    roles: List[str] = []

    model_config = {"from_attributes": True}


class AssignRoleRequest(BaseModel):
    role_id: UUID
