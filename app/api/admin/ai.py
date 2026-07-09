import os
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from ...schemas.base import ResponseModel
from ...db.queries.policy_query import PolicyQuery
from ...db.queries.user_query import UserQuery
from ...db.session import session_scope
from ...db.models.llm_usage import LLMUsage
from ...storage import get_storage
from ...agents import DocumentExtractorAgent, DocValidatorAgent, OutboundCallerAgent, MultilingualAgent
from ..deps import require_permission

admin_ai_router = APIRouter()


# ── Extract + Validate a policy PDF ──────────────────────────────────────────

@admin_ai_router.post("/extract/{policy_id}", response_model=ResponseModel)
async def extract_policy(policy_id: UUID, request: Request, _=Depends(require_permission("ai", "edit"))):
    """
    Run AI extraction + validation on an uploaded policy PDF.
    Updates policy.extracted_fields, ai_confidence, and status.
    """
    pq = PolicyQuery()
    uq = UserQuery()
    storage = get_storage()

    policy = pq.get_by_id(str(policy_id))
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    if not policy.storage_key:
        raise HTTPException(status_code=422, detail="No PDF attached to this policy")

    # Download PDF to a temp file
    pdf_bytes = storage.download(policy.storage_key)
    tmp_path = f"/tmp/{policy_id}.pdf"
    with open(tmp_path, "wb") as f:
        f.write(pdf_bytes)

    try:
        # Step 1: Extract
        extracted = DocumentExtractorAgent().extract(tmp_path, policy_id=str(policy_id))

        # Step 2: Validate
        member = uq.get_user_by_id(str(policy.user_id))
        member_name = member.name if member else ""

        validation = DocValidatorAgent().validate(
            extracted=extracted.model_dump(),
            member_name=member_name,
            policy_id=str(policy_id),
        )

        # Step 3: Persist results
        status_map = {"pass": "active", "review": "pending", "reject": "rejected"}
        new_status = status_map.get(validation.status, "pending")
        confidence_pct = int(extracted.confidence * 100)

        fields = {
            "policy_number": extracted.policy_number,
            "insured_name": extracted.insured_name,
            "insurer_name": extracted.insurer_name,
            "sum_insured": extracted.sum_insured,
            "start_date": extracted.start_date,
            "end_date": extracted.end_date,
            "confidence": extracted.confidence,
            "validation_status": validation.status,
            "validation_reason": validation.reason,
            "name_match": validation.name_match,
        }
        if extracted.additional_info:
            import json
            try:
                fields.update(json.loads(extracted.additional_info))
            except (ValueError, TypeError):
                pass

        pq.update_ai_result(str(policy_id), fields, confidence_pct, new_status)

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return ResponseModel.ok(data={
        "policy_id": str(policy_id),
        "extraction": extracted.model_dump(),
        "validation": validation.model_dump(),
        "new_status": new_status,
    })


# ── Outbound Call Script ──────────────────────────────────────────────────────

class CallScriptRequest(BaseModel):
    member_id: str
    call_type: str        # "Welcome Call" | "Renewal Reminder Call"
    plan_name: str
    end_date: str
    language: str = "Hindi"


@admin_ai_router.post("/call-script", response_model=ResponseModel)
async def generate_call_script(body: CallScriptRequest, request: Request, _=Depends(require_permission("ai", "add"))):
    """Generate an outbound call script for a member."""
    uq = UserQuery()
    member = uq.get_user_by_id(body.member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    script = OutboundCallerAgent().generate_script(
        call_type=body.call_type,
        member_name=member.name or member.email,
        plan_name=body.plan_name,
        end_date=body.end_date,
        language=body.language,
        member_id=body.member_id,
    )
    return ResponseModel.ok(data=script.model_dump())


# ── Translation ───────────────────────────────────────────────────────────────

class TranslateRequest(BaseModel):
    text: str
    target_language: str = "Hindi"


@admin_ai_router.post("/translate", response_model=ResponseModel)
async def translate_text(body: TranslateRequest, request: Request, _=Depends(require_permission("ai", "add"))):
    """Translate text to English or Hindi."""
    result = MultilingualAgent().translate(body.text, body.target_language)
    return ResponseModel.ok(data=result.model_dump())


# ── LLM Billing Summary ───────────────────────────────────────────────────────

@admin_ai_router.get("/billing", response_model=ResponseModel)
async def get_billing_summary(request: Request, _=Depends(require_permission("ai", "view"))):
    """View total LLM usage and cost breakdown by agent."""
    with session_scope() as session:
        rows = session.query(LLMUsage).order_by(LLMUsage.created_at.desc()).limit(500).all()
        records = [
            {
                "id": str(r.id),
                "agent": r.agent_name,
                "model": r.model_name,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "total_tokens": r.total_tokens,
                "cost_usd": r.cost_usd,
                "reference_id": r.reference_id,
                "reference_type": r.reference_type,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    total_cost = sum(r["cost_usd"] for r in records)
    by_agent: dict = {}
    for r in records:
        a = r["agent"]
        if a not in by_agent:
            by_agent[a] = {"calls": 0, "total_tokens": 0, "cost_usd": 0.0}
        by_agent[a]["calls"] += 1
        by_agent[a]["total_tokens"] += r["total_tokens"]
        by_agent[a]["cost_usd"] = round(by_agent[a]["cost_usd"] + r["cost_usd"], 8)

    return ResponseModel.ok(data={
        "total_cost_usd": round(total_cost, 6),
        "total_calls": len(records),
        "by_agent": by_agent,
        "recent": records[:50],
    })
