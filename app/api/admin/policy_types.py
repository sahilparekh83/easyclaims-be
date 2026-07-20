from uuid import UUID
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.policy_type import PolicyTypeCreate, PolicyTypeUpdate
from ...services.policy_type_service import PolicyTypeService
from ..deps import require_permission

admin_policy_types_router = APIRouter()


@admin_policy_types_router.get("", response_model=ResponseModel)
async def list_policy_types(request: Request, _=Depends(require_permission("policy_types", "view"))):
    svc = PolicyTypeService()
    data = [svc.to_dict(pt, linked_count=svc.linked_count(str(pt.id))) for pt in svc.list_all()]
    return ResponseModel.ok(data=data)


@admin_policy_types_router.post("", response_model=ResponseModel, status_code=201)
async def create_policy_type(body: PolicyTypeCreate, request: Request,
                             _=Depends(require_permission("policy_types", "add"))):
    svc = PolicyTypeService()
    pt = svc.create(body)
    return ResponseModel.ok(data=svc.to_dict(pt))


@admin_policy_types_router.get("/{policy_type_id}", response_model=ResponseModel)
async def get_policy_type(policy_type_id: UUID, request: Request,
                          _=Depends(require_permission("policy_types", "view"))):
    svc = PolicyTypeService()
    pt = svc.get(str(policy_type_id))
    return ResponseModel.ok(data=svc.to_dict(pt, linked_count=svc.linked_count(str(policy_type_id))))


@admin_policy_types_router.delete("/{policy_type_id}", response_model=ResponseModel)
async def delete_policy_type(policy_type_id: UUID, request: Request,
                             _=Depends(require_permission("policy_types", "delete"))):
    svc = PolicyTypeService()
    svc.delete(str(policy_type_id))
    return ResponseModel.ok(data={"deleted": True})


@admin_policy_types_router.patch("/{policy_type_id}", response_model=ResponseModel)
async def update_policy_type(policy_type_id: UUID, body: PolicyTypeUpdate,
                             request: Request, _=Depends(require_permission("policy_types", "edit"))):
    svc = PolicyTypeService()
    pt = svc.update(str(policy_type_id), body)
    return ResponseModel.ok(data=svc.to_dict(pt))


@admin_policy_types_router.patch("/{policy_type_id}/activate", response_model=ResponseModel)
async def activate_policy_type(policy_type_id: UUID, request: Request,
                               _=Depends(require_permission("policy_types", "edit"))):
    svc = PolicyTypeService()
    return ResponseModel.ok(data=svc.to_dict(svc.toggle(str(policy_type_id), True)))


@admin_policy_types_router.patch("/{policy_type_id}/deactivate", response_model=ResponseModel)
async def deactivate_policy_type(policy_type_id: UUID, request: Request,
                                 _=Depends(require_permission("policy_types", "edit"))):
    svc = PolicyTypeService()
    return ResponseModel.ok(data=svc.to_dict(svc.toggle(str(policy_type_id), False)))
