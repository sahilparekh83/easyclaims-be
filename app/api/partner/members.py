from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from ...schemas.base import ResponseModel
from ...storage import get_storage
from ...schemas.member import MemberCreate
from ...schemas.list_request import MemberListRequest
from ...services.member_service import MemberService
from ...db.queries.user_query import UserQuery
from ...db.queries.member_query import MemberQuery
from ...db.queries.policy_query import PolicyQuery
from ...db.queries.policy_type_query import PolicyTypeQuery
from ...db.queries.activity_query import ActivityQuery, NotificationQuery
from ...db.queries.plan_query import PlanQuery
from ...db.queries.enrollment_history_query import EnrollmentHistoryQuery
from ...db.queries.user_query import UserQuery
from ..deps import _require_partner
from ...db.queries.activity_query import PolicyFamilyQuery as _PFQ

partner_members_router = APIRouter()


def _family_with_counts(family_members):
    pfq = _PFQ()
    result = []
    for f in family_members:
        count = len(pfq.list_by_family_member(str(f.id)))
        result.append({
            "id": str(f.id), "name": f.name, "relation": f.relation,
            "gender": f.gender, "dob": str(f.dob) if f.dob else None,
            "coverage_type": f.coverage_type, "policy_count": count,
        })
    return result


class SwitchPlanBody(BaseModel):
    plan_id: str


@partner_members_router.post("/list", response_model=ResponseModel)
async def list_members(
    body: MemberListRequest,
    request: Request,
    partner=Depends(_require_partner),
):
    """
    Paginated list of members enrolled under this partner.

    filters[] supports: name, email, mobile_no

    Response shape:
    {
      "data": [
        {
          "id": "...",
          "name": "...",
          "email": "...",
          "mobile_no": "...",
          "enrollment": { plan_id, status, end_date }
        }
      ],
      "total": 12,
      "skip": 0,
      "limit": 10
    }
    """
    mq = MemberQuery()
    pq_plan = PlanQuery()
    pq_policy = PolicyQuery()
    total, users = mq.list_members_paginated(body, partner_id=str(partner.id))

    aq = ActivityQuery()
    result = []
    for u in users:
        enrollment = mq.get_enrollment(str(u.id), str(partner.id))
        activity = aq.get_activity(str(u.id))
        plan_name = None
        if enrollment:
            plan = pq_plan.get_by_id(str(enrollment.plan_id))
            plan_name = plan.name if plan else None
        policy_count = len(pq_policy.list_by_user_partner(str(u.id), str(partner.id)))
        result.append({
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "mobile_no": u.mobile_no,
            "is_active": u.is_active,
            "has_logged_in": activity.has_logged_in if activity else False,
            "last_login_at": activity.last_login_at.isoformat() if activity and activity.last_login_at else None,
            "policy_count": policy_count,
            "enrollment": {
                "plan_id": str(enrollment.plan_id),
                "plan_name": plan_name,
                "status": enrollment.status,
                "start_date": str(enrollment.start_date) if enrollment.start_date else None,
                "end_date": str(enrollment.end_date) if enrollment.end_date else None,
            } if enrollment else None,
        })

    return ResponseModel.ok(data={
        "data": result,
        "total": total,
        "skip": body.skip,
        "limit": body.limit,
    })


@partner_members_router.post("", response_model=ResponseModel, status_code=201)
async def create_member(body: MemberCreate, request: Request, partner=Depends(_require_partner)):
    body.partner_id = str(partner.id)
    result = MemberService().create_member(body)
    user = result["user"]
    enrollment = result["enrollment"]
    return ResponseModel.ok(data={
        "id": str(user.id), "email": user.email, "name": user.name,
        "enrollment": {
            "plan_id": str(enrollment.plan_id),
            "status": enrollment.status,
            "end_date": str(enrollment.end_date),
        },
    })


@partner_members_router.get("/{member_id}", response_model=ResponseModel)
async def get_member(member_id: UUID, request: Request, partner=Depends(_require_partner)):
    mq = MemberQuery()
    pq = PolicyQuery()
    ptq = PolicyTypeQuery()
    aq = ActivityQuery()
    planq = PlanQuery()

    enrollment = mq.get_enrollment(str(member_id), str(partner.id))
    if not enrollment:
        raise HTTPException(status_code=404, detail="Member not found under this partner")

    plan = planq.get_by_id(str(enrollment.plan_id)) if enrollment else None
    user = UserQuery().get_user_by_id(str(member_id))
    family = mq.list_family(str(member_id))
    policies = pq.list_by_user_partner(str(member_id), str(partner.id))
    activity = aq.get_activity(str(member_id))

    # Enrich policies with type name, family links, and file info
    from ...db.queries.activity_query import PolicyFamilyQuery
    pfq = PolicyFamilyQuery()
    policy_list = []
    for p in policies:
        pt = ptq.get_by_id(str(p.policy_type_id))
        # Linked family members for this policy
        links = pfq.list_by_policy(str(p.id))
        linked_family = []
        for link in links:
            fm = mq.get_family_member(str(link.family_member_id))
            if fm:
                linked_family.append({"id": str(fm.id), "name": fm.name, "relation": fm.relation})
        policy_list.append({
            "id": str(p.id),
            "policy_number": p.policy_number,
            "policy_type": pt.name if pt else None,
            "insurer": p.insurer,
            "sum_insured": p.sum_insured,
            "start_date": str(p.start_date) if p.start_date else None,
            "end_date": str(p.end_date) if p.end_date else None,
            "status": p.status,
            "file_name": p.file_name,
            "has_file": bool(p.storage_key),
            "linked_family_members": linked_family,
        })

    return ResponseModel.ok(data={
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "mobile_no": user.mobile_no,
        "has_logged_in": activity.has_logged_in if activity else False,
        "first_login_at": activity.first_login_at.isoformat() if activity and activity.first_login_at else None,
        "last_login_at": activity.last_login_at.isoformat() if activity and activity.last_login_at else None,
        "login_count": activity.login_count if activity else 0,
        "enrollment": {
            "plan_id": str(enrollment.plan_id),
            "plan_name": plan.name if plan else None,
            "plan_type": plan.plan_type if plan else None,
            "status": enrollment.status,
            "start_date": str(enrollment.start_date) if enrollment.start_date else None,
            "end_date": str(enrollment.end_date) if enrollment.end_date else None,
        },
        "profile": {
            "gender": profile.gender if (profile := mq.get_profile(str(member_id))) else None,
            "dob": str(profile.dob) if profile and profile.dob else None,
            "address_line": profile.address_line if profile else None,
            "address_city": profile.address_city if profile else None,
            "address_state": profile.address_state if profile else None,
            "address_pin": profile.address_pin if profile else None,
            "sale_date": str(profile.sale_date) if profile and profile.sale_date else None,
            "sales_channel": profile.sales_channel if profile else None,
            "branch_code": profile.branch_code if profile else None,
            "salesperson_name": profile.salesperson_name if profile else None,
            "employee_code": profile.employee_code if profile else None,
            "data1": profile.data1 if profile else None,
            "data2": profile.data2 if profile else None,
            "data3": profile.data3 if profile else None,
        },
        "family": _family_with_counts(family),
        "policies": policy_list,
    })


