from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ...schemas.base import ResponseModel
from ...schemas.member import MemberCreate, AdminMemberUpdate, ChangeRequestCreate, ChangeRequestReview
from ...schemas.list_request import MemberListRequest
from ...services.member_service import MemberService
from ...services.audit_service import AuditService
from ...db.queries.user_query import UserQuery
from ...db.queries.member_query import MemberQuery
from ...db.queries.policy_query import PolicyQuery
from ...db.queries.policy_type_query import PolicyTypeQuery
from ...db.queries.partner_query import PartnerQuery
from ...db.queries.enrollment_history_query import EnrollmentHistoryQuery
from ...db.queries.plan_query import PlanQuery
from ...db.queries.activity_query import PolicyFamilyQuery
from ..deps import require_permission


class SwitchPlanBody(BaseModel):
    plan_id: str


class CancelEnrollmentBody(BaseModel):
    reason: Optional[str] = None

admin_members_router = APIRouter()


def _enrollment_dict(e) -> dict:
    return {
        "partner_id": str(e.partner_id),
        "plan_id": str(e.plan_id),
        "status": e.status,
        "end_date": str(e.end_date),
    }


def _enrich_family(family_members):
    pfq = PolicyFamilyQuery()
    pq = PolicyQuery()
    result = []
    for f in family_members:
        links = pfq.list_by_family_member(str(f.id))
        linked_policies = []
        for lnk in links:
            policy = pq.get_by_id(str(lnk.policy_id))
            if policy:
                linked_policies.append({
                    "id": str(policy.id),
                    "policy_number": policy.policy_number,
                    "insurer": policy.insurer,
                    "status": policy.status,
                })
        result.append({
            "id": str(f.id),
            "name": f.name,
            "relation": f.relation,
            "gender": f.gender,
            "dob": str(f.dob) if f.dob else None,
            "coverage_type": f.coverage_type if hasattr(f, "coverage_type") else None,
            "policy_count": len(linked_policies),
            "linked_policies": linked_policies,
        })
    return result


@admin_members_router.post("/list", response_model=ResponseModel)
async def list_members(
    body: MemberListRequest,
    request: Request,
    _=Depends(require_permission("members", "view")),
):
    """
    Paginated member list.

    Body includes standard list fields plus:
      partner_id (optional) — scope to members enrolled under that partner
      filters[] supports: name, email, mobile_no, is_active

    Response shape:
    {
      "data": [
        {
          "id": "...",
          "name": "...",
          "email": "...",
          "mobile_no": "...",
          "is_active": true,
          "enrollments": [ { partner_id, plan_id, status, end_date } ]
        }
      ],
      "total": 20,
      "skip": 0,
      "limit": 10
    }
    """
    mq = MemberQuery()
    pq = PolicyQuery()
    planq = PlanQuery()
    partnerq = PartnerQuery()
    total, users = mq.list_members_paginated(body, partner_id=body.partner_id)

    result = []
    for u in users:
        enrollments = mq.list_enrollments(str(u.id))
        primary = enrollments[0] if enrollments else None
        plan = planq.get_by_id(str(primary.plan_id)) if primary else None
        partner = partnerq.get_by_id(str(primary.partner_id)) if primary else None
        policy_count = len(pq.list_by_user(str(u.id)))
        result.append({
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "mobile_no": u.mobile_no,
            "member_code": u.member_code,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if hasattr(u, "created_at") and u.created_at else None,
            "policy_count": policy_count,
            "plan_name": plan.name if plan else None,
            "partner_name": partner.name if partner else None,
            "enrollments": [_enrollment_dict(e) for e in enrollments],
        })

    return ResponseModel.ok(data={
        "data": result,
        "total": total,
        "skip": body.skip,
        "limit": body.limit,
    })


