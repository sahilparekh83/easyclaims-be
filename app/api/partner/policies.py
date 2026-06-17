from collections import defaultdict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from ...schemas.base import ResponseModel
from ...schemas.list_request import PolicyListRequest
from ...services.policy_service import PolicyService
from ...db.queries.policy_query import PolicyQuery
from ...db.queries.user_query import UserQuery
from ...db.queries.policy_type_query import PolicyTypeQuery
from ...storage import get_storage
from ..deps import _require_partner

partner_policies_router = APIRouter()


def _policy_dict(p, policy_type_name: str = None) -> dict:
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
        "file_name": p.file_name,
        "has_file": bool(p.storage_key),
        "extracted_fields": p.extracted_fields or {},
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@partner_policies_router.post("/list", response_model=ResponseModel)
async def list_policies_by_user(
    body: PolicyListRequest,
    request: Request,
    partner=Depends(_require_partner),
):
    """
    Return policies grouped by member (user-wise).

    Response shape:
    {
      "data": [
        {
          "member_id": "...",
          "member_name": "Rahul Sharma",
          "member_email": "...",
          "total_policies": 2,
          "policies": [ { policy fields... } ]
        }
      ],
      "total_members": 1,
      "total_policies": 2,
      "skip": 0,
      "limit": 10
    }
    """
    pq = PolicyQuery()
    uq = UserQuery()
    ptq = PolicyTypeQuery()

    total_policies, policies = pq.list_paginated_by_partner(str(partner.id), body)

    # Cache policy type names
    pt_cache = {}
    for p in policies:
        key = str(p.policy_type_id)
        if key not in pt_cache:
            pt = ptq.get_by_id(key)
            pt_cache[key] = pt.name if pt else None

    # Group by user_id
    user_map: dict = {}
    order: list = []
    for p in policies:
        uid = str(p.user_id)
        if uid not in user_map:
            user = uq.get_user_by_id(uid)
            user_map[uid] = {
                "member_id": uid,
                "member_name": user.name if user else None,
                "member_email": user.email if user else None,
                "policies": [],
            }
            order.append(uid)
        user_map[uid]["policies"].append(
            _policy_dict(p, pt_cache.get(str(p.policy_type_id)))
        )

    result = []
    for uid in order:
        entry = user_map[uid]
        entry["total_policies"] = len(entry["policies"])
        result.append(entry)

    return ResponseModel.ok(data={
        "data": result,
        "total_members": len(result),
        "total_policies": total_policies,
        "skip": body.skip,
        "limit": body.limit,
    })


@partner_policies_router.get("/{policy_id}/view")
async def view_policy_pdf(policy_id: UUID, request: Request, partner=Depends(_require_partner)):
    policy = PolicyService().get_policy_admin(str(policy_id))
    if not policy or str(policy.partner_id) != str(partner.id):
        raise HTTPException(status_code=404, detail="Policy not found")
    if not policy.storage_key:
        raise HTTPException(status_code=404, detail="No file attached to this policy")
    data = get_storage().download(policy.storage_key)
    fname = policy.file_name or "policy.pdf"
    return Response(content=data, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{fname}"'})


@partner_policies_router.get("/{policy_id}/download")
async def download_policy_pdf(policy_id: UUID, request: Request, partner=Depends(_require_partner)):
    policy = PolicyService().get_policy_admin(str(policy_id))
    if not policy or str(policy.partner_id) != str(partner.id):
        raise HTTPException(status_code=404, detail="Policy not found")
    if not policy.storage_key:
        raise HTTPException(status_code=404, detail="No file attached to this policy")
    data = get_storage().download(policy.storage_key)
    fname = policy.file_name or "policy.pdf"
    return Response(content=data, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{fname}"'})


@partner_policies_router.get("/{policy_id}", response_model=ResponseModel)
async def get_policy(policy_id: UUID, request: Request, partner=Depends(_require_partner)):
    svc = PolicyService()
    uq = UserQuery()
    policy = svc.get_policy_admin(str(policy_id))
    if str(policy.partner_id) != str(partner.id):
        raise HTTPException(status_code=404, detail="Policy not found")
    member = uq.get_user_by_id(str(policy.user_id))
    pt = svc.get_policy_type(str(policy.policy_type_id))
    return ResponseModel.ok(data={
        **_policy_dict(policy, pt.name if pt else None),
        "member_name": member.name if member else None,
        "member_email": member.email if member else None,
        "extracted_fields": policy.extracted_fields,
        "storage_key": policy.storage_key,
    })
