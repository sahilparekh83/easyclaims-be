import hmac
import hashlib
import json
import logging

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import PlainTextResponse

from ...db.queries.user_query import UserQuery
from ...agents import TicketManagerAgent, PolicyQAAgent
from ...configs.common import get_settings
from ...services.meta_whatsapp_service import MetaWhatsAppService
from .whatsapp import _get_policy_data, _get_membership

logger = logging.getLogger("easyclaims")
meta_whatsapp_router = APIRouter()


@meta_whatsapp_router.get("/", response_class=PlainTextResponse)
async def meta_whatsapp_verify(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
):
    settings = get_settings()
    if (
        hub_mode == "subscribe"
        and hub_verify_token
        and hub_verify_token == settings.META_WHATSAPP_VERIFY_TOKEN
    ):
        return PlainTextResponse(content=hub_challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Verification token mismatch")


def _verify_signature(raw_body: bytes, signature_header: str, app_secret: str) -> bool:
    if not app_secret or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


@meta_whatsapp_router.post("/", response_class=PlainTextResponse)
async def meta_whatsapp_receive(request: Request):
    settings = get_settings()
    raw_body = await request.body()
    signature = request.headers.get("x-hub-signature-256", "")
    if not _verify_signature(raw_body, signature, settings.META_WHATSAPP_APP_SECRET):
        logger.warning("Meta WhatsApp webhook signature verification failed")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages")
            if not messages:
                # e.g. delivery/read "statuses" callbacks — nothing to reply to.
                continue
            for msg in messages:
                _handle_inbound_message(msg)

    return PlainTextResponse(content="OK", status_code=200)


def _handle_inbound_message(msg: dict) -> None:
    if msg.get("type") != "text":
        # Media/interactive/button messages: out of scope this pass — ack only.
        return

    mobile = "+" + msg.get("from", "")
    body = msg.get("text", {}).get("body", "")
    member = UserQuery().get_customer_by_mobile(mobile)
    member_name = member.name if member else "Unknown"
    member_id = str(member.id) if member else None

    ticket = TicketManagerAgent().classify(
        message=body,
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
            from ...db.queries.member_query import MemberQuery
            profile = MemberQuery().get_profile(member_id)
            language = "Hindi" if profile and profile.preferred_language == "hi" else "English"
            qa = PolicyQAAgent().answer(
                question=body,
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

    MetaWhatsAppService().send_message(mobile, reply)