@admin_members_router.post("", response_model=ResponseModel, status_code=201)
async def create_member(body: MemberCreate, request: Request, _=Depends(require_permission("members", "add"))):
    svc = MemberService()
    result = svc.create_member(body)
    user = result["user"]
    enrollment = result["enrollment"]
    if body.partner_id:
        from ...services.notification_helper import notify_partner
        notify_partner(
            partner_id=body.partner_id,
            type="new_member",
            title=f"New member added: {user.name}",
            body=f"A new member ({user.email}) has been enrolled under your account.",
            ref_id=str(user.id),
            ref_type="member",
        )
    return ResponseModel.ok(data={
        "id": str(user.id), "email": user.email, "name": user.name,
        "enrollment": _enrollment_dict(enrollment),
    })


@admin_members_router.post("/bulk-upload", response_model=ResponseModel, status_code=201)
async def bulk_upload_members(
    request: Request,
    file: UploadFile = File(...),
    partner_id: Optional[str] = Form(None),
    _=Depends(require_permission("members", "add")),
):
    """
    Upload an Excel file with member rows. Expected columns (case-insensitive):
    Sale Date | Primary Member Full Name | Gender | Primary Mobile No. | Primary Email ID |
    Address Line1 | City | State | Pin Code | Sales Channel | Partner Branch Code |
    Sales Person Name | Employee Code | Data 1 | Data 2 | Data 3 | Partner Code | Plan Code

    Each row resolves its own partner via 'Partner Code'; partner_id is only a
    fallback for files that omit that column (single-partner uploads).
    """
    from ...services.member_bulk_upload_service import process_member_bulk_upload

    contents = await file.read()
    results = process_member_bulk_upload(contents, fallback_partner_id=partner_id)
    created_by_partner = results.pop("created_by_partner")

    admin_id = request.state.user_id if hasattr(request.state, "user_id") else "admin"
    ip = request.client.host if request.client else None
    AuditService().log(
        actor_id=admin_id, actor_type="admin",
        action="bulk_upload",
        entity_type="member",
        note=f"Bulk upload: {len(results['created'])} created, {len(results['skipped'])} skipped, {len(results['errors'])} errors",
        ip_address=ip,
    )
    if created_by_partner:
        from ...services.notification_helper import notify_partner
        for pid, count in created_by_partner.items():
            notify_partner(
                partner_id=pid,
                type="new_member",
                title=f"{count} new member(s) added via bulk upload",
                body=f"{count} member(s) were enrolled under your account.",
                ref_id=pid,
                ref_type="partner",
            )
    return ResponseModel.ok(data=results)


@admin_members_router.get("/bulk-upload/sample", response_model=None)
async def admin_member_bulk_sample_multi(
    partner_ids: str,
    _=Depends(require_permission("members", "add")),
):
    """Sample Excel for a bulk upload spanning one or more partners — each row
    carries its own Partner Code + Plan Code. `partner_ids` is comma-separated;
    only Active partners contribute rows (others are silently skipped)."""
    from ...services.member_bulk_upload_service import generate_sample_workbook

    ids = [p.strip() for p in partner_ids.split(",") if p.strip()]
    if not ids:
        raise HTTPException(status_code=422, detail="Select at least one partner")

    pq = PartnerQuery()
    partners = [p for p in (pq.get_by_id(pid) for pid in ids) if p and p.status == "Active"]
    if not partners:
        raise HTTPException(status_code=422, detail="None of the selected partners are Active")

    buf = generate_sample_workbook(partners)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=member_upload_sample.xlsx"},
    )


