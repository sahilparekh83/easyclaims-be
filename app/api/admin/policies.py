from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from ...schemas.base import ResponseModel
from ...storage import get_storage
from ...schemas.list_request import PolicyListRequest
from ...services.policy_service import PolicyService
from ...db.queries.policy_query import PolicyQuery
from ...db.queries.user_query import UserQuery
from ...db.queries.partner_query import PartnerQuery
from ...db.queries.policy_type_query import PolicyTypeQuery
from ..users import _require_superadmin

admin_policies_router = APIRouter()


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
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@admin_policies_router.post("/list", response_model=ResponseModel)
async def list_policies(
    body: PolicyListRequest,
    request: Request,
    _=Depends(_require_superadmin),
):
    """
    Flat list of all policies with optional partner_id filter.

    Body includes standard list fields plus:
      partner_id (optional) — scope to a specific partner
      filters[] supports: policy_number, insurer, status, policy_type_id, file_name

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

        result.append(_policy_dict(
            p,
            member_name=u.name if u else None,
            member_email=u.email if u else None,
            partner_name=pa.name if pa else None,
            policy_type_name=pt.name if pt else None,
        ))

    return ResponseModel.ok(data={
        "data": result,
        "total": total,
        "skip": body.skip,
        "limit": body.limit,
    })


@admin_policies_router.get("/{policy_id}/view")
async def view_policy_pdf(policy_id: UUID, request: Request, _=Depends(_require_superadmin)):
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
async def download_policy_pdf(policy_id: UUID, request: Request, _=Depends(_require_superadmin)):
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


@admin_policies_router.get("/{policy_id}", response_model=ResponseModel)
async def get_policy(policy_id: UUID, request: Request, _=Depends(_require_superadmin)):
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
