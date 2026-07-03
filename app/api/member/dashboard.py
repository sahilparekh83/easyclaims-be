from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...services.member_service import MemberService
from ...db.queries.policy_query import PolicyQuery
from ..deps import _require_customer

member_dashboard_router = APIRouter()


@member_dashboard_router.get("", response_model=ResponseModel)
async def get_dashboard(request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    svc = MemberService()
    enrollments = svc.list_enrollments(user_id)
    family = svc.list_family(user_id)
    all_policies = PolicyQuery().list_by_user(user_id)
    by_status = {}
    for p in all_policies:
        by_status[p.status] = by_status.get(p.status, 0) + 1
    return ResponseModel.ok(data={
        "enrollment_count": len(enrollments),
        "active_enrollments": [
            {"partner_id": str(e.partner_id), "plan_id": str(e.plan_id),
             "status": e.status, "end_date": str(e.end_date)}
            for e in enrollments if e.status == "Active"
        ],
        "family_count": len(family),
        "policy_count": len(all_policies),
        "policies_by_status": by_status,
    })
