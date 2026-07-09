import logging
from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from ..schemas.base import ResponseModel
from ..db.queries.role_query import RoleQuery
from ..db.queries.permission_query import PermissionQuery
from ..constants import RoleType, PERMISSION_MODULES
from .deps import require_permission

roles_router = APIRouter()
logger = logging.getLogger(__name__)


class RoleCreate(BaseModel):
    role_name: str
    role_type: RoleType = RoleType.ADMIN
    permission_ids: List[str] = []


class RoleUpdate(BaseModel):
    role_name: Optional[str] = None
    is_active: Optional[bool] = None


class SetPermissionsBody(BaseModel):
    permission_ids: List[str]


def _role_dict(role) -> dict:
    return {
        "id": str(role.id),
        "role_name": role.role_name,
        "role_type": role.role_type.value if hasattr(role.role_type, "value") else role.role_type,
        "is_active": role.is_active,
        "permissions": PermissionQuery().get_keys_for_role(str(role.id)),
    }


@roles_router.get("", response_model=ResponseModel)
async def list_roles(request: Request, _=Depends(require_permission("roles", "view"))):
    roles = RoleQuery().list_roles()
    return ResponseModel.ok(data=[_role_dict(r) for r in roles])


@roles_router.get("/permissions/catalog", response_model=ResponseModel)
async def list_permission_catalog(request: Request, _=Depends(require_permission("roles", "view"))):
    """The fixed Module x Action grid the UI renders as checkboxes, grouped by module."""
    perms = PermissionQuery().list_all()
    grouped: dict = {}
    for p in perms:
        grouped.setdefault(p.module, {
            "module": p.module,
            "module_label": PERMISSION_MODULES.get(p.module, p.module),
            "actions": [],
        })["actions"].append({"id": str(p.id), "action": p.action, "label": p.label})
    return ResponseModel.ok(data=list(grouped.values()))


@roles_router.post("", response_model=ResponseModel, status_code=201)
async def create_role(body: RoleCreate, request: Request, _=Depends(require_permission("roles", "add"))):
    existing = RoleQuery().get_role_by_name(body.role_name)
    if existing:
        raise HTTPException(status_code=409, detail="Role already exists")
    role = RoleQuery().create_role(body.role_name, body.role_type)
    if body.permission_ids:
        PermissionQuery().set_role_permissions(str(role.id), body.permission_ids)
    return ResponseModel.ok(data=_role_dict(role))


@roles_router.patch("/{role_id}", response_model=ResponseModel)
async def update_role(role_id: UUID, body: RoleUpdate, request: Request,
                      _=Depends(require_permission("roles", "edit"))):
    role = RoleQuery().update_role(str(role_id), role_name=body.role_name, is_active=body.is_active)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return ResponseModel.ok(data=_role_dict(role))


@roles_router.put("/{role_id}/permissions", response_model=ResponseModel)
async def set_role_permissions(role_id: UUID, body: SetPermissionsBody, request: Request,
                               _=Depends(require_permission("roles", "edit"))):
    role = RoleQuery().get_role_by_id(str(role_id))
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.role_name == "SUPERADMIN":
        raise HTTPException(status_code=409, detail="SUPERADMIN always has every permission — it can't be edited")
    PermissionQuery().set_role_permissions(str(role_id), body.permission_ids)
    return ResponseModel.ok(data=_role_dict(RoleQuery().get_role_by_id(str(role_id))))


@roles_router.delete("/{role_id}", response_model=ResponseModel)
async def delete_role(role_id: UUID, request: Request, _=Depends(require_permission("roles", "delete"))):
    role = RoleQuery().get_role_by_id(str(role_id))
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.role_name == "SUPERADMIN":
        raise HTTPException(status_code=409, detail="SUPERADMIN cannot be deleted")
    in_use = RoleQuery().count_users_with_role(str(role_id))
    if in_use > 0:
        raise HTTPException(status_code=409, detail=f"{in_use} user(s) still have this role — unassign first")
    RoleQuery().delete_role(str(role_id))
    return ResponseModel.ok(data={"message": "Role deleted"})
