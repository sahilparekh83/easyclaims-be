from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.member import PlanSwitchRequest
from ...services.member_service import MemberService
from ...services.plan_service import PlanService
from ..deps import _require_customer_enrollment
from ..plans import _plan_to_dict

member_plan_router = APIRouter()


@member_plan_router.get("/available", response_model=ResponseModel)
async def list_available_plans(request: Request, enrollment=Depends(_require_customer_enrollment)):
    plans = PlanService().list_for_partner(str(enrollment.partner_id), active_only=True)
    return ResponseModel.ok(data=[_plan_to_dict(p) for p in plans])


@member_plan_router.get("", response_model=ResponseModel)
async def get_my_plan(request: Request, enrollment=Depends(_require_customer_enrollment)):
    plan = PlanService().get_by_id(str(enrollment.plan_id))
    return ResponseModel.ok(data={
        "enrollment": {
            "partner_id": str(enrollment.partner_id),
            "status": enrollment.status,
            "start_date": str(enrollment.start_date),
            "end_date": str(enrollment.end_date),
        },
        "plan": _plan_to_dict(plan),
    })


@member_plan_router.put("", response_model=ResponseModel)
async def switch_plan(body: PlanSwitchRequest, request: Request,
                      enrollment=Depends(_require_customer_enrollment)):
    user_id = request.state.user_payload["sub"]
    updated = MemberService().switch_plan(user_id, str(enrollment.partner_id), body.plan_id, changed_by="member")
    return ResponseModel.ok(data={
        "partner_id": str(updated.partner_id),
        "plan_id": str(updated.plan_id),
        "status": updated.status,
    })
