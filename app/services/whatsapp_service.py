import logging
import httpx
from ..configs.common import get_settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    def send_message(self, to_mobile: str, body: str) -> bool:
        settings = get_settings()
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.warning("Twilio credentials not configured — skipping WhatsApp message")
            return False

        to_number = to_mobile.strip()
        if not to_number.startswith("+"):
            to_number = "+91" + to_number
        to_whatsapp = f"whatsapp:{to_number}"

        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.post(
                    url,
                    auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                    data={
                        "From": settings.TWILIO_WHATSAPP_FROM,
                        "To": to_whatsapp,
                        "Body": body,
                    },
                )
            if resp.status_code in (200, 201):
                logger.info("WhatsApp message sent to %s", to_whatsapp)
                return True
            logger.error("Twilio error %s: %s", resp.status_code, resp.text)
            return False
        except Exception:
            logger.exception("Failed to send WhatsApp message to %s", to_whatsapp)
            return False
