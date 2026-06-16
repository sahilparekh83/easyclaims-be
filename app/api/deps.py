from typing import Optional
from fastapi import HTTPException, Request
from ..db.queries.partner_query import PartnerQuery
from ..services.member_service import MemberService
from ..constants import UserType


def _require_partner(request: Request):
    payload = getattr(request.state, "user_payload", None)
    if not payload:
        raise HTTPException(status_code=403, detail="Not authenticated")
    if payload.get("user_type") != UserType.PARTNER.value:
        raise HTTPException(status_code=403, detail="Partner access required")
    partner = PartnerQuery().get_by_user_id(payload["sub"])
    if not partner:
        raise HTTPException(status_code=404, detail="Partner record not found")
    return partner


def _require_customer(request: Request):
    payload = getattr(request.state, "user_payload", None)
    if not payload:
        raise HTTPException(status_code=403, detail="Not authenticated")
    if payload.get("user_type") != UserType.CUSTOMER.value:
        raise HTTPException(status_code=403, detail="Customer access required")
    return payload


def _require_customer_enrollment(request: Request):
    """Reads X-Partner-Id header, resolves enrollment. Falls back to first active."""
    payload = getattr(request.state, "user_payload", None)
    if not payload:
        raise HTTPException(status_code=403, detail="Not authenticated")
    if payload.get("user_type") != UserType.CUSTOMER.value:
        raise HTTPException(status_code=403, detail="Customer access required")
    user_id = payload["sub"]
    partner_id: Optional[str] = request.headers.get("X-Partner-Id")
    svc = MemberService()
    enrollment = svc.get_active_enrollment(user_id, partner_id)
    return enrollment
