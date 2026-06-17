from uuid import UUID
from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...schemas.partner import PartnerCreate, PartnerUpdate
from ...schemas.list_request import PartnerListRequest, MemberListRequest, PolicyListRequest
from ...services.partner_service import PartnerService
from ...services.plan_service import PlanService
from ...db.queries.partner_query import PartnerQuery
from ...db.queries.user_query import UserQuery
from ...db.queries.member_query import MemberQuery
from ...db.queries.policy_query import PolicyQuery
from ...db.queries.policy_type_query import PolicyTypeQuery
from ..users import _require_superadmin
from ..plans import _plan_to_dict

admin_partners_router = APIRouter()


def _partner_dict(p, user=None) -> dict:
    return {
        "id": str(p.id),
        "user_id": str(p.user_id),
        "name": p.name,
        "partner_type": p.partner_type,
        "city": p.city,
        "status": p.status,
        "email": str(user.email) if user else None,
        "mobile_no": user.mobile_no if user else None,
        "api_key": p.api_key,
        "api_rate_limit": p.api_rate_limit,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def _enrich(partners: list) -> list:
    uq = UserQuery()
    mq = MemberQuery()
    result = []
    for p in partners:
        user = uq.get_user_by_id(str(p.user_id))
        d = _partner_dict(p, user)
        d["member_count"] = mq.count_by_partner(str(p.id))
        result.append(d)
    return result


@admin_partners_router.post("/list", response_model=ResponseModel)
async def list_partners(
    body: PartnerListRequest,
    request: Request,
    _=Depends(_require_superadmin),
):
    """
    Paginated partner list.

    filters[] supports: name, partner_type, status, city
    """
    pq = PartnerQuery()
    total, partners = pq.list_paginated(body)
    return ResponseModel.ok(data={
        "data": _enrich(partners),
        "total": total,
        "skip": body.skip,
        "limit": body.limit,
    })


@admin_partners_router.post("", response_model=ResponseModel, status_code=201)
async def create_partner(body: PartnerCreate, request: Request, _=Depends(_require_superadmin)):
    p = PartnerService().create(body)
    user = UserQuery().get_user_by_id(str(p.user_id))
    return ResponseModel.ok(data=_partner_dict(p, user))


@admin_partners_router.get("/{partner_id}", response_model=ResponseModel)
async def get_partner(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    p = PartnerService().get_by_id(str(partner_id))
    user = UserQuery().get_user_by_id(str(p.user_id))
    return ResponseModel.ok(data=_partner_dict(p, user))


@admin_partners_router.patch("/{partner_id}", response_model=ResponseModel)
async def update_partner(partner_id: UUID, body: PartnerUpdate, request: Request,
                         _=Depends(_require_superadmin)):
    p = PartnerService().update(str(partner_id), body)
    user = UserQuery().get_user_by_id(str(p.user_id))
    return ResponseModel.ok(data=_partner_dict(p, user))


@admin_partners_router.delete("/{partner_id}", response_model=ResponseModel)
async def delete_partner(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    PartnerService().delete(str(partner_id))
    return ResponseModel.ok(data={"message": "Partner deactivated"})


@admin_partners_router.post("/{partner_id}/regenerate-key", response_model=ResponseModel)
async def regen_key(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    p = PartnerService().regenerate_api_key(str(partner_id))
    return ResponseModel.ok(data={"api_key": p.api_key})


@admin_partners_router.get("/{partner_id}/plans", response_model=ResponseModel)
async def partner_plans(partner_id: UUID, request: Request, _=Depends(_require_superadmin)):
    plans = PlanService().list_for_partner(str(partner_id))
    return ResponseModel.ok(data=[_plan_to_dict(p) for p in plans])


@admin_partners_router.post("/{partner_id}/members/list", response_model=ResponseModel)
async def list_partner_members(
    partner_id: UUID, body: MemberListRequest, request: Request, _=Depends(_require_superadmin)
):
    """Members enrolled under a specific partner, with their plan and policy count."""
    mq = MemberQuery()
    pq = PolicyQuery()
    from ...db.queries.plan_query import PlanQuery
    plan_q = PlanQuery()
    body.partner_id = str(partner_id)
    total, users = mq.list_members_paginated(body, partner_id=str(partner_id))
    result = []
    for u in users:
        enrollment = mq.get_enrollment(str(u.id), str(partner_id))
        plan_name = None
        if enrollment and enrollment.plan_id:
            plan = plan_q.get_by_id(str(enrollment.plan_id))
            plan_name = plan.name if plan else None
        policies = pq.list_by_user_partner(str(u.id), str(partner_id))
        family = mq.list_family(str(u.id))
        result.append({
            "id": str(u.id),
            "name": u.name,
            "email": u.email,
            "mobile_no": u.mobile_no,
            "is_active": u.is_active,
            "enrollment_status": enrollment.status if enrollment else None,
            "plan_id": str(enrollment.plan_id) if enrollment and enrollment.plan_id else None,
            "plan_name": plan_name,
            "policy_count": len(policies),
            "family_count": len(family),
        })
    return ResponseModel.ok(data={"data": result, "total": total, "skip": body.skip, "limit": body.limit})


@admin_partners_router.post("/{partner_id}/policies/list", response_model=ResponseModel)
async def list_partner_policies(
    partner_id: UUID, body: PolicyListRequest, request: Request, _=Depends(_require_superadmin)
):
    """Policies uploaded under a specific partner, with member info."""
    pq = PolicyQuery()
    uq = UserQuery()
    ptq = PolicyTypeQuery()
    body.partner_id = str(partner_id)
    total, policies = pq.list_paginated_all(body, partner_id=str(partner_id), user_id=body.user_id)
    user_cache: dict = {}
    pt_cache: dict = {}
    result = []
    for p in policies:
        uid = str(p.user_id)
        tid = str(p.policy_type_id)
        if uid not in user_cache:
            user_cache[uid] = uq.get_user_by_id(uid)
        if tid not in pt_cache:
            pt_cache[tid] = ptq.get_by_id(tid)
        u = user_cache[uid]
        pt = pt_cache[tid]
        result.append({
            "id": str(p.id),
            "policy_number": p.policy_number,
            "policy_type": pt.name if pt else None,
            "insurer": p.insurer,
            "sum_insured": p.sum_insured,
            "start_date": str(p.start_date) if p.start_date else None,
            "end_date": str(p.end_date) if p.end_date else None,
            "status": p.status,
            "file_name": p.file_name,
            "member_id": uid,
            "member_name": u.name if u else None,
            "member_email": u.email if u else None,
            "has_file": bool(p.storage_key),
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return ResponseModel.ok(data={"data": result, "total": total, "skip": body.skip, "limit": body.limit})
