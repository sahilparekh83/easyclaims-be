from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.partner import PartnerUpdate
from ...services.partner_service import PartnerService
from ..deps import _require_partner

partner_profile_router = APIRouter()


def _partner_dict(p) -> dict:
    return {"id": str(p.id), "user_id": str(p.user_id), "name": p.name,
            "partner_type": p.partner_type, "city": p.city, "status": p.status,
            "api_rate_limit": p.api_rate_limit}


@partner_profile_router.get("", response_model=ResponseModel)
async def get_profile(request: Request, partner=Depends(_require_partner)):
    return ResponseModel.ok(data=_partner_dict(partner))


@partner_profile_router.patch("", response_model=ResponseModel)
async def update_profile(body: PartnerUpdate, request: Request, partner=Depends(_require_partner)):
    updated = PartnerService().update(str(partner.id), body)
    return ResponseModel.ok(data=_partner_dict(updated))
