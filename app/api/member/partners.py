from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...services.member_service import MemberService
from ...db.queries.partner_query import PartnerQuery
from ...services.plan_service import PlanService
from ..deps import _require_customer
from ..plans import _plan_to_dict

member_partners_router = APIRouter()


@member_partners_router.get("", response_model=ResponseModel)
async def list_my_partners(request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    svc = MemberService()
    pq = PartnerQuery()
    ps = PlanService()
    enrollments = svc.list_enrollments(user_id)
    result = []
    for idx, e in enumerate(enrollments):
        partner = pq.get_by_id(str(e.partner_id))
        plan = ps.get_by_id(str(e.plan_id))
        result.append({
            "partner_id": str(e.partner_id),
            "partner_name": partner.name if partner else None,
            "partner_code": partner.partner_code if partner else None,
            "partner_type": partner.partner_type if partner else None,
            "enrollment_status": e.status,
            "start_date": str(e.start_date),
            "end_date": str(e.end_date),
            "plan": _plan_to_dict(plan),
            "is_default": idx == 0,
        })
    return ResponseModel.ok(data=result)
