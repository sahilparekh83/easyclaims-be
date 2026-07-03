from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from ...schemas.base import ResponseModel
from ...db.queries.user_query import UserQuery
from ...db.queries.member_query import MemberQuery
from ...db.queries.ticket_query import TicketQuery
from ...services.notification_helper import notify_all_admins, notify_partner
from ...agents import TicketManagerAgent
from ...configs.common import get_settings

webhook_router = APIRouter()


class IncomingMessage(BaseModel):
    channel: str          # "WhatsApp" | "Email"
    message: str
    member_mobile: Optional[str] = None
    member_email: Optional[str] = None


@webhook_router.post("/classify", response_model=ResponseModel)
async def classify_ticket(
    body: IncomingMessage,
    x_api_key: Optional[str] = Header(None),
):
    """
    Classify an incoming WhatsApp or Email message into a ticket.
    Secured via X-API-Key header.
    """
    settings = get_settings()
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    uq = UserQuery()
    member = None
    if body.member_mobile:
        member = uq.get_by_mobile(body.member_mobile)
    if not member and body.member_email:
        member = uq.get_user_by_email(body.member_email)

    member_name = member.name if member else "Unknown"
    member_id = str(member.id) if member else None

    result = TicketManagerAgent().classify(
        message=body.message,
        channel=body.channel,
        member_name=member_name,
        member_id=member_id,
    )

    tq = TicketQuery()
    dup = tq.find_recent_duplicate(user_id=member_id, category=result.category) if member_id else None

    partner_id = None
    if member_id:
        enrollments = MemberQuery().list_enrollments(member_id)
        if enrollments:
            partner_id = str(enrollments[0].partner_id)

    ticket = tq.create(
        channel=body.channel,
        category=result.category,
        priority=result.priority,
        summary=result.summary,
        user_id=member_id,
        partner_id=partner_id,
        is_duplicate=bool(dup),
        duplicate_of_ticket_id=str(dup.id) if dup else None,
    )

    dup_note = " (possible duplicate of an existing open ticket)" if ticket.is_duplicate else ""
    notify_all_admins(
        type="ticket_raised",
        title=f"New {result.category.title()} Ticket — {body.channel}",
        body=f"{member_name}: {result.summary}{dup_note}",
        ref_id=str(ticket.id),
        ref_type="ticket",
    )
    if partner_id:
        notify_partner(
            partner_id=partner_id,
            type="ticket_raised",
            title=f"New {result.category.title()} Ticket — {body.channel}",
            body=f"{member_name}: {result.summary}{dup_note}",
            ref_id=str(ticket.id),
            ref_type="ticket",
        )

    return ResponseModel.ok(data={
        **{**result.model_dump(), "is_duplicate": ticket.is_duplicate},
        "ticket_id": str(ticket.id),
        "member_id": member_id,
        "member_name": member_name,
    })
