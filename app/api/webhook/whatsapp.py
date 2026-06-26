import logging
from xml.sax.saxutils import escape as _xml_escape

from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse
from typing import Optional

from ...db.queries.user_query import UserQuery
from ...db.queries.policy_query import PolicyQuery
from ...db.queries.member_query import MemberQuery
from ...agents import TicketManagerAgent, PolicyQAAgent
from ...configs.common import get_settings
from ...constants import UserType

logger = logging.getLogger("easyclaims")
whatsapp_router = APIRouter()


def _twiml(message: str) -> PlainTextResponse:
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f"<Response>\n    <Message>{_xml_escape(message)}</Message>\n</Response>"
    )
    return PlainTextResponse(content=xml, media_type="text/xml")


def _get_policy_data(user_id: str) -> dict:
    policies = PolicyQuery().list_by_user(user_id)
    if not policies:
        return {}
    active = [p for p in policies if p.status == "active"]
    p = active[0] if active else policies[0]
    ef = p.extracted_fields or {}
    data = {
        "policy_number": p.policy_number,
        "insurer": p.insurer,
        "sum_insured": p.sum_insured,
        "start_date": str(p.start_date) if p.start_date else None,
        "end_date": str(p.end_date) if p.end_date else None,
        "status": p.status,
    }
    data.update(ef)
    return {k: v for k, v in data.items() if v is not None}


def _get_membership(user_id: str):
    enrollment = MemberQuery().get_first_active_enrollment(user_id)
    if not enrollment:
        return "inactive", "N/A"
    return enrollment.status, str(enrollment.end_date) if enrollment.end_date else "N/A"


@whatsapp_router.post("/incoming", response_class=PlainTextResponse)
async def whatsapp_incoming(
    Body: str = Form(default=""),
    From: str = Form(...),
    To: Optional[str] = Form(None),
    NumMedia: Optional[str] = Form(default="0"),
    MediaUrl0: Optional[str] = Form(default=None),
    MediaContentType0: Optional[str] = Form(default=None),
):
    mobile = From.replace("whatsapp:", "").strip()
    member = UserQuery().get_customer_by_mobile(mobile)
    member_name = member.name if member else "Unknown"
    member_id = str(member.id) if member else None

    # ── Reject any file/media uploads ────────────────────────────────────────
    if MediaUrl0:
        settings = get_settings()
        upload_url = f"{settings.FRONTEND_URL}/upload"
        return _twiml(
            "To upload your policy document, please use the link below:\n"
            f"{upload_url}"
        )

    # ── Text message flow ─────────────────────────────────────────────────────
    ticket = TicketManagerAgent().classify(
        message=Body,
        channel="WhatsApp",
        member_name=member_name,
        member_id=member_id,
    )

    if ticket.category.lower() == "query" and member:
        policy_data = _get_policy_data(member_id)

        if not policy_data:
            settings = get_settings()
            upload_url = f"{settings.FRONTEND_URL}/upload"
            reply = (
                f"Hello {member_name}! 👋\n\n"
                "We could not find an active policy on your account.\n\n"
                "To upload your policy document, visit:\n"
                f"{upload_url}"
            )
        else:
            membership_status, membership_end = _get_membership(member_id)
            profile = MemberQuery().get_profile(member_id)
            language = "Hindi" if profile and profile.preferred_language == "hi" else "English"
            qa = PolicyQAAgent().answer(
                question=Body,
                policy_data=policy_data,
                membership_status=membership_status,
                membership_end=membership_end,
                language=language,
                member_id=member_id,
            )
            reply = qa.answer

    elif ticket.category.lower() == "query" and not member:
        reply = (
            "We could not find your account. "
            "Please contact support with your registered email."
        )

    else:
        reply = (
            f"*{ticket.category.title()}* request received.\n\n"
            f"{ticket.summary}\n\n"
            f"Priority: {ticket.priority.upper()} — Our team will follow up shortly."
        )

    return _twiml(reply)
