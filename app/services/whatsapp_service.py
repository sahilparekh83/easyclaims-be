import logging
from ..configs.common import get_settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    def _client(self):
        from twilio.rest import Client
        settings = get_settings()
        return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN), settings

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
