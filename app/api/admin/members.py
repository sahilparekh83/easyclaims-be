from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel
import openpyxl, io
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
from ..users import _require_superadmin


class SwitchPlanBody(BaseModel):
    plan_id: str

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
    _=Depends(_require_superadmin),
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
async def create_member(body: MemberCreate, request: Request, _=Depends(_require_superadmin)):
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
    partner_id: str = Form(...),
    plan_id: str = Form(...),
    _=Depends(_require_superadmin),
):
    """
    Upload an Excel file with member rows. Expected columns (case-insensitive):
    Sale Date | Primary Member Full Name | Gender | Primary Mobile No. | Primary Email ID |
    Address Line1 | City | State | Pin Code | Sales Channel | Partner Branch Code |
    Sales Person Name | Employee Code | Data 1 | Data 2 | Data 3
    """
    contents = await file.read()
    try:
        wb = openpyxl.load_workbook(filename=io.BytesIO(contents), read_only=True, data_only=True)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid Excel file")

    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise HTTPException(status_code=422, detail="Excel file is empty")

    header = [str(c).strip().lower() if c else "" for c in rows[0]]
    COL_MAP = {
        # name variants
        "primary member full name": "name", "full name": "name", "name": "name",
        "member name": "name",
        # email variants
        "primary email id": "email", "email id": "email", "email": "email",
        # mobile variants
        "primary mobile no.": "mobile_no", "primary mobile no": "mobile_no",
        "mobile number": "mobile_no", "mobile no": "mobile_no",
        "mobile no.": "mobile_no", "mobile": "mobile_no",
        "phone": "mobile_no", "phone number": "mobile_no",
        # gender
        "gender": "gender",
        # address variants
        "address line1": "address_line", "address line 1": "address_line",
        "address": "address_line", "address line": "address_line",
        # city / state / pin
        "city": "address_city",
        "state": "address_state",
        "pin code": "address_pin", "pin": "address_pin",
        "pincode": "address_pin", "postal code": "address_pin",
        # optional fields
        "sale date": "sale_date",
        "sales channel": "sales_channel",
        "partner branch code": "branch_code", "branch code": "branch_code",
        "sales person name": "salesperson_name", "salesperson name": "salesperson_name",
        "employee code": "employee_code",
        "data 1": "data1", "data1": "data1",
        "data 2": "data2", "data2": "data2",
        "data 3": "data3", "data3": "data3",
    }
    col_idx = {}
    for i, h in enumerate(header):
        mapped = COL_MAP.get(h)
        if mapped:
            col_idx[mapped] = i

    MANDATORY = {"name", "mobile_no", "email"}
    missing_cols = MANDATORY - set(col_idx.keys())
    if missing_cols:
        raise HTTPException(status_code=422, detail=f"Missing mandatory columns: {missing_cols}")

    svc = MemberService()
    admin_id = request.state.user_id if hasattr(request.state, "user_id") else "admin"
    ip = request.client.host if request.client else None
    results = {"created": [], "skipped": [], "errors": []}

    for row_num, row in enumerate(rows[1:], start=2):
        def cell(field, _row=row):
            idx = col_idx.get(field)
            if idx is None:
                return None
            v = _row[idx]
            return str(v).strip() if v is not None else None

        email = cell("email")
        name = cell("name")
        mobile = cell("mobile_no")
        gender = cell("gender")
        addr = cell("address_line")
        city = cell("address_city")
        state = cell("address_state")
        pin = cell("address_pin")

        if not email:
            results["skipped"].append({"row": row_num, "reason": "empty email"})
            continue

        missing_mandatory = [f for f, v in [("name", name), ("mobile_no", mobile)] if not v]
        if missing_mandatory:
            results["errors"].append({"row": row_num, "email": email, "reason": f"Missing: {missing_mandatory}"})
            continue

        import datetime as _dt
        sale_date_raw = cell("sale_date")
        sale_date = None
        if sale_date_raw:
            try:
                sale_date = _dt.date.fromisoformat(sale_date_raw)
            except Exception:
                pass

        try:
            member_data = MemberCreate(
                email=email, name=name, mobile_no=mobile, gender=gender,
                address_line=addr, address_city=city, address_state=state, address_pin=pin,
                partner_id=partner_id, plan_id=plan_id,
                sale_date=sale_date,
                sales_channel=cell("sales_channel"),
                branch_code=cell("branch_code"),
                salesperson_name=cell("salesperson_name"),
                employee_code=cell("employee_code"),
                data1=cell("data1"),
                data2=cell("data2"),
                data3=cell("data3"),
            )
            result = svc.create_member(member_data)
            results["created"].append({"row": row_num, "email": email, "id": str(result["user"].id)})
        except HTTPException as e:
            results["skipped"].append({"row": row_num, "email": email, "reason": e.detail})
        except Exception as e:
            results["errors"].append({"row": row_num, "email": email, "reason": str(e)})

    AuditService().log(
        actor_id=admin_id, actor_type="admin",
        action="bulk_upload",
        entity_type="member",
        note=f"Bulk upload: {len(results['created'])} created, {len(results['skipped'])} skipped, {len(results['errors'])} errors",
        ip_address=ip,
    )
    if results["created"] and partner_id:
        from ...services.notification_helper import notify_partner
        notify_partner(
            partner_id=partner_id,
            type="new_member",
            title=f"{len(results['created'])} new member(s) added via bulk upload",
            body=f"{len(results['created'])} member(s) were enrolled under your account.",
            ref_id=partner_id,
            ref_type="partner",
        )
    return ResponseModel.ok(data={
        "total_rows": len(rows) - 1,
        **results,
    })


