import logging
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from ..schemas.base import ResponseModel
from ..db.queries.role_query import RoleQuery
from ..constants import RoleType

roles_router = APIRouter()
logger = logging.getLogger(__name__)


def _require_superadmin(request: Request):
    payload = getattr(request.state, "user_payload", None)
    if not payload:
        raise HTTPException(status_code=403, detail="Not authenticated")
    if "SUPERADMIN" not in payload.get("roles", []):
        raise HTTPException(status_code=403, detail="SUPERADMIN role required")
    return payload


class RoleCreate(BaseModel):
    role_name: str
    role_type: RoleType


@roles_router.get("", response_model=ResponseModel)
async def list_roles(request: Request, _=Depends(_require_superadmin)):
    roles = RoleQuery().list_roles()
    return ResponseModel.ok(data=[
        {
            "id": str(r.id),
            "role_name": r.role_name,
            "role_type": r.role_type.value if hasattr(r.role_type, "value") else r.role_type,
            "is_active": r.is_active,
        }
        for r in roles
    ])


@roles_router.post("", response_model=ResponseModel, status_code=201)
async def create_role(body: RoleCreate, request: Request, _=Depends(_require_superadmin)):
    existing = RoleQuery().get_role_by_name(body.role_name)
    if existing:
        raise HTTPException(status_code=409, detail="Role already exists")
    role = RoleQuery().create_role(body.role_name, body.role_type)
    return ResponseModel.ok(data={
        "id": str(role.id),
        "role_name": role.role_name,
        "role_type": role.role_type.value if hasattr(role.role_type, "value") else role.role_type,
        "is_active": role.is_active,
    })
