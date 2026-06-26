from uuid import UUID
from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel
from ...schemas.base import ResponseModel
from ...storage import get_storage
from ...schemas.policy import PolicyCreate
from ...schemas.list_request import PolicyListRequest
from ...services.policy_service import PolicyService, run_ai_extraction
from ...db.queries.policy_query import PolicyQuery
from ...db.queries.member_query import MemberQuery
from ...db.queries.activity_query import PolicyFamilyQuery
from ..deps import _require_customer_enrollment

member_policies_router = APIRouter()


class UpdatePolicyBody(BaseModel):
    family_member_ids: Optional[List[str]] = None  # set linked family members (replaces current links)


def _get_linked_family(policy_id: str, user_id: str) -> list:
    """Return list of linked family member dicts for a policy."""
    pfq = PolicyFamilyQuery()
    mq = MemberQuery()
    links = pfq.list_by_policy(policy_id)
    result = []
    for link in links:
        fm = mq.get_family_member(str(link.family_member_id))
        if fm and str(fm.user_id) == user_id:
            result.append({
                "id": str(fm.id),
                "name": fm.name,
                "relation": fm.relation,
                "gender": fm.gender,
                "dob": str(fm.dob) if fm.dob else None,
            })
    return result


def _policy_dict(p, policy_type_name: str = None, user_id: str = None) -> dict:
    linked = _get_linked_family(str(p.id), user_id) if user_id else []
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
        "extracted_fields": p.extracted_fields,
        "linked_family_members": linked,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def _enrich(policies, svc: PolicyService, user_id: str) -> list:
    result = []
    for p in policies:
        pt = svc.get_policy_type(str(p.policy_type_id))
        result.append(_policy_dict(p, pt.name if pt else None, user_id=user_id))
    return result


def _set_family_members(policy_id: str, user_id: str, family_member_ids: List[str]) -> None:
    """Replace linked family members for a policy with the given list."""
    pfq = PolicyFamilyQuery()
    mq = MemberQuery()

    # Remove all current links
    existing = pfq.list_by_policy(policy_id)
    for link in existing:
        pfq.unlink(policy_id, str(link.family_member_id))

    # Add new links (validate each belongs to this user, deduplicate)
    seen = set()
    for fmid in family_member_ids:
        if fmid in seen:
            continue
        seen.add(fmid)
        fm = mq.get_family_member(fmid, user_id=user_id)
        if not fm:
            raise HTTPException(status_code=404, detail=f"Family member {fmid} not found")
        try:
            pfq.link(policy_id, str(fm.id))
        except ValueError:
            pass  # already linked (shouldn't happen after clearing, but safe)


@member_policies_router.post("/list", response_model=ResponseModel)
async def list_policies(
    body: PolicyListRequest,
    request: Request,
    enrollment=Depends(_require_customer_enrollment),
):
    user_id = request.state.user_payload["sub"]
    pq = PolicyQuery()
    svc = PolicyService()
    total, policies = pq.list_paginated_by_user_partner(
        user_id, str(enrollment.partner_id), body
    )
    return ResponseModel.ok(data={
        "data": _enrich(policies, svc, user_id),
        "total": total,
        "skip": body.skip,
        "limit": body.limit,
    })


@member_policies_router.post("", response_model=ResponseModel, status_code=201)
async def upload_policy(
    request: Request,
    background_tasks: BackgroundTasks,
    policy_type_id: str = Form(...),
    insurer: Optional[str] = Form(None),
    sum_insured: Optional[int] = Form(None),
    family_member_ids: Optional[str] = Form(None, description="Comma-separated family member UUIDs"),
    file: UploadFile = File(...),
    enrollment=Depends(_require_customer_enrollment),
):
    user_id = request.state.user_payload["sub"]
    data = PolicyCreate(policy_type_id=policy_type_id, insurer=insurer, sum_insured=sum_insured)
    svc = PolicyService()
    policy = await svc.upload_policy(user_id, str(enrollment.partner_id), data, file)

    if family_member_ids:
        ids = [fmid.strip() for fmid in family_member_ids.split(",") if fmid.strip()]
        if ids:
            _set_family_members(str(policy.id), user_id, ids)

    member_name = request.state.user_payload.get("name", "")
    background_tasks.add_task(run_ai_extraction, str(policy.id), policy.storage_key, member_name)

    pt = svc.get_policy_type(str(policy.policy_type_id))
    return ResponseModel.ok(data=_policy_dict(policy, pt.name if pt else None, user_id=user_id))


@member_policies_router.get("/{policy_id}/view")
async def view_policy_pdf(policy_id: UUID, request: Request,
                          enrollment=Depends(_require_customer_enrollment)):
    user_id = request.state.user_payload["sub"]
    svc = PolicyService()
    policy = svc.get_policy(user_id, str(policy_id))
    if not policy or not policy.storage_key:
        raise HTTPException(status_code=404, detail="No file attached to this policy")
    data = get_storage().download(policy.storage_key)
    fname = policy.file_name or "policy.pdf"
    return Response(content=data, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{fname}"'})


@member_policies_router.get("/{policy_id}/download")
async def download_policy_pdf(policy_id: UUID, request: Request,
                              enrollment=Depends(_require_customer_enrollment)):
    user_id = request.state.user_payload["sub"]
    svc = PolicyService()
    policy = svc.get_policy(user_id, str(policy_id))
    if not policy or not policy.storage_key:
        raise HTTPException(status_code=404, detail="No file attached to this policy")
    data = get_storage().download(policy.storage_key)
    fname = policy.file_name or "policy.pdf"
    return Response(content=data, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{fname}"'})


@member_policies_router.get("/{policy_id}", response_model=ResponseModel)
async def get_policy(policy_id: UUID, request: Request,
                     enrollment=Depends(_require_customer_enrollment)):
    user_id = request.state.user_payload["sub"]
    svc = PolicyService()
    policy = svc.get_policy(user_id, str(policy_id))
    pt = svc.get_policy_type(str(policy.policy_type_id))
    return ResponseModel.ok(data=_policy_dict(policy, pt.name if pt else None, user_id=user_id))


@member_policies_router.patch("/{policy_id}", response_model=ResponseModel)
async def update_policy(policy_id: UUID, body: UpdatePolicyBody, request: Request,
                        enrollment=Depends(_require_customer_enrollment)):
    """
    Update a policy's linked family members.
    Pass family_member_ids to replace the current set (empty list = remove all).
    """
    user_id = request.state.user_payload["sub"]
    svc = PolicyService()
    policy = svc.get_policy(user_id, str(policy_id))

    if body.family_member_ids is not None:
        _set_family_members(str(policy.id), user_id, body.family_member_ids)

    pt = svc.get_policy_type(str(policy.policy_type_id))
    return ResponseModel.ok(data=_policy_dict(policy, pt.name if pt else None, user_id=user_id))


@member_policies_router.delete("/{policy_id}", response_model=ResponseModel)
async def delete_policy(policy_id: UUID, request: Request,
                        enrollment=Depends(_require_customer_enrollment)):
    user_id = request.state.user_payload["sub"]
    PolicyService().delete_policy(user_id, str(policy_id))
    return ResponseModel.ok(data={"message": "Policy removed"})
