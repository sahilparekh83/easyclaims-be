from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from ...schemas.base import ResponseModel
from ...db.queries.policy_query import PolicyQuery
from ...db.queries.member_query import MemberQuery
from ...db.queries.ticket_query import TicketQuery
from ...db.queries.user_query import UserQuery
from ...db.queries.partner_query import PartnerQuery
from ...services.notification_helper import notify_all_admins, notify_partner
from ...services.email_service import EmailService
from ...services.whatsapp_service import WhatsAppService
from ...agents import PolicyQAAgent, ClaimAssistantAgent
from ..deps import _require_customer_enrollment
from ...configs.common import get_settings

member_ai_router = APIRouter()


# ── Policy Q&A ────────────────────────────────────────────────────────────────

class QARequest(BaseModel):
    question: str
    policy_id: Optional[str] = None
    language: str = "English"


@member_ai_router.post("/qa", response_model=ResponseModel)
async def policy_qa(body: QARequest, request: Request, enrollment=Depends(_require_customer_enrollment)):
    """Answer a member's question about their policy using AI."""
    pq = PolicyQuery()
    user_id = str(enrollment.user_id)
    partner_id = str(enrollment.partner_id)

    # Get policy data — use specific policy or most recent
    if body.policy_id:
        policy = pq.get_by_id(body.policy_id, user_id=user_id)
    else:
        policies = pq.list_by_user_partner(user_id, partner_id)
        policy = policies[0] if policies else None

    if not policy:
        raise HTTPException(status_code=404, detail="No policy found")

    policy_data = policy.extracted_fields or {
        "policy_number": policy.policy_number,
        "insurer": policy.insurer,
        "sum_insured": policy.sum_insured,
        "end_date": str(policy.end_date) if policy.end_date else None,
    }

    answer = PolicyQAAgent().answer(
        question=body.question,
        policy_data=policy_data,
        membership_status=enrollment.status,
        membership_end=str(enrollment.end_date),
        language=body.language,
        member_id=user_id,
    )
    return ResponseModel.ok(data=answer.model_dump())


# ── Claim Assistant ───────────────────────────────────────────────────────────

class ClaimRequest(BaseModel):
    claim_type: str          # "Health" | "Motor" | "Life"
    incident_details: str
    policy_id: Optional[str] = None
    language: str = "English"


@member_ai_router.post("/claim", response_model=ResponseModel)
async def claim_assist(body: ClaimRequest, request: Request, enrollment=Depends(_require_customer_enrollment)):
    """AI-assisted claim filing — returns document checklist and next steps."""
    pq = PolicyQuery()
    user_id = str(enrollment.user_id)
    partner_id = str(enrollment.partner_id)

    if body.policy_id:
        policy = pq.get_by_id(body.policy_id, user_id=user_id)
    else:
        policies = pq.list_by_user_partner(user_id, partner_id)
        policy = policies[0] if policies else None

    policy_data = {}
    if policy:
        policy_data = policy.extracted_fields or {
            "policy_number": policy.policy_number,
            "insurer": policy.insurer,
            "sum_insured": policy.sum_insured,
        }

    result = ClaimAssistantAgent().assist(
        claim_type=body.claim_type,
        incident_details=body.incident_details,
        policy_data=policy_data,
        language=body.language,
        member_id=user_id,
    )

    tq = TicketQuery()
    dup = tq.find_recent_duplicate(user_id=user_id, category="claim")
    ticket = tq.create(
        channel="Portal",
        category="claim",
        priority="high",
        summary=result.incident_summary,
        user_id=user_id,
        partner_id=partner_id,
        ref_policy_id=str(policy.id) if policy else None,
        is_duplicate=bool(dup),
        duplicate_of_ticket_id=str(dup.id) if dup else None,
    )

    member = UserQuery().get_user_by_id(user_id)
    member_label = (member.name or member.email) if member else "A member"
    member_email = member.email if member else None
    member_mobile = member.mobile_no if member else None
    dup_note = " (possible duplicate of an existing open ticket)" if ticket.is_duplicate else ""

    notify_all_admins(
        type="ticket_raised",
        title=f"New Claim Raised — {body.claim_type}",
        body=f"{member_label} raised a {body.claim_type} claim.{dup_note}",
        ref_id=str(ticket.id),
        ref_type="ticket",
    )
    notify_partner(
        partner_id=partner_id,
        type="ticket_raised",
        title=f"New Claim Raised — {body.claim_type}",
        body=f"{member_label} raised a {body.claim_type} claim.{dup_note}",
        ref_id=str(ticket.id),
        ref_type="ticket",
    )

    # Email + WhatsApp to member
    settings = get_settings()
    ticket_id_str = str(ticket.id)
    summary_str = result.incident_summary or ""
    if member_email:
        try:
            EmailService().send_ticket_raised(
                to_email=member_email,
                member_name=member_label,
                ticket_id=ticket_id_str,
                summary=summary_str,
                channel="Portal",
                partner_id=partner_id,
            )
        except Exception:
            pass
    if member_mobile:
        try:
            WhatsAppService().send_from_db_template(
                to_mobile=member_mobile,
                slug="wa_ticket_raised",
                context={
                    "member_name": member_label,
                    "ticket_id": ticket_id_str,
                    "summary": summary_str,
                },
                partner_id=partner_id,
            )
        except Exception:
            pass

    return ResponseModel.ok(data={**result.model_dump(), "ticket_id": ticket_id_str, "is_duplicate": ticket.is_duplicate})


@member_ai_router.get("/tickets", response_model=ResponseModel)
async def list_member_tickets(
    skip: int = 0,
    limit: int = 20,
    enrollment=Depends(_require_customer_enrollment),
):
    user_id = str(enrollment.user_id)
    tickets = TicketQuery().list_by_user(user_id=user_id, skip=skip, limit=limit)
    return ResponseModel.ok(data=[
        {
            "id": str(t.id),
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "summary": t.summary,
            "channel": t.channel,
            "is_duplicate": t.is_duplicate,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tickets
    ])