@admin_members_router.get("/change-requests", response_model=ResponseModel)
async def list_change_requests(
    request: Request,
    status: str = None,
    member_id: str = None,
    entity_type: str = None,
    skip: int = 0,
    limit: int = 50,
    _=Depends(require_permission("members", "view")),
):
    mq = MemberQuery()
    uq = UserQuery()
    total, rows = mq.list_change_requests(user_id=member_id, status=status, entity_type=entity_type, skip=skip, limit=limit)
    items = []
    for cr in rows:
        user = uq.get_user_by_id(str(cr.user_id))
        family_member_name = None
        if cr.entity_type == "family_member" and cr.entity_id:
            fm = mq.get_family_member(str(cr.entity_id))
            family_member_name = fm.name if fm else None
        items.append({
            "id": str(cr.id),
            "member_name": user.name if user else None,
            "member_email": user.email if user else None,
            "entity_type": cr.entity_type,
            "entity_id": str(cr.entity_id) if cr.entity_id else None,
            "family_member_name": family_member_name,
            "requested_fields": cr.requested_fields,
            "reason": cr.reason,
            "status": cr.status,
            "admin_note": cr.admin_note,
            "reviewed_at": cr.reviewed_at.isoformat() if cr.reviewed_at else None,
            "created_at": cr.created_at.isoformat() if cr.created_at else None,
        })
    return ResponseModel.ok(data={"items": items, "total": total, "skip": skip, "limit": limit})


class ReviewBody(BaseModel):
    admin_note: str = None


@admin_members_router.post("/change-requests/{request_id}/approve", response_model=ResponseModel)
async def approve_change_request(request_id: str, body: ReviewBody, request: Request, _=Depends(require_permission("members", "edit"))):
    admin_id = request.state.user_id if hasattr(request.state, "user_id") else "admin"
    ip = request.client.host if request.client else None
    svc = MemberService()
    cr = svc.approve_change_request(request_id, admin_id=admin_id, admin_note=body.admin_note, ip=ip)
    return ResponseModel.ok(data={"status": cr.status})


@admin_members_router.post("/change-requests/{request_id}/reject", response_model=ResponseModel)
async def reject_change_request(request_id: str, body: ReviewBody, request: Request, _=Depends(require_permission("members", "edit"))):
    admin_id = request.state.user_id if hasattr(request.state, "user_id") else "admin"
    svc = MemberService()
    cr = svc.reject_change_request(request_id, admin_id=admin_id, admin_note=body.admin_note)
    return ResponseModel.ok(data={"status": cr.status})


@admin_members_router.patch("/{member_id}", response_model=ResponseModel)
async def update_member(
    member_id: UUID,
    body: AdminMemberUpdate,
    request: Request,
    _=Depends(require_permission("members", "edit")),
):
    admin_id = request.state.user_id if hasattr(request.state, "user_id") else "admin"
    ip = request.client.host if request.client else None
    svc = MemberService()
    result = svc.update_member_by_admin(str(member_id), body, admin_id=admin_id or "admin", ip=ip)
    return ResponseModel.ok(data=result)


@admin_members_router.patch("/{member_id}/plan", response_model=ResponseModel)
async def switch_member_plan(member_id: UUID, body: SwitchPlanBody,
                             request: Request, _=Depends(require_permission("members", "edit"))):
    """Admin switches a member's plan."""
    mq = MemberQuery()
    enrollments = mq.list_enrollments(str(member_id))
    if not enrollments:
        raise HTTPException(status_code=404, detail="No enrollment found for this member")
    enrollment = enrollments[0]
    svc = MemberService()
    updated = svc.switch_plan(str(member_id), str(enrollment.partner_id), body.plan_id, changed_by="admin")
    return ResponseModel.ok(data={
        "plan_id": str(updated.plan_id),
        "status": updated.status,
    })


@admin_members_router.post("/{member_id}/enrollment/renew", response_model=ResponseModel)
async def renew_member_enrollment(member_id: UUID, request: Request, _=Depends(require_permission("members", "edit"))):
    """Admin renews a member's enrollment for 1 more year."""
    mq = MemberQuery()
    enrollments = mq.list_enrollments(str(member_id))
    if not enrollments:
        raise HTTPException(status_code=404, detail="No enrollment found for this member")
    enrollment = enrollments[0]
    svc = MemberService()
    updated = svc.renew_enrollment(str(member_id), str(enrollment.partner_id), changed_by="admin")
    return ResponseModel.ok(data={
        "plan_id": str(updated.plan_id),
        "status": updated.status,
        "start_date": str(updated.start_date),
        "end_date": str(updated.end_date),
    })


