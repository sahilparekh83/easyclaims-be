from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Optional
from ...schemas.base import ResponseModel
from ...schemas.partner import PartnerUpdate
from ...services.partner_service import PartnerService
from ...db.queries.user_query import UserQuery
from ...db.queries.partner_query import PartnerQuery
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
        "allow_member_upload":       getattr(p, "allow_member_upload", True),
        "api_rate_limit":            p.api_rate_limit,
        "float_balance":             getattr(p, "float_balance", 0) or 0,
        "is_low_float":              (getattr(p, "float_balance", 0) or 0) <= (getattr(p, "low_float_threshold", 0) or 0),
    }


def _cr_dict(cr) -> dict:
    return {
        "id":               str(cr.id),
        "requested_fields": cr.requested_fields,
        "reason":           cr.reason,
        "status":           cr.status,
        "admin_note":       cr.admin_note,
        "reviewed_at":      cr.reviewed_at.isoformat() if cr.reviewed_at else None,
        "created_at":       cr.created_at.isoformat() if cr.created_at else None,
    }


class ChangeRequestCreate(BaseModel):
    requested_fields: dict
    reason: Optional[str] = None


@partner_profile_router.get("", response_model=ResponseModel)
async def get_profile(request: Request, partner=Depends(_require_partner)):
    user = UserQuery().get_user_by_id(str(partner.user_id))
    return ResponseModel.ok(data=_partner_dict(partner, user))


@partner_profile_router.post("/change-request", response_model=ResponseModel, status_code=201)
async def submit_change_request(body: ChangeRequestCreate, request: Request, partner=Depends(_require_partner)):
    if not body.requested_fields:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="requested_fields cannot be empty")
    cr = PartnerService().create_change_request(
        partner_id=str(partner.id),
        requested_fields=body.requested_fields,
        reason=body.reason,
    )
    return ResponseModel.ok(data=_cr_dict(cr))


@partner_profile_router.get("/change-requests", response_model=ResponseModel)
async def list_my_change_requests(request: Request, skip: int = 0, limit: int = 20,
                                  partner=Depends(_require_partner)):
    total, rows = PartnerQuery().list_change_requests(
        partner_id=str(partner.id), skip=skip, limit=limit
    )
    return ResponseModel.ok(data={
        "data": [_cr_dict(cr) for cr in rows],
        "total": total,
        "skip": skip,
        "limit": limit,
    })
