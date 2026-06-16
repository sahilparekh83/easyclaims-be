from uuid import UUID
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.partner import PartnerCreate, PartnerUpdate
from ...services.partner_service import PartnerService
from ...services.plan_service import PlanService
from ..users import _require_superadmin
from ..plans import _plan_to_dict

admin_partners_router = APIRouter()


def _partner_dict(p) -> dict:
    return {"id": str(p.id), "user_id": str(p.user_id), "name": p.name,
            "partner_type": p.partner_type, "city": p.city, "status": p.status,
            "api_key": p.api_key, "api_rate_limit": p.api_rate_limit}


@admin_partners_router.get("", response_model=ResponseModel)
async def list_partners(request: Request, skip: int = 0, limit: int = 100,
                        _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=[_partner_dict(p) for p in PartnerService().list_all(skip=skip, limit=limit)])


@admin_partners_router.post("", response_model=ResponseModel, status_code=201)
async def create_partner(body: PartnerCreate, request: Request, _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_partner_dict(PartnerService().create(body)))


@admin_partners_router.get("/{partner_id}", response_model=ResponseModel)
async def get_partner(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_partner_dict(PartnerService().get_by_id(str(partner_id))))


@admin_partners_router.patch("/{partner_id}", response_model=ResponseModel)
async def update_partner(partner_id: UUID, body: PartnerUpdate, request: Request,
                         _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_partner_dict(PartnerService().update(str(partner_id), body)))


@admin_partners_router.delete("/{partner_id}", response_model=ResponseModel)
async def delete_partner(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    PartnerService().delete(str(partner_id))
    return ResponseModel.ok(data={"message": "Partner deactivated"})


@admin_partners_router.post("/{partner_id}/regenerate-key", response_model=ResponseModel)
async def regen_key(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    p = PartnerService().regenerate_api_key(str(partner_id))
    return ResponseModel.ok(data={"api_key": p.api_key})


@admin_partners_router.get("/{partner_id}/plans", response_model=ResponseModel)
async def partner_plans(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    plans = PlanService().list_for_partner(str(partner_id))
    return ResponseModel.ok(data=[_plan_to_dict(p) for p in plans])
