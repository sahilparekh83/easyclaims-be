import logging
import httpx
from ..configs.common import get_settings

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.facebook.com"


class MetaWhatsAppService:
    def _client(self, settings) -> httpx.Client:
        return httpx.Client(
            base_url=f"{GRAPH_BASE}/{settings.META_WHATSAPP_API_VERSION}",
            headers={"Authorization": f"Bearer {settings.META_WHATSAPP_ACCESS_TOKEN}"},
            timeout=15.0,
        )

    def _normalize(self, to_mobile: str) -> str:
        n = to_mobile.strip()
        if not n.startswith("+"):
            n = "+91" + n
        return n.lstrip("+")

    def send_message(self, to_mobile: str, body: str) -> bool:
        settings = get_settings()
        if not settings.META_WHATSAPP_PHONE_NUMBER_ID or not settings.META_WHATSAPP_ACCESS_TOKEN:
            logger.warning("Meta WhatsApp credentials not configured — skipping message")
            return False

        to_number = self._normalize(to_mobile)
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": body, "preview_url": False},
        }
        try:
            with self._client(settings) as client:
                resp = client.post(f"/{settings.META_WHATSAPP_PHONE_NUMBER_ID}/messages", json=payload)
            if resp.status_code >= 400:
                logger.error(
                    "Meta WhatsApp send failed to %s: status=%s body=%s",
                    to_number, resp.status_code, resp.text,
                )
                return False
            data = resp.json()
            wamid = data.get("messages", [{}])[0].get("id")
            logger.info("Meta WhatsApp message sent to %s, id=%s", to_number, wamid)
            return True
        except Exception:
            logger.exception("Failed to send Meta WhatsApp message to %s", to_number)
            return False

    def send_template(self, to_mobile: str, template_name: str, language_code: str,
                      body_params: list, header_media_url: str = None, header_type: str = None) -> bool:
        """Send a Meta-approved template message (business-initiated messages must use
        this — free-form type:text only works as a reply within an open 24h session)."""
        settings = get_settings()
        if not settings.META_WHATSAPP_PHONE_NUMBER_ID or not settings.META_WHATSAPP_ACCESS_TOKEN:
            logger.warning("Meta WhatsApp credentials not configured — skipping template message")
            return False

        to_number = self._normalize(to_mobile)
        components = []
        if header_media_url and header_type:
            components.append({
                "type": "header",
                "parameters": [{"type": header_type, header_type: {"link": header_media_url}}],
            })
        if body_params:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": str(v)} for v in body_params],
            })
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components,
            },
        }
        try:
            with self._client(settings) as client:
                resp = client.post(f"/{settings.META_WHATSAPP_PHONE_NUMBER_ID}/messages", json=payload)
            if resp.status_code >= 400:
                logger.error(
                    "Meta WhatsApp template send failed to %s (template=%s): status=%s body=%s",
                    to_number, template_name, resp.status_code, resp.text,
                )
                return False
            data = resp.json()
            wamid = data.get("messages", [{}])[0].get("id")
            logger.info("Meta WhatsApp template '%s' sent to %s, id=%s", template_name, to_number, wamid)
            return True
        except Exception:
            logger.exception("Failed to send Meta WhatsApp template '%s' to %s", template_name, to_number)
            return False

    def send_template_from_db(self, to_mobile: str, slug: str, variables: dict,
                              partner_id: str = None, media_url: str = None) -> bool:
        """Look up the approved-template metadata for `slug` (app/db/models/whatsapp_template.py)
        and send it. No-ops (with a warning) if the row doesn't exist or hasn't been
        wired up to a Meta-approved template name yet — safe to call unconditionally
        from call sites even before templates are approved."""
        from ..db.queries.whatsapp_template_query import WhatsAppTemplateQuery
        row = WhatsAppTemplateQuery().get_for_partner(slug, partner_id)
        if not row or not row.meta_template_name:
            logger.warning("No approved Meta template configured for slug '%s' — skipping WhatsApp send", slug)
            return False

        body_params = [str(variables.get(key, "")) for key in (row.variable_order or [])]
        header_media_url = media_url if row.header_type else None
        return self.send_template(
            to_mobile, row.meta_template_name, row.meta_template_language,
            body_params, header_media_url=header_media_url, header_type=row.header_type,
        )

    def send_media(self, to_mobile: str, body: str, media_url: str) -> bool:
        """Meta requires the caption on the media object itself, not as a
        separate text message like Twilio — audio media does not support captions."""
        settings = get_settings()
        if not settings.META_WHATSAPP_PHONE_NUMBER_ID or not settings.META_WHATSAPP_ACCESS_TOKEN:
            logger.warning("Meta WhatsApp credentials not configured — skipping media message")
            return False

        to_number = self._normalize(to_mobile)
        media_type = "document"
        if media_url.lower().endswith((".jpg", ".jpeg", ".png")):
            media_type = "image"
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": media_type,
            media_type: {"link": media_url, "caption": body},
        }
        try:
            with self._client(settings) as client:
                resp = client.post(f"/{settings.META_WHATSAPP_PHONE_NUMBER_ID}/messages", json=payload)
            if resp.status_code >= 400:
                logger.error(
                    "Meta WhatsApp media send failed to %s: status=%s body=%s",
                    to_number, resp.status_code, resp.text,
                )
                return False
            logger.info("Meta WhatsApp media message sent to %s", to_number)
            return True
        except Exception:
            logger.exception("Failed to send Meta WhatsApp media message to %s", to_number)
            return False
