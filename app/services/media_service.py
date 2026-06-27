import os
import uuid
import logging

logger = logging.getLogger(__name__)


class MediaService:
    def save_card_pdf(self, pdf_bytes: bytes) -> str:
        """Save PDF bytes to static/cards/ and return its public URL."""
        from ..configs.common import get_settings
        settings = get_settings()

        # Resolve static/cards directory relative to this file
        base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "static", "cards")
        os.makedirs(base_dir, exist_ok=True)

        filename = f"{uuid.uuid4()}.pdf"
        filepath = os.path.join(base_dir, filename)
        with open(filepath, "wb") as f:
            f.write(pdf_bytes)

        url = f"{settings.BACKEND_URL}/static/cards/{filename}"
        logger.info("Saved card PDF: %s", url)
        return url
