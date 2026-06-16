from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from ...schemas.base import ResponseModel
from ...schemas.member import MemberCreate
from ...services.member_service import MemberService
from ...db.queries.user_query import UserQuery
from ...db.queries.member_query import MemberQuery
from ...db.queries.policy_query import PolicyQuery
from ..deps import _require_partner

partner_members_router = APIRouter()


class SwitchPlanBody(BaseModel):
    plan_id: str


@partner_members_router.get("", response_model=ResponseModel)
async def list_members(request: Request, skip: int = 0, limit: int = 100,
                       partner=Depends(_require_partner)):
    mq = MemberQuery()
    uq = UserQuery()
    enrollments = mq.list_by_partner(str(partner.id), skip=skip, limit=limit)
    result = []
    for e in enrollments:
        user = uq.get_user_by_id(str(e.user_id))
        if user:
            result.append({
                "id": str(user.id), "email": user.email, "name": user.name,
                "mobile_no": user.mobile_no,
                "enrollment": {"plan_id": str(e.plan_id), "status": e.status,
                               "end_date": str(e.end_date)},
            })
    return ResponseModel.ok(data=result)


@partner_members_router.post("", response_model=ResponseModel, status_code=201)
async def create_member(body: MemberCreate, request: Request, partner=Depends(_require_partner)):
    body.partner_id = str(partner.id)
    result = MemberService().create_member(body)
    user = result["user"]
    enrollment = result["enrollment"]
    return ResponseModel.ok(data={
        "id": str(user.id), "email": user.email, "name": user.name,
        "enrollment": {"plan_id": str(enrollment.plan_id), "status": enrollment.status,
                       "end_date": str(enrollment.end_date)},
    })


@partner_members_router.get("/{member_id}", response_model=ResponseModel)
async def get_member(member_id: UUID, request: Request, partner=Depends(_require_partner)):
    mq = MemberQuery()
    enrollment = mq.get_enrollment(str(member_id), str(partner.id))
    if not enrollment:
        raise HTTPException(status_code=404, detail="Member not found under this partner")
    user = UserQuery().get_user_by_id(str(member_id))
    family = mq.list_family(str(member_id))
    policies = PolicyQuery().list_by_user_partner(str(member_id), str(partner.id))
    return ResponseModel.ok(data={
        "id": str(user.id), "email": user.email, "name": user.name,
        "enrollment": {"plan_id": str(enrollment.plan_id), "status": enrollment.status,
                       "end_date": str(enrollment.end_date)},
        "family": [{"id": str(f.id), "name": f.name, "relation": f.relation} for f in family],
        "policies": [{"id": str(p.id), "type": p.policy_type, "status": p.status} for p in policies],
    })


@partner_members_router.patch("/{member_id}/plan", response_model=ResponseModel)
async def switch_member_plan(member_id: UUID, body: SwitchPlanBody, request: Request,
                             partner=Depends(_require_partner)):
    enrollment = MemberService().switch_plan(str(member_id), str(partner.id), body.plan_id)
    return ResponseModel.ok(data={"plan_id": str(enrollment.plan_id), "status": enrollment.status})