@admin_members_router.get("/change-requests", response_model=ResponseModel)
async def list_change_requests(
    request: Request,
    status: str = None,
    member_id: str = None,
    entity_type: str = None,
    skip: int = 0,
    limit: int = 50,
    _=Depends(_require_superadmin),
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
async def approve_change_request(request_id: str, body: ReviewBody, request: Request, _=Depends(_require_superadmin)):
    admin_id = request.state.user_id if hasattr(request.state, "user_id") else "admin"
    ip = request.client.host if request.client else None
    svc = MemberService()
    cr = svc.approve_change_request(request_id, admin_id=admin_id, admin_note=body.admin_note, ip=ip)
    return ResponseModel.ok(data={"status": cr.status})


@admin_members_router.post("/change-requests/{request_id}/reject", response_model=ResponseModel)
async def reject_change_request(request_id: str, body: ReviewBody, request: Request, _=Depends(_require_superadmin)):
    admin_id = request.state.user_id if hasattr(request.state, "user_id") else "admin"
    svc = MemberService()
    cr = svc.reject_change_request(request_id, admin_id=admin_id, admin_note=body.admin_note)
    return ResponseModel.ok(data={"status": cr.status})


@admin_members_router.patch("/{member_id}", response_model=ResponseModel)
async def update_member(
    member_id: UUID,
    body: AdminMemberUpdate,
    request: Request,
    _=Depends(_require_superadmin),
):
    admin_id = request.state.user_id if hasattr(request.state, "user_id") else "admin"
    ip = request.client.host if request.client else None
    svc = MemberService()
    result = svc.update_member_by_admin(str(member_id), body, admin_id=admin_id or "admin", ip=ip)
    return ResponseModel.ok(data=result)


@admin_members_router.patch("/{member_id}/plan", response_model=ResponseModel)
async def switch_member_plan(member_id: UUID, body: SwitchPlanBody,
                             request: Request, _=Depends(_require_superadmin)):
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
async def renew_member_enrollment(member_id: UUID, request: Request, _=Depends(_require_superadmin)):
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


@admin_members_router.get("/{member_id}/enrollment/history", response_model=ResponseModel)
async def get_member_enrollment_history(member_id: UUID, request: Request, _=Depends(_require_superadmin)):
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
async def get_member(member_id: UUID, request: Request, _=Depends(_require_superadmin)):
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
