from uuid import UUID
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.member import FamilyMemberCreate, FamilyMemberUpdate, FamilyChangeRequestCreate
from ...services.member_service import MemberService
from ...services.audit_service import AuditService
from ...db.queries.member_query import MemberQuery
from ...db.queries.plan_query import PlanQuery
from ..deps import _require_customer

member_family_router = APIRouter()


@member_family_router.get("", response_model=ResponseModel)
async def list_family(request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    mq = MemberQuery()
    family = mq.list_family_with_policy_counts(user_id)

    # Get plan family limit from active enrollment
    plan_family_limit = None
    enrollments = mq.list_enrollments(user_id)
    if enrollments:
        plan = PlanQuery().get_by_id(str(enrollments[0].plan_id))
        if plan:
            plan_family_limit = plan.benefit_family

    return ResponseModel.ok(data={
        "family": family,
        "plan_family_limit": plan_family_limit,
    })


@member_family_router.post("", response_model=ResponseModel, status_code=201)
async def add_family(body: FamilyMemberCreate, request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    fm = MemberService().add_family_member(user_id, body)
    AuditService().log(
        actor_id=user_id, actor_type="member",
        action="family_member_added",
        entity_type="family_member", entity_id=str(fm.id),
        new_value={"name": fm.name, "relation": fm.relation, "gender": fm.gender, "coverage_type": fm.coverage_type},
    )
    return ResponseModel.ok(data={
        "id": str(fm.id), "name": fm.name, "relation": fm.relation,
        "gender": fm.gender, "dob": str(fm.dob) if fm.dob else None,
        "coverage_type": fm.coverage_type, "policy_count": 0,
    })


@member_family_router.patch("/{member_id}", response_model=ResponseModel)
async def update_family(member_id: UUID, body: FamilyMemberUpdate,
                         request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    old_fm = MemberQuery().get_family_member(str(member_id), user_id)
    old_val = {"name": old_fm.name, "relation": old_fm.relation} if old_fm else {}
    fm = MemberService().update_family_member(user_id, str(member_id), body)
    AuditService().log(
        actor_id=user_id, actor_type="member",
        action="family_member_updated",
        entity_type="family_member", entity_id=str(member_id),
        old_value=old_val,
        new_value=body.model_dump(exclude_none=True),
    )
    return ResponseModel.ok(data={
        "id": str(fm.id), "name": fm.name, "relation": fm.relation,
        "gender": fm.gender, "dob": str(fm.dob) if fm.dob else None,
        "coverage_type": fm.coverage_type,
    })


@member_family_router.delete("/{member_id}", response_model=ResponseModel)
async def delete_family(member_id: UUID, request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    old_fm = MemberQuery().get_family_member(str(member_id), user_id)
    old_val = {"name": old_fm.name} if old_fm else {}
    MemberService().delete_family_member(user_id, str(member_id))
    AuditService().log(
        actor_id=user_id, actor_type="member",
        action="family_member_deleted",
        entity_type="family_member", entity_id=str(member_id),
        old_value=old_val,
    )
    return ResponseModel.ok(data={"message": "Family member removed"})


@member_family_router.post("/{member_id}/change-request",
                            response_model=ResponseModel, status_code=201)
async def family_change_request(member_id: UUID, body: FamilyChangeRequestCreate,
                                 request: Request, _=Depends(_require_customer)):
    user_id = request.state.user_payload["sub"]
    cr = MemberService().create_family_change_request(user_id, str(member_id), body)
    return ResponseModel.ok(data={
        "id": str(cr.id), "status": cr.status,
        "entity_type": cr.entity_type, "entity_id": str(cr.entity_id),
        "requested_fields": cr.requested_fields, "reason": cr.reason,
        "created_at": cr.created_at.isoformat() if cr.created_at else None,
    })