@admin_members_router.post("/{member_id}/enrollment/cancel", response_model=ResponseModel)
async def cancel_member_enrollment(member_id: UUID, body: CancelEnrollmentBody,
                                   request: Request, _=Depends(require_permission("members", "edit"))):
    """Admin cancels a member's membership — blocks further portal access."""
    mq = MemberQuery()
    enrollments = mq.list_enrollments(str(member_id))
    if not enrollments:
        raise HTTPException(status_code=404, detail="No enrollment found for this member")
    enrollment = enrollments[0]
    svc = MemberService()
    updated = svc.cancel_enrollment(
        str(member_id), str(enrollment.partner_id), reason=body.reason, changed_by="admin",
    )
    return ResponseModel.ok(data={
        "status": updated.status,
    })


@admin_members_router.get("/{member_id}/enrollment/history", response_model=ResponseModel)
async def get_member_enrollment_history(member_id: UUID, request: Request, _=Depends(require_permission("members", "view"))):
    """Admin gets the enrollment plan change history for a member."""
    mq = MemberQuery()
    pq = PlanQuery()
    history = EnrollmentHistoryQuery().list_for_user(str(member_id))
    result = []
    for h in history:
        to_plan = pq.get_by_id(str(h.to_plan_id)) if h.to_plan_id else None
        from_plan = pq.get_by_id(str(h.from_plan_id)) if h.from_plan_id else None
        result.append({
            "id": str(h.id),
            "action": h.action,
            "changed_by": h.changed_by,
            "from_plan_id": str(h.from_plan_id) if h.from_plan_id else None,
            "from_plan_name": from_plan.name if from_plan else None,
            "to_plan_id": str(h.to_plan_id),
            "to_plan_name": to_plan.name if to_plan else None,
            "note": h.note,
            "changed_at": h.changed_at.isoformat() if h.changed_at else None,
        })
    return ResponseModel.ok(data=result)


@admin_members_router.get("/{member_id}", response_model=ResponseModel)
async def get_member(member_id: UUID, request: Request, _=Depends(require_permission("members", "view"))):
    uq = UserQuery()
    mq = MemberQuery()
    pq = PolicyQuery()
    ptq = PolicyTypeQuery()
    planq = PlanQuery()
    partnerq = PartnerQuery()
    pfq = PolicyFamilyQuery()

    user = uq.get_user_by_id(str(member_id))
    if not user:
        raise HTTPException(status_code=404, detail="Member not found")

    enrollments = mq.list_enrollments(str(member_id))
    profile = mq.get_profile(str(member_id))
    family = mq.list_family(str(member_id))
    policies = pq.list_by_user(str(member_id))
    nominees = mq.list_nominees(str(member_id))

    enriched_enrollments = []
    for e in enrollments:
        plan = planq.get_by_id(str(e.plan_id))
        partner = partnerq.get_by_id(str(e.partner_id))
        enriched_enrollments.append({
            "partner_id": str(e.partner_id),
            "partner_name": partner.name if partner else None,
            "plan_id": str(e.plan_id),
            "plan_name": plan.name if plan else None,
            "status": e.status,
            "start_date": str(e.start_date) if e.start_date else None,
            "end_date": str(e.end_date) if e.end_date else None,
        })

    policy_list = []
    for p in policies:
        pt = ptq.get_by_id(str(p.policy_type_id))
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
            "has_file": bool(p.storage_key),
            "extracted_fields": p.extracted_fields or {},
            "linked_family_members": linked_family,
        })

    return ResponseModel.ok(data={
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "mobile_no": user.mobile_no,
        "member_code": user.member_code,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if hasattr(user, "created_at") and user.created_at else None,
        "enrollments": enriched_enrollments,
        "profile": {
            "gender": profile.gender if profile else None,
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
        "family": _enrich_family(family),
        "policies": policy_list,
        "nominees": [
            {
                "id": str(n.id),
                "name": n.name,
                "relation": n.relation,
                "share_percent": n.share_percent,
            }
            for n in nominees
        ],
    })
