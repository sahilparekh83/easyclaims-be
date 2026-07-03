import logging
from jinja2 import Environment, Undefined
from ..configs.common import get_settings
from ..db.queries.email_template_query import EmailTemplateQuery

logger = logging.getLogger(__name__)

_jinja_env = Environment(undefined=Undefined)


class WhatsAppService:
    def _client(self):
        from twilio.rest import Client
        settings = get_settings()
        return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN), settings

    def send_from_db_template(self, to_mobile: str, slug: str, context: dict,
                              partner_id: str = None, media_url: str = None) -> bool:
        """Render a WhatsApp message body from the editable DB template (`email_templates`
        table, channel_type='whatsapp') and send it. Partner-specific override (E6) is
        used automatically if one exists for this slug, else the system default."""
        tpl = EmailTemplateQuery().get_for_partner(slug, partner_id, channel_type="whatsapp")
        if not tpl:
            logger.error("WhatsApp template '%s' not found in DB — skipping send", slug)
            return False
        try:
            body = _jinja_env.from_string(tpl.html_body).render(**context)
        except Exception:
            logger.exception("Failed to render WhatsApp template '%s'", slug)
            return False
        if media_url:
            return self.send_media(to_mobile, body, media_url)
        return self.send_message(to_mobile, body)

    def send_message(self, to_mobile: str, body: str) -> bool:
        settings = get_settings()
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.warning("Twilio credentials not configured — skipping WhatsApp message")
            return False

        to_number = to_mobile.strip()
        if not to_number.startswith("+"):
            to_number = "+91" + to_number

        try:
            client, _ = self._client()
            msg = client.messages.create(
                from_=settings.TWILIO_WHATSAPP_FROM,
                body=body,
                to=f"whatsapp:{to_number}",
            )
            logger.info("WhatsApp message sent to %s, sid=%s", to_number, msg.sid)
            return True
        except Exception:
            logger.exception("Failed to send WhatsApp message to %s", to_number)
            return False

    def send_media(self, to_mobile: str, body: str, media_url: str) -> bool:
        """Send a WhatsApp message with a media attachment (PDF/image)."""
        settings = get_settings()
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.warning("Twilio credentials not configured — skipping WhatsApp media message")
            return False

        to_number = to_mobile.strip()
        if not to_number.startswith("+"):
            to_number = "+91" + to_number

        try:
            client, _ = self._client()
            msg = client.messages.create(
                from_=settings.TWILIO_WHATSAPP_FROM,
                body=body,
                media_url=[media_url],
                to=f"whatsapp:{to_number}",
            )
            logger.info("WhatsApp media message sent to %s, sid=%s", to_number, msg.sid)
            return True
        except Exception:
            logger.exception("Failed to send WhatsApp media message to %s", to_number)
            return False

    def send_template(self, to_mobile: str, content_sid: str, content_variables: dict) -> bool:
        """Send a pre-approved WhatsApp template message via content_sid."""
        settings = get_settings()
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.warning("Twilio credentials not configured — skipping WhatsApp template message")
            return False

        to_number = to_mobile.strip()
        if not to_number.startswith("+"):
            to_number = "+91" + to_number

        import json
        try:
            client, _ = self._client()
            msg = client.messages.create(
                from_=settings.TWILIO_WHATSAPP_FROM,
                content_sid=content_sid,
                content_variables=json.dumps(content_variables),
                to=f"whatsapp:{to_number}",
            )
            logger.info("WhatsApp template message sent to %s, sid=%s", to_number, msg.sid)
            return True
        except Exception:
            logger.exception("Failed to send WhatsApp template message to %s", to_number)
            return False
