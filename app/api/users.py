import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, Request, Depends
from ..schemas.base import ResponseModel
from ..schemas.user import UserCreate, UserUpdate, AssignRoleRequest
from ..services.user_service import UserService
from ..db.queries.role_query import RoleQuery

users_router = APIRouter()
logger = logging.getLogger(__name__)


def _require_superadmin(request: Request):
    payload = getattr(request.state, "user_payload", None)
    if not payload:
        raise HTTPException(status_code=403, detail="Not authenticated")
    is_superadmin = (
        payload.get("user_type") == "SUPERADMIN"
        or "SUPERADMIN" in payload.get("roles", [])
    )
    if not is_superadmin:
        raise HTTPException(status_code=403, detail="SUPERADMIN role required")
    return payload


def _require_authenticated(request: Request):
    payload = getattr(request.state, "user_payload", None)
    if not payload:
        raise HTTPException(status_code=403, detail="Not authenticated")
    return payload


def _user_to_response(user, user_service: UserService) -> dict:
    roles = user_service.get_user_roles(str(user.id))
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "mobile_no": user.mobile_no,
        "user_type": user.user_type.value if hasattr(user.user_type, "value") else user.user_type,
        "is_active": user.is_active,
        "roles": roles,
    }


@users_router.get("/me", response_model=ResponseModel)
async def get_me(request: Request, _=Depends(_require_authenticated)):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    svc = UserService()
    return ResponseModel.ok(data=_user_to_response(user, svc))


@users_router.get("", response_model=ResponseModel)
async def list_users(request: Request, skip: int = 0, limit: int = 100, _=Depends(_require_superadmin)):
    svc = UserService()
    users = svc.list_users(skip=skip, limit=limit)
    return ResponseModel.ok(data=[_user_to_response(u, svc) for u in users])


@users_router.post("", response_model=ResponseModel, status_code=201)
async def create_user(body: UserCreate, request: Request, _=Depends(_require_superadmin)):
    svc = UserService()
    user = svc.create_user(body)
    return ResponseModel.ok(data=_user_to_response(user, svc))


@users_router.get("/{user_id}", response_model=ResponseModel)
async def get_user(user_id: UUID, request: Request, _=Depends(_require_superadmin)):
    svc = UserService()
    user = svc.get_user_by_id(str(user_id))
    return ResponseModel.ok(data=_user_to_response(user, svc))


@users_router.patch("/{user_id}", response_model=ResponseModel)
async def update_user(user_id: UUID, body: UserUpdate, request: Request, _=Depends(_require_superadmin)):
    svc = UserService()
    user = svc.update_user(str(user_id), body)
    return ResponseModel.ok(data=_user_to_response(user, svc))


@users_router.delete("/{user_id}", response_model=ResponseModel)
async def delete_user(user_id: UUID, request: Request, _=Depends(_require_superadmin)):
    svc = UserService()
    svc.delete_user(str(user_id))
    return ResponseModel.ok(data={"message": "User deleted"})


@users_router.post("/{user_id}/roles", response_model=ResponseModel)
async def assign_role(user_id: UUID, body: AssignRoleRequest, request: Request, _=Depends(_require_superadmin)):
    payload = getattr(request.state, "user_payload", {})
    assigned_by = payload.get("sub")
    RoleQuery().assign_role(str(user_id), str(body.role_id), assigned_by=assigned_by)
    return ResponseModel.ok(data={"message": "Role assigned"})


@users_router.delete("/{user_id}/roles/{role_id}", response_model=ResponseModel)
async def remove_role(user_id: UUID, role_id: UUID, request: Request, _=Depends(_require_superadmin)):
    removed = RoleQuery().remove_role(str(user_id), str(role_id))
    if not removed:
        raise HTTPException(status_code=404, detail="Role assignment not found")
    return ResponseModel.ok(data={"message": "Role removed"})
