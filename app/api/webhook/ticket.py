from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from ...schemas.base import ResponseModel
from ...db.queries.user_query import UserQuery
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
    return ResponseModel.ok(data={
        **result.model_dump(),
        "member_id": member_id,
        "member_name": member_name,
    })
