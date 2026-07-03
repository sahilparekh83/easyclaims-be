from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...db.session import session_scope
from ...db.models.member import MemberEnrollment
from ..deps import _require_partner

partner_dashboard_router = APIRouter()


@partner_dashboard_router.get("", response_model=ResponseModel)
async def get_dashboard(request: Request, partner=Depends(_require_partner)):
    with session_scope() as session:
        total = session.query(MemberEnrollment).filter(
            MemberEnrollment.partner_id == partner.id).count()
        active = session.query(MemberEnrollment).filter(
            MemberEnrollment.partner_id == partner.id,
            MemberEnrollment.status == "Active").count()
    return ResponseModel.ok(data={
        "partner_id": str(partner.id), "total_enrollments": total,
        "active_enrollments": active, "inactive_enrollments": total - active,
        "float_balance": partner.float_balance or 0,
        "is_low_float": (partner.float_balance or 0) <= (partner.low_float_threshold or 0),
    })
