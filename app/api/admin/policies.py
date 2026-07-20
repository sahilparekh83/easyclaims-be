import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import Response
from ...schemas.base import ResponseModel
from ...storage import get_storage
from ...schemas.list_request import PolicyListRequest
from ...schemas.policy import PolicyCreate
from ...services.policy_service import PolicyService, run_ai_extraction
from ...db.queries.policy_query import PolicyQuery
from ...db.queries.user_query import UserQuery
from ...db.queries.partner_query import PartnerQuery
from ...db.queries.policy_type_query import PolicyTypeQuery
from ...db.queries.member_query import MemberQuery
from ...db.queries.activity_query import PolicyFamilyQuery, PolicyNomineeQuery
from ...db.queries.audit_log_query import AuditLogQuery
from ...services.audit_service import AuditService
from ..deps import require_permission

logger = logging.getLogger("easyclaims")
admin_policies_router = APIRouter()


def _notify_admins(type: str, title: str, body: str, ref_id: str, ref_type: str):
    from ...services.notification_helper import notify_all_admins
    notify_all_admins(type=type, title=title, body=body, ref_id=ref_id, ref_type=ref_type)


def _policy_dict(p, member_name=None, member_email=None,
                 partner_name=None, policy_type_name=None) -> dict:
    return {
        "id": str(p.id),
        "policy_number": p.policy_number,
        "policy_type_id": str(p.policy_type_id),
        "policy_type": policy_type_name,
        "insurer": p.insurer,
        "sum_insured": p.sum_insured,
        "start_date": str(p.start_date) if p.start_date else None,
        "end_date": str(p.end_date) if p.end_date else None,
        "status": p.status,
        "ai_confidence": p.ai_confidence,
        "member_id": str(p.user_id),
        "member_name": member_name,
        "member_email": member_email,
        "partner_id": str(p.partner_id),
        "partner_name": partner_name,
        "file_name": p.file_name,
        "has_file": bool(p.storage_key),
        "extracted_fields": p.extracted_fields or {},
        "previous_policy_id": str(p.previous_policy_id) if p.previous_policy_id else None,
        "renewal_confidence": p.renewal_confidence,
        "vehicle_number": p.vehicle_number,
        "vehicle_type": p.vehicle_type,
        "vehicle_owner_family_member_id": str(p.vehicle_owner_family_member_id) if p.vehicle_owner_family_member_id else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@admin_policies_router.post("/list", response_model=ResponseModel)
async def list_policies(
    body: PolicyListRequest,
    request: Request,
    _=Depends(require_permission("policies", "view")),
):
    """
    Flat list of all policies with optional partner_id filter.

    Body includes standard list fields plus:
      partner_id (optional) — scope to a specific partner
      filters[] supports: policy_number, insurer, status, policy_type_id, file_name,
      member_name, policy_holder_name, family_member_name (all "contains"/"equals"),
      start_date, end_date (also "gte"/"lte"/"between" — e.g. an "end_date" "between"
      filter with [today, today+30d] implements "expiring soon"). global_filter also
      matches member name, AI-extracted policy holder name, and validation_reason.

    Response shape:
    {
      "data": [ { policy + member + partner fields } ],
      "total": 42,
      "skip": 0,
      "limit": 10
    }
    """
    pq = PolicyQuery()
    uq = UserQuery()
    paq = PartnerQuery()
    ptq = PolicyTypeQuery()

    total, policies = pq.list_paginated_all(body, partner_id=body.partner_id, user_id=body.user_id)

    # Local caches to avoid re-querying for the same user/partner/type
    user_cache: dict = {}
    partner_cache: dict = {}
    pt_cache: dict = {}
    mq = MemberQuery()
    pfq = PolicyFamilyQuery()
    pnq = PolicyNomineeQuery()

    result = []
    for p in policies:
        uid = str(p.user_id)
        pid = str(p.partner_id)
        tid = str(p.policy_type_id)

        if uid not in user_cache:
            u = uq.get_user_by_id(uid)
            user_cache[uid] = u
        if pid not in partner_cache:
            pa = paq.get_by_id(pid)
            partner_cache[pid] = pa
        if tid not in pt_cache:
            pt = ptq.get_by_id(tid)
            pt_cache[tid] = pt

        u = user_cache[uid]
        pa = partner_cache[pid]
        pt = pt_cache[tid]

        linked_family = []
        for link in pfq.list_by_policy(str(p.id)):
            fm = mq.get_family_member(str(link.family_member_id))
            if fm:
                linked_family.append({"id": str(fm.id), "name": fm.name, "relation": fm.relation})

        linked_nominees = []
        for link in pnq.list_by_policy(str(p.id)):
            n = mq.get_nominee(str(link.nominee_id), uid)
            if n:
                linked_nominees.append({"id": str(n.id), "name": n.name, "relation": n.relation, "share_percent": n.share_percent})

        d = _policy_dict(
            p,
            member_name=u.name if u else None,
            member_email=u.email if u else None,
            partner_name=pa.name if pa else None,
            policy_type_name=pt.name if pt else None,
        )
        d["linked_family_members"] = linked_family
        d["linked_nominees"] = linked_nominees
        result.append(d)

    return ResponseModel.ok(data={
        "data": result,
        "total": total,
        "skip": body.skip,
        "limit": body.limit,
    })


@admin_policies_router.post("/upload", response_model=ResponseModel, status_code=201)
async def admin_upload_policy(
    request: Request,
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    partner_id: str = Form(...),
    policy_type_id: Optional[str] = Form(None),
    insurer: Optional[str] = Form(None),
    sum_insured: Optional[int] = Form(None),
    vehicle_number: Optional[str] = Form(None),
    vehicle_type: Optional[str] = Form(None),
    vehicle_owner_family_member_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    _=Depends(require_permission("policies", "add")),
):
    """Admin upload a policy for any member — triggers real AI extraction."""
    data = PolicyCreate(
        policy_type_id=policy_type_id or None, insurer=insurer, sum_insured=sum_insured,
        vehicle_number=vehicle_number, vehicle_type=vehicle_type,
        vehicle_owner_family_member_id=vehicle_owner_family_member_id or None,
    )
    svc = PolicyService()
    admin_id = request.state.user_payload.get("sub") if hasattr(request.state, "user_payload") else None
    policy = await svc.upload_policy(user_id, partner_id, data, file,
                                     actor_id=admin_id, actor_type="admin")
    uq = UserQuery()
    member = uq.get_user_by_id(user_id)
    member_name = member.name if member else ""
    background_tasks.add_task(run_ai_extraction, str(policy.id), policy.storage_key, member_name)
    pt = svc.get_policy_type(str(policy.policy_type_id))
    return ResponseModel.ok(data={
        "id": str(policy.id),
        "policy_number": policy.policy_number,
        "status": policy.status,
        "policy_type": pt.name if pt else None,
        "member_name": member.name if member else None,
    })


@admin_policies_router.delete("/{policy_id}", response_model=ResponseModel)
async def delete_policy(policy_id: UUID, request: Request, _=Depends(require_permission("policies", "delete"))):
    pq = PolicyQuery()
    policy = pq.get_by_id(str(policy_id))
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    if policy.storage_key:
        try:
            get_storage().delete(policy.storage_key)
        except Exception:
            pass
    from ...db.queries.activity_query import PolicyFamilyQuery, PolicyNomineeQuery
    PolicyFamilyQuery().delete_by_policy(str(policy_id))
    PolicyNomineeQuery().delete_by_policy(str(policy_id))
    pq.soft_delete_admin(str(policy_id))
    return ResponseModel.ok(data={"deleted": True})


@admin_policies_router.get("/{policy_id}/view")
async def view_policy_pdf(policy_id: UUID, request: Request, _=Depends(require_permission("policies", "view"))):
    """Stream policy PDF for inline viewing."""
    policy = PolicyService().get_policy_admin(str(policy_id))
    if not policy or not policy.storage_key:
        raise HTTPException(status_code=404, detail="No file attached to this policy")
    data = get_storage().download(policy.storage_key)
    fname = policy.file_name or "policy.pdf"
    return Response(
        content=data, media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{fname}"'},
    )


@admin_policies_router.get("/{policy_id}/download")
async def download_policy_pdf(policy_id: UUID, request: Request, _=Depends(require_permission("policies", "view"))):
    """Download policy PDF as attachment."""
    policy = PolicyService().get_policy_admin(str(policy_id))
    if not policy or not policy.storage_key:
        raise HTTPException(status_code=404, detail="No file attached to this policy")
    data = get_storage().download(policy.storage_key)
    fname = policy.file_name or "policy.pdf"
    return Response(
        content=data, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@admin_policies_router.patch("/{policy_id}/fields", response_model=ResponseModel)
async def update_policy_fields(policy_id: UUID, body: dict, _=Depends(require_permission("policies", "edit"))):
    pq = PolicyQuery()
    policy = pq.get_by_id(str(policy_id))
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    existing = policy.extracted_fields or {}
    existing.update(body)
    pq.update_extracted_fields(str(policy_id), existing)
    return ResponseModel.ok(data={"updated": True})


# ---------------------------------------------------------------------------
# APPROVE / REJECT endpoints — temporarily disabled (policies auto-activate).
# Uncomment when manual review flow is re-enabled.
# ---------------------------------------------------------------------------
# @admin_policies_router.post("/{policy_id}/approve", response_model=ResponseModel)
# async def approve_policy(policy_id: UUID, _=Depends(require_permission("policies", "edit"))):
#     pq = PolicyQuery()
#     uq = UserQuery()
#     policy = pq.get_by_id(str(policy_id))
#     if not policy:
#         raise HTTPException(status_code=404, detail="Policy not found")
#     if policy.status == "active":
#         raise HTTPException(status_code=400, detail="Policy already approved")
#
#     pq.update_status(str(policy_id), "active")
#
#     member = uq.get_user_by_id(str(policy.user_id))
#     if member:
#         pol_no = policy.policy_number or str(policy_id)
#         try:
#             from ...services.whatsapp_service import WhatsAppService
#             if member.mobile_no:
#                 WhatsAppService().send_message(
#                     member.mobile_no,
#                     f"Hi {member.name or 'there'}! 🎉\n\n"
#                     f"Your policy *{pol_no}* has been verified and is now *Active*.\n\n"
#                     "You can view your policy details on the EasyClaims portal."
#                 )
#         except Exception:
#             pass
#         try:
#             from ...services.email_service import EmailService
#             EmailService().send_policy_active(member.email, member.name or member.email, pol_no)
#         except Exception:
#             pass
#
#     member_name = member.name if member else "Member"
#     _notify_admins(
#         type="policy_approved",
#         title=f"Policy Approved — {policy.policy_number or str(policy_id)}",
#         body=f"{member_name} ki policy approve ki gayi.",
#         ref_id=str(policy_id), ref_type="policy",
#     )
#     return ResponseModel.ok(data={"status": "active"})
#
#
# @admin_policies_router.post("/{policy_id}/reject", response_model=ResponseModel)
# async def reject_policy(policy_id: UUID, _=Depends(require_permission("policies", "edit"))):
#     pq = PolicyQuery()
#     uq = UserQuery()
#     policy = pq.get_by_id(str(policy_id))
#     if not policy:
#         raise HTTPException(status_code=404, detail="Policy not found")
#     if policy.status == "rejected":
#         raise HTTPException(status_code=400, detail="Policy already rejected")
#
#     pq.update_status(str(policy_id), "rejected")
#
#     member = uq.get_user_by_id(str(policy.user_id))
#     if member:
#         pol_no = policy.policy_number or str(policy_id)
#         try:
#             from ...services.whatsapp_service import WhatsAppService
#             if member.mobile_no:
#                 WhatsAppService().send_message(
#                     member.mobile_no,
#                     f"Hi {member.name or 'there'}! ❌\n\n"
#                     f"Your policy *{pol_no}* could not be approved.\n\n"
#                     "Please contact your partner or EasyClaims support for assistance."
#                 )
#         except Exception:
#             pass
#         try:
#             from ...services.email_service import EmailService
#             EmailService().send_policy_rejected(member.email, member.name or member.email, pol_no)
#         except Exception:
#             pass
#
#     member_name = member.name if member else "Member"
#     _notify_admins(
#         type="policy_rejected",
#         title=f"Policy Rejected — {policy.policy_number or str(policy_id)}",
#         body=f"{member_name} ki policy reject ki gayi.",
#         ref_id=str(policy_id), ref_type="policy",
#     )
#     return ResponseModel.ok(data={"status": "rejected"})
# ---------------------------------------------------------------------------


@admin_policies_router.post("/{policy_id}/confirm-renewal", response_model=ResponseModel)
async def confirm_renewal(policy_id: UUID, request: Request, _=Depends(require_permission("policies", "edit"))):
    pq = PolicyQuery()
    ok = pq.confirm_renewal(str(policy_id))
    if not ok:
        raise HTTPException(status_code=400, detail="No pending renewal found for this policy")
    admin_id = request.state.user_payload.get("sub") if hasattr(request.state, "user_payload") else None
    AuditService().log(
        actor_id=admin_id, actor_type="admin",
        action="policy_renewal_confirmed",
        entity_type="policy", entity_id=str(policy_id),
    )
    return ResponseModel.ok(data={"renewed": True})


@admin_policies_router.post("/{policy_id}/dismiss-renewal", response_model=ResponseModel)
async def dismiss_renewal(policy_id: UUID, request: Request, _=Depends(require_permission("policies", "edit"))):
    pq = PolicyQuery()
    ok = pq.dismiss_renewal(str(policy_id))
    if not ok:
        raise HTTPException(status_code=404, detail="Policy not found")
    admin_id = request.state.user_payload.get("sub") if hasattr(request.state, "user_payload") else None
    AuditService().log(
        actor_id=admin_id, actor_type="admin",
        action="policy_renewal_dismissed",
        entity_type="policy", entity_id=str(policy_id),
    )
    return ResponseModel.ok(data={"dismissed": True})


@admin_policies_router.get("/{policy_id}", response_model=ResponseModel)
async def get_policy(policy_id: UUID, request: Request, _=Depends(require_permission("policies", "view"))):
    svc = PolicyService()
    uq = UserQuery()
    paq = PartnerQuery()
    policy = svc.get_policy_admin(str(policy_id))
    member = uq.get_user_by_id(str(policy.user_id))
    partner = paq.get_by_id(str(policy.partner_id))
    pt = svc.get_policy_type(str(policy.policy_type_id))
    return ResponseModel.ok(data={
        **_policy_dict(
            policy,
            member_name=member.name if member else None,
            member_email=member.email if member else None,
            partner_name=partner.name if partner else None,
            policy_type_name=pt.name if pt else None,
        ),
        "extracted_fields": policy.extracted_fields,
        "storage_key": policy.storage_key,
    })


@admin_policies_router.get("/{policy_id}/history", response_model=ResponseModel)
async def get_policy_history(policy_id: UUID, skip: int = 0, limit: int = 50,
                             _=Depends(require_permission("policies", "view"))):
    """Chronological audit trail for a single policy — upload, extraction, approval/rejection, expiry, renewal events."""
    total, rows = AuditLogQuery().list_paginated(
        entity_type="policy", entity_id=str(policy_id), skip=skip, limit=limit,
    )
    uq = UserQuery()
    actor_names: dict = {}

    def _actor_name(actor_id: Optional[str]) -> Optional[str]:
        if not actor_id:
            return None
        if actor_id not in actor_names:
            u = uq.get_user_by_id(actor_id)
            actor_names[actor_id] = u.name or u.email if u else None
        return actor_names[actor_id]

    entries = [
        {
            "id": str(r.id),
            "action": r.action,
            "actor_id": r.actor_id,
            "actor_type": r.actor_type,
            "actor_name": _actor_name(r.actor_id),
            "old_value": r.old_value,
            "new_value": r.new_value,
            "note": r.note,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    entries.reverse()  # oldest → newest for a timeline display
    return ResponseModel.ok(data={"data": entries, "total": total, "skip": skip, "limit": limit})
