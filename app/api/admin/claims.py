import mimetypes
from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from ...schemas.base import ResponseModel
from ...schemas.policy_claim import ClaimStatusUpdate, ClaimReassign, ClaimRemark, ClaimBulkAssign
from ...services.policy_claim_service import PolicyClaimService
from ...db.queries.user_query import UserQuery
from ...db.queries.policy_query import PolicyQuery
from ...db.queries.policy_type_query import PolicyTypeQuery
from ...db.queries.member_query import MemberQuery
from ...db.queries.plan_query import PlanQuery
from ...db.queries.role_query import RoleQuery
from ...db.queries.policy_claim_query import PolicyClaimQuery
from ...storage import get_storage
from ..deps import require_permission, require_superadmin

admin_claims_router = APIRouter()


def _agent_name(agent_id) -> Optional[str]:
    if not agent_id:
        return None
    agent = UserQuery().get_user_by_id(str(agent_id))
    return (agent.name or agent.email) if agent else None


def _claim_dict(c) -> dict:
    uq = UserQuery()
    pq = PolicyQuery()
    mq = MemberQuery()
    ptq = PolicyTypeQuery()
    plan_q = PlanQuery()

    member = uq.get_user_by_id(str(c.user_id))
    policy = pq.get_by_id(str(c.policy_id))
    family_member = mq.get_family_member(str(c.family_member_id)) if c.family_member_id else None
    policy_type = ptq.get_by_id(str(policy.policy_type_id)) if policy and policy.policy_type_id else None

    # Max claim value comes from the member's plan on the partner this claim was filed under.
    max_claim_value = None
    plan_name = None
    for enrollment in mq.list_enrollments(str(c.user_id)):
        if str(enrollment.partner_id) == str(c.partner_id):
            plan = plan_q.get_by_id(str(enrollment.plan_id))
            if plan:
                max_claim_value = plan.max_claim_value
                plan_name = plan.name
            break

    return {
        "id": str(c.id),
        "claim_number": c.claim_number,
        "policy_id": str(c.policy_id),
        "policy_number": policy.policy_number if policy else None,
        "policy_type": policy_type.name if policy_type else None,
        "insurer": policy.insurer if policy else None,
        "sum_insured": policy.sum_insured if policy else None,
        "policy_start_date": str(policy.start_date) if policy and policy.start_date else None,
        "policy_end_date": str(policy.end_date) if policy and policy.end_date else None,
        "policy_status": policy.status if policy else None,
        "has_policy_file": bool(policy and policy.storage_key),
        "policy_file_name": policy.file_name if policy else None,
        "policy_extracted_fields": policy.extracted_fields if policy else None,
        "member_id": str(c.user_id),
        "member_name": member.name if member else None,
        "member_email": member.email if member else None,
        "member_mobile_no": member.mobile_no if member else None,
        "family_member_id": str(c.family_member_id) if c.family_member_id else None,
        "family_member_name": family_member.name if family_member else None,
        "family_member_relation": family_member.relation if family_member else None,
        "partner_id": str(c.partner_id),
        "plan_name": plan_name,
        "max_claim_value": max_claim_value,
        "incident_date": str(c.incident_date) if c.incident_date else None,
        "description": c.description,
        "claimed_amount": c.claimed_amount,
        "exceeds_max_claim_value": bool(
            c.claimed_amount and max_claim_value and c.claimed_amount > max_claim_value
        ),
        "status": c.status,
        "assigned_agent_id": str(c.assigned_agent_id) if c.assigned_agent_id else None,
        "assigned_agent_name": _agent_name(c.assigned_agent_id),
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


class ListFilters(BaseModel):
    skip: int = 0
    limit: int = 50
    status: Optional[str] = None
    statuses: Optional[list] = None
    partner_id: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    user_id: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


@admin_claims_router.post("/list", response_model=ResponseModel)
async def list_claims(body: ListFilters, request: Request, _=Depends(require_permission("claims", "view"))):
    payload = getattr(request.state, "user_payload", {})
    date_from = datetime.fromisoformat(body.date_from) if body.date_from else None
    date_to = datetime.fromisoformat(body.date_to) if body.date_to else None
    total, claims = PolicyClaimService().list_paginated(
        payload, skip=body.skip, limit=body.limit, status=body.status, statuses=body.statuses,
        partner_id=body.partner_id, assigned_agent_id=body.assigned_agent_id,
        user_id=body.user_id, search=body.search, date_from=date_from, date_to=date_to,
    )
    return ResponseModel.ok(data={
        "data": [_claim_dict(c) for c in claims], "total": total, "skip": body.skip, "limit": body.limit,
    })


@admin_claims_router.get("/agents", response_model=ResponseModel)
async def list_claim_agents(_=Depends(require_permission("claims", "view"))):
    """Active users holding the CLAIMS_AGENT role — for the reassignment dropdown."""
    agent_ids = RoleQuery().list_user_ids_with_role_name("CLAIMS_AGENT")
    uq = UserQuery()
    agents = []
    for aid in agent_ids:
        u = uq.get_user_by_id(aid)
        if u:
            agents.append({"id": str(u.id), "name": u.name or u.email, "email": u.email})
    return ResponseModel.ok(data=agents)


@admin_claims_router.get("/agents/overview", response_model=ResponseModel)
async def list_claim_agents_overview(
    skip: int = 0, limit: int = 50, active_only: bool = False,
    _=Depends(require_superadmin),
):
    """CLAIMS_AGENT users (active + deactivated accounts) with total claims handled
    and a per-status breakdown, paginated — for the Claim Agents admin page.
    Superadmin-only: this is cross-agent workload data, not scoped to "your own"."""
    total, agents = PolicyClaimService().get_agents_overview(skip=skip, limit=limit, active_only=active_only)
    return ResponseModel.ok(data={"data": agents, "total": total, "skip": skip, "limit": limit})


@admin_claims_router.get("/agents/overview/{agent_id}", response_model=ResponseModel)
async def get_claim_agent_overview(
    agent_id: UUID, request: Request, _=Depends(require_permission("claims", "view")),
):
    """Single agent's workload summary — used by the (superadmin-only) Claim
    Agents detail page, and by an agent's own dashboard to show their own
    "My Claims" tile. Anyone with claims:view may fetch their own overview;
    only SUPERADMIN may fetch someone else's."""
    payload = getattr(request.state, "user_payload", {}) or {}
    is_superadmin = payload.get("user_type") == "SUPERADMIN" or "SUPERADMIN" in payload.get("roles", [])
    if not is_superadmin and str(agent_id) != str(payload.get("sub")):
        raise HTTPException(status_code=403, detail="You can only view your own claim workload")

    agent = PolicyClaimService().get_agent_overview(str(agent_id))
    if not agent:
        raise HTTPException(status_code=404, detail="Claim agent not found")
    return ResponseModel.ok(data=agent)


@admin_claims_router.get("/{claim_id}", response_model=ResponseModel)
async def get_claim(claim_id: UUID, request: Request, _=Depends(require_permission("claims", "view"))):
    payload = getattr(request.state, "user_payload", {})
    svc = PolicyClaimService()
    claim = svc.get_for_admin(str(claim_id), payload)
    family_members = MemberQuery().list_family(str(claim.user_id))
    return ResponseModel.ok(data={
        **_claim_dict(claim),
        "family_members": [
            {
                "id": str(fm.id), "name": fm.name, "relation": fm.relation,
                "gender": fm.gender, "dob": str(fm.dob) if fm.dob else None,
                "is_claim_subject": str(fm.id) == str(claim.family_member_id) if claim.family_member_id else False,
            }
            for fm in family_members
        ],
        "timeline": [
            {
                "id": str(l.id), "actor_type": l.actor_type, "actor_name": l.actor_name,
                "message": l.message, "old_status": l.old_status, "new_status": l.new_status,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in svc.get_timeline(str(claim_id))
        ],
        "documents": [
            {
                "id": str(d.id), "doc_type": d.doc_type, "file_name": d.file_name,
                "uploaded_by": d.uploaded_by, "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in svc.get_documents(str(claim_id))
        ],
    })


@admin_claims_router.patch("/{claim_id}/status", response_model=ResponseModel)
async def update_claim_status(claim_id: UUID, body: ClaimStatusUpdate, request: Request,
                              _=Depends(require_permission("claims", "edit"))):
    payload = getattr(request.state, "user_payload", {})
    claim = PolicyClaimService().update_status(str(claim_id), body, payload)
    return ResponseModel.ok(data=_claim_dict(claim))


@admin_claims_router.patch("/{claim_id}/reassign", response_model=ResponseModel)
async def reassign_claim(claim_id: UUID, body: ClaimReassign, request: Request,
                         _=Depends(require_permission("claims", "edit"))):
    payload = getattr(request.state, "user_payload", {})
    is_superadmin = payload.get("user_type") == "SUPERADMIN" or "SUPERADMIN" in payload.get("roles", [])
    if not is_superadmin:
        raise HTTPException(status_code=403, detail="Only a superadmin can reassign a claim")
    claim = PolicyClaimService().reassign_agent(str(claim_id), body.agent_id, payload)
    return ResponseModel.ok(data=_claim_dict(claim))


@admin_claims_router.patch("/bulk-assign", response_model=ResponseModel)
async def bulk_assign_claims(body: ClaimBulkAssign, request: Request,
                             _=Depends(require_permission("claims", "edit"))):
    payload = getattr(request.state, "user_payload", {})
    is_superadmin = payload.get("user_type") == "SUPERADMIN" or "SUPERADMIN" in payload.get("roles", [])
    if not is_superadmin:
        raise HTTPException(status_code=403, detail="Only a superadmin can assign claims")
    if not body.claim_ids:
        raise HTTPException(status_code=422, detail="Select at least one claim")
    claims = PolicyClaimService().bulk_reassign(body.claim_ids, body.agent_id, payload)
    return ResponseModel.ok(data={"assigned": len(claims), "claims": [_claim_dict(c) for c in claims]})


@admin_claims_router.post("/{claim_id}/remarks", response_model=ResponseModel, status_code=201)
async def add_remark(claim_id: UUID, body: ClaimRemark, request: Request,
                     _=Depends(require_permission("claims", "edit"))):
    payload = getattr(request.state, "user_payload", {})
    claim = PolicyClaimService().add_remark(str(claim_id), body.message, payload)
    return ResponseModel.ok(data=_claim_dict(claim))


@admin_claims_router.post("/{claim_id}/documents", response_model=ResponseModel, status_code=201)
async def upload_claim_document_admin(
    claim_id: UUID, request: Request,
    doc_type: str = Form("Other"), file: UploadFile = File(...),
    _=Depends(require_permission("claims", "edit")),
):
    payload = getattr(request.state, "user_payload", {})
    svc = PolicyClaimService()
    claim = svc.get_for_admin(str(claim_id), payload)
    actor = UserQuery().get_user_by_id(payload.get("sub"))
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="File must be under 10MB")
    doc = svc.add_document(
        str(claim.id), doc_type, contents, file.filename or "document",
        uploaded_by="agent", actor_label=(actor.name or actor.email) if actor else "Admin",
    )
    return ResponseModel.ok(data={"id": str(doc.id), "doc_type": doc.doc_type, "file_name": doc.file_name})


def _get_claim_document_or_404(claim_id: UUID, document_id: UUID, payload: dict):
    svc = PolicyClaimService()
    claim = svc.get_for_admin(str(claim_id), payload)  # enforces agent-own-claim access
    doc = PolicyClaimQuery().get_document(str(document_id))
    if not doc or str(doc.claim_id) != str(claim.id):
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@admin_claims_router.get("/{claim_id}/documents/{document_id}/view")
async def view_claim_document(claim_id: UUID, document_id: UUID, request: Request,
                              _=Depends(require_permission("claims", "view"))):
    payload = getattr(request.state, "user_payload", {})
    doc = _get_claim_document_or_404(claim_id, document_id, payload)
    data = get_storage().download(doc.storage_key)
    media_type = mimetypes.guess_type(doc.file_name)[0] or "application/octet-stream"
    return Response(
        content=data, media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{doc.file_name}"'},
    )


@admin_claims_router.get("/{claim_id}/documents/{document_id}/download")
async def download_claim_document(claim_id: UUID, document_id: UUID, request: Request,
                                  _=Depends(require_permission("claims", "view"))):
    payload = getattr(request.state, "user_payload", {})
    doc = _get_claim_document_or_404(claim_id, document_id, payload)
    data = get_storage().download(doc.storage_key)
    media_type = mimetypes.guess_type(doc.file_name)[0] or "application/octet-stream"
    return Response(
        content=data, media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{doc.file_name}"'},
    )