@partner_members_router.get("/{member_id}/policies/{policy_id}/view")
async def view_member_policy_pdf(
    member_id: UUID, policy_id: UUID, request: Request, partner=Depends(_require_partner)
):
    """Partner views a PDF of one of their member's policies."""
    pq = PolicyQuery()
    policy = pq.get_by_id(str(policy_id))
    if not policy or str(policy.partner_id) != str(partner.id) or str(policy.user_id) != str(member_id):
        raise HTTPException(status_code=404, detail="Policy not found")
    if not policy.storage_key:
        raise HTTPException(status_code=404, detail="No file attached to this policy")
    data = get_storage().download(policy.storage_key)
    fname = policy.file_name or "policy.pdf"
    return Response(content=data, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{fname}"'})


@partner_members_router.get("/{member_id}/policies/{policy_id}/download")
async def download_member_policy_pdf(
    member_id: UUID, policy_id: UUID, request: Request, partner=Depends(_require_partner)
):
    pq = PolicyQuery()
    policy = pq.get_by_id(str(policy_id))
    if not policy or str(policy.partner_id) != str(partner.id) or str(policy.user_id) != str(member_id):
        raise HTTPException(status_code=404, detail="Policy not found")
    if not policy.storage_key:
        raise HTTPException(status_code=404, detail="No file attached to this policy")
    data = get_storage().download(policy.storage_key)
    fname = policy.file_name or "policy.pdf"
    return Response(content=data, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{fname}"'})


@partner_members_router.post("/{member_id}/enrollment/renew", response_model=ResponseModel)
async def renew_member_enrollment(member_id: UUID, request: Request, partner=Depends(_require_partner)):
    """Partner renews a member's enrollment for 1 more year."""
    svc = MemberService()
    updated = svc.renew_enrollment(str(member_id), str(partner.id), changed_by="partner")
    return ResponseModel.ok(data={
        "plan_id": str(updated.plan_id),
        "status": updated.status,
        "start_date": str(updated.start_date),
        "end_date": str(updated.end_date),
    })


@partner_members_router.get("/{member_id}/enrollment/history", response_model=ResponseModel)
async def get_member_enrollment_history(member_id: UUID, request: Request, partner=Depends(_require_partner)):
    """Partner views the enrollment plan change history for one of their members."""
    mq = MemberQuery()
    pq = PlanQuery()
    # Verify member is enrolled under this partner
    enrollment = mq.get_enrollment(str(member_id), str(partner.id))
    if not enrollment:
        raise HTTPException(status_code=404, detail="Member not found under this partner")
    history = EnrollmentHistoryQuery().list_for_enrollment(str(enrollment.id))
    result = []
    for h in history:
        to_plan = pq.get_by_id(str(h.to_plan_id)) if h.to_plan_id else None
        from_plan = pq.get_by_id(str(h.from_plan_id)) if h.from_plan_id else None
        result.append({
            "id": str(h.id),
            "action": h.action,
            "changed_by": h.changed_by,
            "from_plan_name": from_plan.name if from_plan else None,
            "to_plan_name": to_plan.name if to_plan else None,
            "note": h.note,
            "changed_at": h.changed_at.isoformat() if h.changed_at else None,
        })
    return ResponseModel.ok(data=result)


@partner_members_router.patch("/{member_id}/plan", response_model=ResponseModel)
async def switch_member_plan(member_id: UUID, body: SwitchPlanBody, request: Request,
                             partner=Depends(_require_partner)):
    enrollment = MemberService().switch_plan(str(member_id), str(partner.id), body.plan_id, changed_by="partner")

    # Notify the member of the plan change
    try:
        member_user = UserQuery().get_user_by_id(str(member_id))
        plan = PlanQuery().get_by_id(str(enrollment.plan_id))
        if member_user:
            NotificationQuery().create(
                recipient_user_id=str(member_user.id),
                type="plan_changed",
                title="Your plan has been updated",
                body=f"{partner.name} has switched your plan to '{plan.name if plan else 'a new plan'}'.",
                ref_id=str(enrollment.plan_id),
                ref_type="plan",
            )
    except Exception:
        pass

    return ResponseModel.ok(data={
        "plan_id": str(enrollment.plan_id),
        "status": enrollment.status,
    })
