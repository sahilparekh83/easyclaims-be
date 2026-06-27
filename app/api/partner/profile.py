from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.partner import PartnerUpdate
from ...services.partner_service import PartnerService
from ...db.queries.user_query import UserQuery
from ..deps import _require_partner

partner_profile_router = APIRouter()


def _partner_dict(p, user=None) -> dict:
    return {
        "id":                        str(p.id),
        "user_id":                   str(p.user_id),
        "name":                      p.name,
        "partner_type":              p.partner_type,
        "city":                      p.city,
        "state":                     getattr(p, "state", None),
        "legal_company_name":        getattr(p, "legal_company_name", None),
        "trade_name":                getattr(p, "trade_name", None),
        "registered_address":        getattr(p, "registered_address", None),
        "pin_code":                  getattr(p, "pin_code", None),
        "gstin":                     getattr(p, "gstin", None),
        "pan":                       getattr(p, "pan", None),
        "authorized_signatory_name": getattr(p, "authorized_signatory_name", None),
        "designation":               getattr(p, "designation", None),
        "data_1":                    getattr(p, "data_1", None),
        "data_2":                    getattr(p, "data_2", None),
        "data_3":                    getattr(p, "data_3", None),
        "email":                     str(user.email) if user else None,
        "mobile_no":                 user.mobile_no if user else None,
        "status":                    p.status,
        "api_rate_limit":            p.api_rate_limit,
    }


@partner_profile_router.get("", response_model=ResponseModel)
async def get_profile(request: Request, partner=Depends(_require_partner)):
    user = UserQuery().get_user_by_id(str(partner.user_id))
    return ResponseModel.ok(data=_partner_dict(partner, user))


@partner_profile_router.patch("", response_model=ResponseModel)
async def update_profile(body: PartnerUpdate, request: Request, partner=Depends(_require_partner)):
    updated = PartnerService().update(str(partner.id), body)
    user = UserQuery().get_user_by_id(str(updated.user_id))
    return ResponseModel.ok(data=_partner_dict(updated, user))
