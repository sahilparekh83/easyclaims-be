from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from ...schemas.base import ResponseModel
from ...schemas.policy import PolicyCreate
from ...services.policy_service import PolicyService
from ..deps import _require_customer_enrollment

me_policies_router = APIRouter()


def _policy_dict(p) -> dict:
    return {"id": str(p.id), "policy_number": p.policy_number, "policy_type": p.policy_type,
            "insurer": p.insurer, "sum_insured": p.sum_insured,
            "start_date": str(p.start_date) if p.start_date else None,
            "end_date": str(p.end_date) if p.end_date else None,
            "status": p.status, "ai_confidence": p.ai_confidence,
            "extracted_fields": p.extracted_fields}


@me_policies_router.get("", response_model=ResponseModel)
async def list_policies(request: Request, enrollment=Depends(_require_customer_enrollment)):
    user_id = request.state.user_payload["sub"]
    policies = PolicyService().list_policies(user_id, str(enrollment.partner_id))
    return ResponseModel.ok(data=[_policy_dict(p) for p in policies])


@me_policies_router.post("", response_model=ResponseModel, status_code=201)
async def upload_policy(
    request: Request,
    policy_type: str = Form(...),
    insurer: Optional[str] = Form(None),
    sum_insured: Optional[int] = Form(None),
    file: UploadFile = File(...),
    enrollment=Depends(_require_customer_enrollment),
):
    user_id = request.state.user_payload["sub"]
    data = PolicyCreate(policy_type=policy_type, insurer=insurer, sum_insured=sum_insured)
    policy = await PolicyService().upload_policy(user_id, str(enrollment.partner_id), data, file)
    return ResponseModel.ok(data=_policy_dict(policy))


@me_policies_router.get("/{policy_id}", response_model=ResponseModel)
async def get_policy(policy_id: UUID, request: Request,
                     enrollment=Depends(_require_customer_enrollment)):
    user_id = request.state.user_payload["sub"]
    policy = PolicyService().get_policy(user_id, str(policy_id))
    return ResponseModel.ok(data=_policy_dict(policy))


@me_policies_router.delete("/{policy_id}", response_model=ResponseModel)
async def delete_policy(policy_id: UUID, request: Request,
                        enrollment=Depends(_require_customer_enrollment)):
    user_id = request.state.user_payload["sub"]
    PolicyService().delete_policy(user_id, str(policy_id))
    return ResponseModel.ok(data={"message": "Policy removed"})
