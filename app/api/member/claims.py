import mimetypes
from uuid import UUID
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from ...schemas.base import ResponseModel
from ...schemas.policy_claim import ClaimCreate
from ...services.policy_claim_service import PolicyClaimService
from ...db.queries.user_query import UserQuery
from ...db.queries.policy_claim_query import PolicyClaimQuery
from ...storage import get_storage
from ..deps import _require_customer

member_claims_router = APIRouter()

_DOC_TYPES = (
    "Hospital Bill", "Discharge Summary", "Prescription", "Medical Report",
    "ID Proof", "FIR / Accident Report", "Repair Estimate", "Death Certificate", "Other",
)


def _claim_dict(c, agent_name: str = None) -> dict:
    return {
        "id": str(c.id),
        "claim_number": c.claim_number,
        "policy_id": str(c.policy_id),
        "family_member_id": str(c.family_member_id) if c.family_member_id else None,
        "incident_date": str(c.incident_date) if c.incident_date else None,
        "description": c.description,
        "claimed_amount": c.claimed_amount,
        "status": c.status,
        "assigned_agent_id": str(c.assigned_agent_id) if c.assigned_agent_id else None,
        "assigned_agent_name": agent_name,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _with_agent_name(c) -> dict:
    agent_name = None
    if c.assigned_agent_id:
        agent = UserQuery().get_user_by_id(str(c.assigned_agent_id))
        agent_name = agent.name or agent.email if agent else None
    return _claim_dict(c, agent_name)


@member_claims_router.get("/document-types", response_model=ResponseModel)
async def list_document_types(_=Depends(_require_customer)):
    return ResponseModel.ok(data=list(_DOC_TYPES))


@member_claims_router.post("", response_model=ResponseModel, status_code=201)
async def create_claim(body: ClaimCreate, request: Request, payload=Depends(_require_customer)):
    user_id = payload["sub"]
    claim = PolicyClaimService().create_claim(user_id, body)
    return ResponseModel.ok(data=_with_agent_name(claim))


@member_claims_router.get("", response_model=ResponseModel)
async def list_my_claims(request: Request, payload=Depends(_require_customer)):
    user_id = payload["sub"]
    claims = PolicyClaimService().list_my_claims(user_id)
    return ResponseModel.ok(data=[_with_agent_name(c) for c in claims])


@member_claims_router.get("/{claim_id}", response_model=ResponseModel)
async def get_claim(claim_id: UUID, request: Request, payload=Depends(_require_customer)):
    user_id = payload["sub"]
    svc = PolicyClaimService()
    claim = svc.get_for_member(str(claim_id), user_id)
    return ResponseModel.ok(data={
        **_with_agent_name(claim),
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


@member_claims_router.post("/{claim_id}/documents", response_model=ResponseModel, status_code=201)
async def upload_claim_document(
    claim_id: UUID, request: Request,
    doc_type: str = Form("Other"), file: UploadFile = File(...),
    payload=Depends(_require_customer),
):
    user_id = payload["sub"]
    svc = PolicyClaimService()
    claim = svc.get_for_member(str(claim_id), user_id)  # 404s if not the member's own claim
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="File must be under 10MB")
    doc = svc.add_document(
        str(claim.id), doc_type, contents, file.filename or "document",
        uploaded_by="member", actor_label="Member",
    )
    return ResponseModel.ok(data={"id": str(doc.id), "doc_type": doc.doc_type, "file_name": doc.file_name})


def _get_claim_document_or_404(claim_id: UUID, document_id: UUID, user_id: str):
    svc = PolicyClaimService()
    claim = svc.get_for_member(str(claim_id), user_id)  # 404s if not the member's own claim
    doc = PolicyClaimQuery().get_document(str(document_id))
    if not doc or str(doc.claim_id) != str(claim.id):
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@member_claims_router.get("/{claim_id}/documents/{document_id}/view")
async def view_claim_document(claim_id: UUID, document_id: UUID, request: Request,
                              payload=Depends(_require_customer)):
    doc = _get_claim_document_or_404(claim_id, document_id, payload["sub"])
    data = get_storage().download(doc.storage_key)
    media_type = mimetypes.guess_type(doc.file_name)[0] or "application/octet-stream"
    return Response(
        content=data, media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{doc.file_name}"'},
    )


@member_claims_router.get("/{claim_id}/documents/{document_id}/download")
async def download_claim_document(claim_id: UUID, document_id: UUID, request: Request,
                                  payload=Depends(_require_customer)):
    doc = _get_claim_document_or_404(claim_id, document_id, payload["sub"])
    data = get_storage().download(doc.storage_key)
    media_type = mimetypes.guess_type(doc.file_name)[0] or "application/octet-stream"
    return Response(
        content=data, media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{doc.file_name}"'},
    )
