import uuid
import logging
from typing import List
from fastapi import HTTPException
from ..db.queries.partner_query import PartnerQuery
from ..db.queries.user_query import UserQuery
from ..db.models.partner import Partner
from ..schemas.partner import PartnerCreate, PartnerUpdate
from ..constants import UserType

logger = logging.getLogger("easyclaims")


class PartnerService:
    def __init__(self):
        self.query = PartnerQuery()
        self.user_query = UserQuery()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Partner]:
        return self.query.list_all(skip=skip, limit=limit)

    def get_by_id(self, partner_id: str) -> Partner:
        p = self.query.get_by_id(partner_id)
        if not p:
            raise HTTPException(status_code=404, detail="Partner not found")
        return p

    def get_by_user_id(self, user_id: str) -> Partner:
        p = self.query.get_by_user_id(user_id)
        if not p:
            raise HTTPException(status_code=404, detail="Partner record not found for this user")
        return p

    def create(self, data: PartnerCreate) -> Partner:
        existing = self.user_query.get_user_by_email(str(data.email))
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
        existing_deleted = self.user_query.get_user_by_email_any(str(data.email))
        if existing_deleted:
            raise HTTPException(status_code=409, detail="Email already registered (previously deleted account)")
        user = self.user_query.create_user(
            email=str(data.email), name=data.name,
            user_type=UserType.PARTNER, mobile_no=data.mobile_no,
        )
        api_key = str(uuid.uuid4()).replace("-", "")
        partner = self.query.create(
            user_id=str(user.id), name=data.name,
            partner_type=data.partner_type, city=data.city, api_key=api_key,
            state=data.state,
            legal_company_name=data.legal_company_name,
            trade_name=data.trade_name,
            registered_address=data.registered_address,
            pin_code=data.pin_code,
            gstin=data.gstin,
            pan=data.pan,
            authorized_signatory_name=data.authorized_signatory_name,
            designation=data.designation,
            data_1=data.data_1,
            data_2=data.data_2,
            data_3=data.data_3,
        )
        self._send_welcome_notifications(user, partner)
        return partner

    def _send_welcome_notifications(self, user, partner) -> None:
        from ..configs.common import get_settings
        from .email_service import EmailService
        from .whatsapp_service import WhatsAppService
        settings = get_settings()
        portal_url = f"{settings.FRONTEND_URL}/login"

        try:
            EmailService().send_from_template(str(user.email), "welcome_partner", {
                "partner_name": partner.name,
                "email": str(user.email),
                "portal_url": portal_url,
            })
        except Exception:
            logger.exception("Failed to send welcome email to partner %s", user.email)

        if user.mobile_no:
            try:
                message = (
                    f"Welcome to EasyClaims, {partner.name}! 🎉\n\n"
                    f"Your partner account has been created.\n\n"
                    f"Login at: {portal_url}\n"
                    f"Email: {user.email}\n\n"
                    f"For support, reply to this message."
                )
                WhatsAppService().send_message(user.mobile_no, message)
            except Exception:
                logger.exception("Failed to send welcome WhatsApp to partner %s", user.mobile_no)

    def update(self, partner_id: str, data: PartnerUpdate) -> Partner:
        self.get_by_id(partner_id)
        kwargs = data.model_dump(exclude_none=True)
        p = self.query.update(partner_id, **kwargs)
        if not p:
            raise HTTPException(status_code=404, detail="Partner not found")
        return p

    def delete(self, partner_id: str) -> None:
        self.get_by_id(partner_id)
        self.query.soft_delete(partner_id)

    def regenerate_api_key(self, partner_id: str) -> Partner:
        self.get_by_id(partner_id)
        new_key = str(uuid.uuid4()).replace("-", "")
        return self.query.update(partner_id, api_key=new_key)

    # ── Change Requests ───────────────────────────────────────────────────────

    def create_change_request(self, partner_id: str, requested_fields: dict,
                              reason: str = None):
        from datetime import datetime, timezone
        return self.query.create_change_request(
            partner_id=partner_id,
            requested_fields=requested_fields,
            reason=reason,
        )

    def approve_change_request(self, cr_id: str, admin_id: str = "admin",
                               admin_note: str = None):
        from datetime import datetime, timezone
        cr = self.query.get_change_request(cr_id)
        if not cr:
            raise HTTPException(status_code=404, detail="Change request not found")
        if cr.status != "pending":
            raise HTTPException(status_code=409, detail="Change request is already reviewed")
        # Apply requested_fields to partner record
        fields = cr.requested_fields or {}
        ALLOWED = {
            "name", "city", "state", "legal_company_name", "trade_name",
            "registered_address", "pin_code", "gstin", "pan",
            "authorized_signatory_name", "designation", "data_1", "data_2", "data_3",
        }
        safe_fields = {k: v for k, v in fields.items() if k in ALLOWED}
        if safe_fields:
            self.query.update(str(cr.partner_id), **safe_fields)
        return self.query.update_change_request(
            cr_id,
            status="approved",
            reviewed_by=admin_id,
            reviewed_at=datetime.now(timezone.utc),
            admin_note=admin_note,
        )

    def reject_change_request(self, cr_id: str, admin_id: str = "admin",
                              admin_note: str = None):
        from datetime import datetime, timezone
        cr = self.query.get_change_request(cr_id)
        if not cr:
            raise HTTPException(status_code=404, detail="Change request not found")
        if cr.status != "pending":
            raise HTTPException(status_code=409, detail="Change request is already reviewed")
        return self.query.update_change_request(
            cr_id,
            status="rejected",
            reviewed_by=admin_id,
            reviewed_at=datetime.now(timezone.utc),
            admin_note=admin_note,
        )
