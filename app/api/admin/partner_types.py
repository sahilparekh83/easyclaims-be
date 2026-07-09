from uuid import UUID
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.partner_type import PartnerTypeCreate, PartnerTypeUpdate
from ...services.partner_type_service import PartnerTypeService
from ..deps import require_permission

admin_partner_types_router = APIRouter()


@admin_partner_types_router.get("", response_model=ResponseModel)
async def list_partner_types(request: Request, _=Depends(require_permission("partner_types", "view"))):
    svc = PartnerTypeService()
    return ResponseModel.ok(data=[svc.to_dict(pt) for pt in svc.list_all()])


@admin_partner_types_router.post("", response_model=ResponseModel, status_code=201)
async def create_partner_type(body: PartnerTypeCreate, request: Request,
                              _=Depends(require_permission("partner_types", "add"))):
    svc = PartnerTypeService()
    pt = svc.create(body)
    return ResponseModel.ok(data=svc.to_dict(pt))


@admin_partner_types_router.get("/{partner_type_id}", response_model=ResponseModel)
async def get_partner_type(partner_type_id: UUID, request: Request,
                           _=Depends(require_permission("partner_types", "view"))):
    svc = PartnerTypeService()
    return ResponseModel.ok(data=svc.to_dict(svc.get(str(partner_type_id))))


@admin_partner_types_router.patch("/{partner_type_id}", response_model=ResponseModel)
async def update_partner_type(partner_type_id: UUID, body: PartnerTypeUpdate,
                              request: Request, _=Depends(require_permission("partner_types", "edit"))):
    svc = PartnerTypeService()
    pt = svc.update(str(partner_type_id), body)
    return ResponseModel.ok(data=svc.to_dict(pt))


@admin_partner_types_router.patch("/{partner_type_id}/activate", response_model=ResponseModel)
async def activate_partner_type(partner_type_id: UUID, request: Request,
                                _=Depends(require_permission("partner_types", "edit"))):
    svc = PartnerTypeService()
    return ResponseModel.ok(data=svc.to_dict(svc.toggle(str(partner_type_id), True)))


@admin_partner_types_router.patch("/{partner_type_id}/deactivate", response_model=ResponseModel)
async def deactivate_partner_type(partner_type_id: UUID, request: Request,
                                  _=Depends(require_permission("partner_types", "edit"))):
    svc = PartnerTypeService()
    return ResponseModel.ok(data=svc.to_dict(svc.toggle(str(partner_type_id), False)))
