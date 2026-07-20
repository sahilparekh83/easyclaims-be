import sys
import os
import logging
sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from dotenv import load_dotenv
load_dotenv()

from app.services.meta_whatsapp_service import MetaWhatsAppService

TO = sys.argv[1] if len(sys.argv) > 1 else "+91XXXXXXXXXX"
ok = MetaWhatsAppService().send_message(TO, "EasyClaims Meta WhatsApp test — token check")
print("Result:", "SENT" if ok else "FAILED — check logs above")
