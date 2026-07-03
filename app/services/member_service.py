import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException
from ..db.queries.member_query import MemberQuery
from ..db.queries.user_query import UserQuery
from ..db.queries.plan_query import PlanQuery
from ..db.queries.partner_query import PartnerQuery
from ..db.queries.activity_query import ActivityQuery
from ..db.models.member import MemberEnrollment, MemberProfile, FamilyMember, Nominee, DpdpConsent
from ..schemas.member import (
    MemberCreate, ProfileUpdate,
    FamilyMemberCreate, FamilyMemberUpdate,
    NomineeCreate, NomineeUpdate,
    ConsentCreate,
)
from ..constants import UserType

logger = logging.getLogger(__name__)


class MemberService:
    def __init__(self):
        self.q = MemberQuery()
        self.user_q = UserQuery()
        self.plan_q = PlanQuery()
        self.partner_q = PartnerQuery()

    def create_member(self, data: MemberCreate) -> dict:
        is_new_user = False
        existing = self.user_q.get_user_by_email(str(data.email))
        if existing:
            # Block re-enrollment under the same partner
            if data.partner_id and self.q.get_enrollment(str(existing.id), data.partner_id):
                raise HTTPException(
                    status_code=409,
                    detail=f"This member ({data.email}) is already enrolled under this partner.",
                )
            user = existing
        else:
            is_new_user = True
            user = self.user_q.create_user(
                email=str(data.email), name=data.name,
                user_type=UserType.CUSTOMER, mobile_no=data.mobile_no,
            )

        partner = self.partner_q.get_by_id(data.partner_id)
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        if partner.status != "Active":
            raise HTTPException(
                status_code=403,
                detail=f"This partner is {partner.status.lower()} — new member registrations are blocked. "
                       "Existing members are unaffected.",
            )

        if data.plan_id:
            plan = self.plan_q.get_by_id(data.plan_id)
            if not plan or plan.status != "Active":
                raise HTTPException(status_code=404, detail="Plan not found or not active")
            plan_id = data.plan_id
        else:
            available = self.plan_q.list_for_partner(data.partner_id)
            if not available:
                raise HTTPException(status_code=422, detail="No active plans available for this partner")
            plan_id = str(available[0].id)

        enrollment = self.q.create_enrollment(str(user.id), data.partner_id, plan_id)
        profile_fields = {}
        for f in ("gender", "address_line", "address_city", "address_state", "address_pin",
                  "sale_date", "sales_channel", "branch_code", "salesperson_name",
                  "employee_code", "data1", "data2", "data3"):
            v = getattr(data, f, None)
            if v is not None:
                profile_fields[f] = v
        self.q.upsert_profile(str(user.id), **profile_fields)

        plan_obj = self.plan_q.get_by_id(plan_id)

        self._deduct_float_for_enrollment(partner, plan_obj, enrollment, user)

        if is_new_user:
            self._send_welcome_email(user, partner)
            self._send_welcome_whatsapp(user, partner)
        else:
            self._send_new_partner_email(user, partner)
            self._send_new_partner_whatsapp(user, partner)

        self._send_membership_card_email(user, partner, plan_obj, enrollment)
        self._send_membership_card_whatsapp(user, partner, plan_obj, enrollment)

        self._notify_admins_new_member(user, partner)
        return {"user": user, "enrollment": enrollment}

    def _deduct_float_for_enrollment(self, partner, plan_obj, enrollment, user) -> None:
        """Deducts the plan price from the partner's prepaid float balance.
        Best-effort: never blocks enrollment creation, even if the partner
        goes into a negative balance — that case is surfaced as a Low Float alert."""
        if not plan_obj or not plan_obj.price:
            return
        try:
            from ..db.queries.float_query import FloatQuery
            fq = FloatQuery()
            txn = fq.deduct(
                str(partner.id), plan_obj.price,
                ref_type="enrollment", ref_id=str(enrollment.id),
                note=f"Enrollment — {user.name or user.email} ({plan_obj.name})",
            )
            if txn and txn.balance_after <= partner.low_float_threshold:
                from .notification_helper import notify_all_admins, notify_partner
                notify_all_admins(
                    type="low_float_alert",
                    title=f"Low Float — {partner.name}",
                    body=f"{partner.name}'s float balance is now {txn.balance_after}.",
                    ref_id=str(partner.id), ref_type="partner",
                )
                notify_partner(
                    partner_id=str(partner.id),
                    type="low_float_alert",
                    title="Low Float Balance",
                    body=f"Your float balance is now {txn.balance_after}. Please top up to continue enrolling members.",
                    ref_id=str(partner.id), ref_type="partner",
                )
        except Exception:
            logger.exception("Failed to deduct float balance for partner %s", partner.id)

    def _notify_admins_new_member(self, user, partner) -> None:
        try:
            from .notification_helper import notify_all_admins
            notify_all_admins(
                type="member_joined",
                title=f"New Member — {user.name or user.email}",
                body=f"{user.name or user.email} joined via {partner.name}.",
                ref_id=str(user.id),
                ref_type="member",
            )
        except Exception:
            logger.exception("Failed to notify admins of new member %s", user.id)

    def _send_welcome_email(self, user, partner) -> None:
        try:
            from .email_service import EmailService
            from ..configs.common import get_settings
            settings = get_settings()
            login_url = f"{settings.FRONTEND_URL}/login"
            EmailService().send_welcome_member(
                to_email=user.email,
                member_name=user.name or user.email,
                partner_name=partner.name,
                login_url=login_url,
                partner_id=str(partner.id),
            )
        except Exception:
            logger.exception("Failed to send welcome email to %s", user.email)

    def _send_welcome_whatsapp(self, user, partner) -> None:
        if not user.mobile_no:
            return
        try:
            from .whatsapp_service import WhatsAppService
            from ..configs.common import get_settings
            settings = get_settings()
            WhatsAppService().send_from_db_template(
                user.mobile_no, "wa_welcome_member",
                {
                    "member_name": user.name or "there",
                    "partner_name": partner.name,
                    "upload_url": f"{settings.FRONTEND_URL}/upload",
                },
                partner_id=str(partner.id),
            )
        except Exception:
            logger.exception("Failed to send welcome WhatsApp to %s", user.mobile_no)

    def _send_new_partner_email(self, user, partner) -> None:
        try:
            from .email_service import EmailService
            from ..configs.common import get_settings
            settings = get_settings()
            EmailService().send_new_partner_welcome(
                to_email=user.email,
                member_name=user.name or user.email,
                partner_name=partner.name,
                login_url=f"{settings.FRONTEND_URL}/login",
                partner_id=str(partner.id),
            )
        except Exception:
            logger.exception("Failed to send new-partner email to %s", user.email)

    def _send_new_partner_whatsapp(self, user, partner) -> None:
        if not user.mobile_no:
            return
        try:
            from .whatsapp_service import WhatsAppService
            from ..configs.common import get_settings
            settings = get_settings()
            WhatsAppService().send_from_db_template(
                user.mobile_no, "wa_new_partner",
                {
                    "member_name": user.name or "there",
                    "partner_name": partner.name,
                    "login_url": f"{settings.FRONTEND_URL}/login",
                },
                partner_id=str(partner.id),
            )
        except Exception:
            logger.exception("Failed to send new-partner WhatsApp to %s", user.mobile_no)

    def _send_membership_card_email(self, user, partner, plan, enrollment=None) -> None:
        try:
            from .email_service import EmailService
            from ..configs.common import get_settings
            settings = get_settings()
            membership_number = f"MEM-{str(enrollment.id)[:8].upper()}" if enrollment else None
            EmailService().send_membership_card(
                to_email=user.email,
                member_name=user.name or user.email,
                member_email=user.email,
                partner_name=partner.name,
                partner_type=getattr(partner, "partner_type", "Partner"),
                plan_name=plan.name,
                plan=plan,
                login_url=f"{settings.FRONTEND_URL}/login",
                membership_number=membership_number,
                start_date=str(enrollment.start_date) if enrollment and enrollment.start_date else None,
                end_date=str(enrollment.end_date) if enrollment and enrollment.end_date else None,
                partner_address=getattr(partner, "registered_address", None),
                card_logo_key=getattr(partner, "card_logo_key", None),
                card_color=getattr(partner, "card_color", None),
                partner_id=str(partner.id),
            )
        except Exception:
            logger.exception("Failed to send membership card email to %s", user.email)

    def _send_membership_card_whatsapp(self, user, partner, plan, enrollment=None) -> None:
        if not user.mobile_no:
            return
        try:
            from .whatsapp_service import WhatsAppService
            from .pdf_service import PdfService
            from .media_service import MediaService
            from ..configs.common import get_settings
            settings = get_settings()

            logo_bytes = None
            card_logo_key = getattr(partner, "card_logo_key", None)
            if card_logo_key:
                try:
                    from ..storage import get_storage
                    logo_bytes = get_storage().download(card_logo_key)
                except Exception:
                    logger.warning("Failed to fetch partner card logo '%s' for WhatsApp card", card_logo_key)

            membership_number = f"MEM-{str(enrollment.id)[:8].upper()}" if enrollment else None
            pdf_bytes = PdfService().generate_membership_card_pdf(
                member_name=user.name or user.email,
                member_email=user.email,
                partner_name=partner.name,
                partner_type=getattr(partner, "partner_type", "Partner"),
                plan_name=plan.name,
                plan=plan,
                membership_number=membership_number,
                start_date=str(enrollment.start_date) if enrollment and enrollment.start_date else None,
                end_date=str(enrollment.end_date) if enrollment and enrollment.end_date else None,
                partner_address=getattr(partner, "registered_address", None),
                partner_logo_bytes=logo_bytes,
                partner_color=getattr(partner, "card_color", None),
            )
            media_url = MediaService().save_card_pdf(pdf_bytes)

            benefits = []
            if getattr(plan, "benefit_aiqa", False):
                benefits.append("• AI Health Query Assistant")
            tc = getattr(plan, "benefit_teleconsult_sessions", 0)
            if tc:
                benefits.append(f"• Tele-consultation ({tc} sessions)")
            wc = getattr(plan, "benefit_wellness_sessions", 0)
            if wc:
                benefits.append(f"• Wellness Sessions ({wc})")
            if getattr(plan, "benefit_hospital_cash", False):
                benefits.append("• Hospital Cash Benefit")
            if getattr(plan, "benefit_emergency_assist", False):
                benefits.append("• Emergency Assistance")
            extra_benefits = "\n".join(benefits) if benefits else ""

            WhatsAppService().send_from_db_template(
                user.mobile_no, "wa_membership_card",
                {
                    "member_name": user.name or user.email,
                    "partner_name": partner.name,
                    "plan_name": plan.name,
                    "benefit_family": plan.benefit_family,
                    "benefit_slots": plan.benefit_slots,
                    "benefit_claim": plan.benefit_claim,
                    "extra_benefits": extra_benefits,
                    "login_url": f"{settings.FRONTEND_URL}/login",
                },
                partner_id=str(partner.id),
                media_url=media_url,
            )
        except Exception:
            logger.exception("Failed to send membership card WhatsApp to %s", user.mobile_no)

    def list_enrollments(self, user_id: str) -> List[MemberEnrollment]:
        return self.q.list_enrollments(user_id)

    def get_enrollment(self, user_id: str, partner_id: str) -> MemberEnrollment:
        e = self.q.get_enrollment(user_id, partner_id)
        if not e:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        return e

    def get_active_enrollment(self, user_id: str, partner_id: Optional[str]) -> MemberEnrollment:
        if partner_id:
            e = self.q.get_enrollment(user_id, partner_id)
            if not e:
                raise HTTPException(status_code=403, detail="No enrollment found for this partner")
            if e.status == "Cancelled":
                raise HTTPException(status_code=403, detail="This membership has been cancelled")
            return e
        e = self.q.get_first_active_enrollment(user_id)
        if not e:
            raise HTTPException(status_code=404, detail="No active enrollment found")
        return e

    def switch_plan(self, user_id: str, partner_id: str, plan_id: str,
                    changed_by: str = "system") -> MemberEnrollment:
        available = self.plan_q.list_for_partner(partner_id)
        available_ids = [str(p.id) for p in available]
        if plan_id not in available_ids:
            raise HTTPException(status_code=404, detail="Plan not available for this partner")

        # Get current plan before switching (for history)
        old_enrollment = self.q.get_enrollment(user_id, partner_id)
        old_plan_id = str(old_enrollment.plan_id) if old_enrollment else None

        e = self.q.update_enrollment(user_id, partner_id, plan_id=plan_id)
        if not e:
            raise HTTPException(status_code=404, detail="Enrollment not found")

        # Log history
        try:
            from ..db.queries.enrollment_history_query import EnrollmentHistoryQuery
            EnrollmentHistoryQuery().create(
                enrollment_id=str(e.id),
                user_id=user_id,
                partner_id=partner_id,
                to_plan_id=plan_id,
                from_plan_id=old_plan_id,
                action="plan_changed",
                changed_by=changed_by,
            )
        except Exception:
            logger.exception("Failed to log enrollment history for user %s", user_id)

        # Send email notification to member
        try:
            member = self.user_q.get_user_by_id(user_id)
            old_plan = self.plan_q.get_by_id(old_plan_id) if old_plan_id else None
            new_plan = self.plan_q.get_by_id(plan_id)
            if member and new_plan:
                from .email_service import EmailService
                EmailService().send_plan_changed(
                    to_email=member.email,
                    member_name=member.name or member.email,
                    old_plan=old_plan.name if old_plan else "—",
                    new_plan=new_plan.name,
                    changed_by=changed_by,
                    partner_id=partner_id,
                )
        except Exception:
            logger.exception("Failed to send plan-changed email for user %s", user_id)

        return e

    def renew_enrollment(self, user_id: str, partner_id: str,
                         changed_by: str = "system") -> MemberEnrollment:
        """Extend enrollment by 1 year from today and set status=Active."""
        from datetime import date, timedelta
        e = self.q.get_enrollment(user_id, partner_id)
        if not e:
            raise HTTPException(status_code=404, detail="Enrollment not found")

        new_start = date.today()
        new_end = new_start + timedelta(days=365)
        updated = self.q.update_enrollment(
            user_id, partner_id,
            status="Active",
            start_date=new_start,
            end_date=new_end,
        )
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to renew enrollment")

        # Log history
        try:
            from ..db.queries.enrollment_history_query import EnrollmentHistoryQuery
            EnrollmentHistoryQuery().create(
                enrollment_id=str(updated.id),
                user_id=user_id,
                partner_id=partner_id,
                to_plan_id=str(updated.plan_id),
                from_plan_id=str(updated.plan_id),
                action="renewed",
                changed_by=changed_by,
                note=f"Renewed until {new_end.isoformat()}",
            )
        except Exception:
            logger.exception("Failed to log renewal history for user %s", user_id)

        # Send email notification to member
        try:
            member = self.user_q.get_user_by_id(user_id)
            plan = self.plan_q.get_by_id(str(updated.plan_id))
            if member and plan:
                from .email_service import EmailService
                EmailService().send_from_template(
                    to_email=member.email,
                    slug="enrollment_renewed",
                    context={
                        "member_name": member.name or member.email,
                        "plan_name": plan.name,
                        "end_date": str(new_end),
                    },
                    partner_id=partner_id,
                )
                # In-app notification
                from ..db.queries.activity_query import NotificationQuery
                NotificationQuery().create(
                    recipient_user_id=user_id,
                    type="plan_renewed",
                    title="Your plan has been renewed",
                    body=f"Your plan '{plan.name}' has been renewed until {new_end.isoformat()}.",
                    ref_id=str(updated.plan_id),
                    ref_type="plan",
                )
        except Exception:
            logger.exception("Failed to send renewal email for user %s", user_id)

        return updated

    def cancel_enrollment(self, user_id: str, partner_id: str, reason: str = None,
                          changed_by: str = "admin") -> MemberEnrollment:
        """Admin cancels a member's membership. Portal access is blocked immediately."""
        e = self.q.get_enrollment(user_id, partner_id)
        if not e:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        if e.status == "Cancelled":
            raise HTTPException(status_code=400, detail="Enrollment is already cancelled")

        updated = self.q.update_enrollment(user_id, partner_id, status="Cancelled")
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to cancel enrollment")

        try:
            from ..db.queries.enrollment_history_query import EnrollmentHistoryQuery
            EnrollmentHistoryQuery().create(
                enrollment_id=str(updated.id),
                user_id=user_id,
                partner_id=partner_id,
                to_plan_id=str(updated.plan_id),
                from_plan_id=str(updated.plan_id),
                action="cancelled",
                changed_by=changed_by,
                note=reason,
            )
        except Exception:
            logger.exception("Failed to log cancellation history for user %s", user_id)

        try:
            member = self.user_q.get_user_by_id(user_id)
            plan = self.plan_q.get_by_id(str(updated.plan_id))
            if member and plan:
                from .email_service import EmailService
                EmailService().send_membership_cancelled(
                    to_email=member.email,
                    member_name=member.name or member.email,
                    plan_name=plan.name,
                    reason=reason,
                    partner_id=partner_id,
                )
                from ..db.queries.activity_query import NotificationQuery
                NotificationQuery().create(
                    recipient_user_id=user_id,
                    type="membership_cancelled",
                    title="Your membership has been cancelled",
                    body=f"Your '{plan.name}' membership has been cancelled." + (f" Reason: {reason}" if reason else ""),
                    ref_id=str(updated.plan_id),
                    ref_type="plan",
                )
        except Exception:
            logger.exception("Failed to send cancellation notification for user %s", user_id)

        return updated

    def get_profile(self, user_id: str) -> dict:
        user = self.user_q.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        profile = self.q.get_profile(user_id)
        return {"user": user, "profile": profile}

    def update_profile(self, user_id: str, data: ProfileUpdate) -> dict:
        user_field_names = {"name", "mobile_no"}
        user_fields, profile_fields = {}, {}
        for field, value in data.model_dump(exclude_none=True).items():
            if field in user_field_names:
                user_fields[field] = value
            else:
                profile_fields[field] = value
        if user_fields:
            self.user_q.update_user(user_id, **user_fields)
        if profile_fields:
            self.q.upsert_profile(user_id, **profile_fields)
        return self.get_profile(user_id)

    def update_member_by_admin(self, member_id: str, data, admin_id: str, ip: str = None) -> dict:
        from .audit_service import AuditService
        user = self.user_q.get_user_by_id(member_id)
        if not user:
            raise HTTPException(status_code=404, detail="Member not found")

        old_user = {"name": user.name, "mobile_no": user.mobile_no, "is_active": user.is_active}
        profile = self.q.get_profile(member_id)
        old_profile = {
            "gender": profile.gender if profile else None,
            "address_line": profile.address_line if profile else None,
            "address_city": profile.address_city if profile else None,
            "address_state": profile.address_state if profile else None,
            "address_pin": profile.address_pin if profile else None,
            "sale_date": str(profile.sale_date) if profile and profile.sale_date else None,
            "sales_channel": profile.sales_channel if profile else None,
            "branch_code": profile.branch_code if profile else None,
            "salesperson_name": profile.salesperson_name if profile else None,
            "employee_code": profile.employee_code if profile else None,
            "data1": profile.data1 if profile else None,
            "data2": profile.data2 if profile else None,
            "data3": profile.data3 if profile else None,
        }

        payload = data.model_dump(exclude_none=True)
        user_fields = {k: v for k, v in payload.items() if k in ("name", "mobile_no", "is_active")}
        profile_fields = {k: v for k, v in payload.items() if k not in ("name", "mobile_no", "is_active")}

        if user_fields:
            self.user_q.update_user(member_id, **user_fields)
        if profile_fields:
            self.q.upsert_profile(member_id, **profile_fields)

        AuditService().log(
            actor_id=admin_id, actor_type="admin",
            action="member_updated",
            entity_type="member", entity_id=member_id,
            old_value={**old_user, **old_profile},
            new_value=payload,
            ip_address=ip,
        )
        u = self.user_q.get_user_by_id(member_id)
        p = self.q.get_profile(member_id)
        return {
            "id": str(u.id), "name": u.name, "email": u.email,
            "mobile_no": u.mobile_no, "is_active": u.is_active,
            "gender": p.gender if p else None,
            "address_line": p.address_line if p else None,
            "address_city": p.address_city if p else None,
            "address_state": p.address_state if p else None,
            "address_pin": p.address_pin if p else None,
            "sale_date": str(p.sale_date) if p and p.sale_date else None,
            "sales_channel": p.sales_channel if p else None,
            "branch_code": p.branch_code if p else None,
            "salesperson_name": p.salesperson_name if p else None,
            "employee_code": p.employee_code if p else None,
            "data1": p.data1 if p else None,
            "data2": p.data2 if p else None,
            "data3": p.data3 if p else None,
        }

    def create_change_request(self, user_id: str, data) -> object:
        from .audit_service import AuditService
        cr = self.q.create_change_request(
            user_id=user_id,
            requested_fields=data.requested_fields,
            reason=data.reason,
        )
        # Notify all admins
        try:
            from .notification_helper import notify_all_admins
            user = self.user_q.get_user_by_id(user_id)
            notify_all_admins(
                type="change_request",
                title=f"Profile Change Request — {user.name or user.email}",
                body=f"{user.name or user.email} requested changes to their profile.",
                ref_id=str(cr.id),
                ref_type="change_request",
            )
        except Exception:
            logger.exception("Failed to notify admins of change request %s", cr.id)
        AuditService().log(
            actor_id=user_id, actor_type="member",
            action="change_request_created",
            entity_type="change_request", entity_id=str(cr.id),
            new_value=data.requested_fields,
        )
        return cr

    def approve_change_request(self, request_id: str, admin_id: str, admin_note: str = None, ip: str = None) -> object:
        from .audit_service import AuditService
        cr = self.q.get_change_request(request_id)
        if not cr:
            raise HTTPException(status_code=404, detail="Change request not found")
        if cr.status != "pending":
            raise HTTPException(status_code=400, detail="Change request already reviewed")

        # Apply the changes
        from app.schemas.member import AdminMemberUpdate
        update_data = AdminMemberUpdate(**cr.requested_fields)
        self.update_member_by_admin(
            member_id=str(cr.user_id),
            data=update_data,
            admin_id=admin_id,
            ip=ip,
        )
        updated = self.q.update_change_request(
            request_id, status="approved", reviewed_by=admin_id, admin_note=admin_note
        )
        # Notify member
        try:
            from ..db.queries.activity_query import NotificationQuery
            NotificationQuery().create(
                recipient_user_id=str(cr.user_id),
                type="change_request_approved",
                title="Your profile change request was approved",
                body="Your requested profile changes have been applied.",
                ref_id=request_id,
                ref_type="change_request",
            )
        except Exception:
            logger.exception("Failed to notify member of change request approval %s", request_id)
        AuditService().log(
            actor_id=admin_id, actor_type="admin",
            action="change_request_approved",
            entity_type="change_request", entity_id=request_id,
            new_value=cr.requested_fields,
            ip_address=ip,
        )
        return updated

    def reject_change_request(self, request_id: str, admin_id: str, admin_note: str = None) -> object:
        from .audit_service import AuditService
        cr = self.q.get_change_request(request_id)
        if not cr:
            raise HTTPException(status_code=404, detail="Change request not found")
        if cr.status != "pending":
            raise HTTPException(status_code=400, detail="Change request already reviewed")
        updated = self.q.update_change_request(
            request_id, status="rejected", reviewed_by=admin_id, admin_note=admin_note
        )
        try:
            from ..db.queries.activity_query import NotificationQuery
            NotificationQuery().create(
                recipient_user_id=str(cr.user_id),
                type="change_request_rejected",
                title="Your profile change request was rejected",
                body=admin_note or "Your profile change request was not approved.",
                ref_id=request_id,
                ref_type="change_request",
            )
        except Exception:
            logger.exception("Failed to notify member of change request rejection %s", request_id)
        AuditService().log(
            actor_id=admin_id, actor_type="admin",
            action="change_request_rejected",
            entity_type="change_request", entity_id=request_id,
        )
        return updated

    def list_family(self, user_id: str) -> List[FamilyMember]:
        return self.q.list_family(user_id)

    def add_family_member(self, user_id: str, data: FamilyMemberCreate) -> FamilyMember:
        # Enforce plan family limit
        enrollments = self.q.list_enrollments(user_id)
        if enrollments:
            plan = self.plan_q.get_by_id(str(enrollments[0].plan_id))
            limit = plan.benefit_family if plan else 999
            current = len(self.q.list_family(user_id))
            if current >= limit:
                raise HTTPException(
                    status_code=400,
                    detail=f"Your plan allows a maximum of {limit} family member(s). "
                           f"You have already added {current}."
                )
        return self.q.create_family_member(user_id, **data.model_dump())

    def _family_policy_count(self, family_member_id: str) -> int:
        from ..db.queries.activity_query import PolicyFamilyQuery
        return len(PolicyFamilyQuery().list_by_family_member(family_member_id))

    def update_family_member(self, user_id: str, member_id: str, data: FamilyMemberUpdate) -> FamilyMember:
        count = self._family_policy_count(member_id)
        if count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"This family member is linked to {count} policy/policies. "
                       f"To change their details, please raise a change request."
            )
        m = self.q.update_family_member(member_id, user_id, **data.model_dump(exclude_none=True))
        if not m:
            raise HTTPException(status_code=404, detail="Family member not found")
        return m

    def delete_family_member(self, user_id: str, member_id: str) -> None:
        count = self._family_policy_count(member_id)
        if count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot remove: this family member is linked to {count} policy/policies. "
                       f"Contact your administrator."
            )
        if not self.q.delete_family_member(member_id, user_id):
            raise HTTPException(status_code=404, detail="Family member not found")

    def create_family_add_request(self, user_id: str, data) -> object:
        """Member requests a NEW family member — admin approval creates the record.
        Members no longer add family members directly (E8, 4th MOM): family data comes
        from AI policy extraction; any manual addition must go through admin review."""
        from .audit_service import AuditService
        fields = data.requested_fields
        if not fields.get("name") or not fields.get("relation"):
            raise HTTPException(status_code=422, detail="Name and Relation are required to request a new family member")
        cr = self.q.create_change_request(
            user_id=user_id,
            requested_fields=fields,
            reason=data.reason,
            entity_type="family_member",
            entity_id=None,
        )
        try:
            from .notification_helper import notify_all_admins
            user = self.user_q.get_user_by_id(user_id)
            notify_all_admins(
                type="change_request",
                title=f"New Family Member Request — {user.name or user.email}",
                body=f"{user.name or user.email} requested to add a new family member: {fields.get('name')}.",
                ref_id=str(cr.id),
                ref_type="change_request",
            )
        except Exception:
            logger.exception("Failed to notify admins of family add request %s", cr.id)
        AuditService().log(
            actor_id=user_id, actor_type="member",
            action="family_add_request_created",
            entity_type="family_member", entity_id=None,
            new_value=fields,
        )
        return cr

    def create_family_change_request(self, user_id: str, family_member_id: str,
                                      data) -> object:
        from .audit_service import AuditService
        fm = self.q.get_family_member(family_member_id, user_id)
        if not fm:
            raise HTTPException(status_code=404, detail="Family member not found")
        cr = self.q.create_change_request(
            user_id=user_id,
            requested_fields=data.requested_fields,
            reason=data.reason,
            entity_type="family_member",
            entity_id=family_member_id,
        )
        AuditService().log(
            actor_id=user_id, actor_type="member",
            action="family_change_request_created",
            entity_type="family_member", entity_id=family_member_id,
            new_value=data.requested_fields,
        )
        return cr

    def list_nominees(self, user_id: str) -> List[Nominee]:
        return self.q.list_nominees(user_id)

    def add_nominee(self, user_id: str, data: NomineeCreate) -> Nominee:
        current = self.q.total_share(user_id)
        if current + data.share_percent > 100:
            raise HTTPException(status_code=422,
                                detail=f"Total share would exceed 100% (current: {current}%)")
        return self.q.create_nominee(user_id, **data.model_dump())

    def update_nominee(self, user_id: str, nominee_id: str, data: NomineeUpdate) -> Nominee:
        kwargs = data.model_dump(exclude_none=True)
        if "share_percent" in kwargs:
            current = self.q.total_share(user_id, exclude_id=nominee_id)
            if current + kwargs["share_percent"] > 100:
                raise HTTPException(status_code=422, detail="Total share would exceed 100%")
        n = self.q.update_nominee(nominee_id, user_id, **kwargs)
        if not n:
            raise HTTPException(status_code=404, detail="Nominee not found")
        return n

    def delete_nominee(self, user_id: str, nominee_id: str) -> None:
        if not self.q.delete_nominee(nominee_id, user_id):
            raise HTTPException(status_code=404, detail="Nominee not found")

    def get_consent(self, user_id: str) -> DpdpConsent:
        c = self.q.get_latest_consent(user_id)
        if not c:
            raise HTTPException(status_code=404, detail="No consent record found")
        return c

    def update_member_by_admin(self, member_id: str, data, admin_id: str, ip: str = None) -> dict:
        from .audit_service import AuditService
        from ..schemas.member import AdminMemberUpdate
        user = self.user_q.get_user_by_id(member_id)
        if not user:
            raise HTTPException(status_code=404, detail="Member not found")

        old_user = {"name": user.name, "mobile_no": user.mobile_no, "is_active": user.is_active}
        profile = self.q.get_profile(member_id)
        old_profile = {
            "gender": profile.gender if profile else None,
            "address_line": profile.address_line if profile else None,
            "address_city": profile.address_city if profile else None,
            "address_state": profile.address_state if profile else None,
            "address_pin": profile.address_pin if profile else None,
            "sale_date": str(profile.sale_date) if profile and profile.sale_date else None,
            "sales_channel": profile.sales_channel if profile else None,
            "branch_code": profile.branch_code if profile else None,
            "salesperson_name": profile.salesperson_name if profile else None,
            "employee_code": profile.employee_code if profile else None,
            "data1": profile.data1 if profile else None,
            "data2": profile.data2 if profile else None,
            "data3": profile.data3 if profile else None,
        }

        if isinstance(data, dict):
            payload = {k: v for k, v in data.items() if v is not None}
        else:
            payload = data.model_dump(exclude_none=True)

        user_fields = {k: v for k, v in payload.items() if k in ("name", "mobile_no", "is_active")}
        profile_fields = {k: v for k, v in payload.items() if k not in ("name", "mobile_no", "is_active")}

        if user_fields:
            self.user_q.update_user(member_id, **user_fields)
        if profile_fields:
            self.q.upsert_profile(member_id, **profile_fields)

        AuditService().log(
            actor_id=admin_id, actor_type="admin",
            action="member_updated",
            entity_type="member", entity_id=member_id,
            old_value={**old_user, **old_profile},
            new_value=payload,
            ip_address=ip,
        )
        u = self.user_q.get_user_by_id(member_id)
        p = self.q.get_profile(member_id)
        return {
            "id": str(u.id), "name": u.name, "email": u.email,
            "mobile_no": u.mobile_no, "is_active": u.is_active,
            "gender": p.gender if p else None,
            "address_line": p.address_line if p else None,
            "address_city": p.address_city if p else None,
            "address_state": p.address_state if p else None,
            "address_pin": p.address_pin if p else None,
            "sale_date": str(p.sale_date) if p and p.sale_date else None,
            "sales_channel": p.sales_channel if p else None,
            "branch_code": p.branch_code if p else None,
            "salesperson_name": p.salesperson_name if p else None,
            "employee_code": p.employee_code if p else None,
            "data1": p.data1 if p else None,
            "data2": p.data2 if p else None,
            "data3": p.data3 if p else None,
        }

    def create_change_request(self, user_id: str, data) -> object:
        from .audit_service import AuditService
        cr = self.q.create_change_request(
            user_id=user_id,
            requested_fields=data.requested_fields,
            reason=data.reason,
        )
        try:
            from .notification_helper import notify_all_admins
            user = self.user_q.get_user_by_id(user_id)
            notify_all_admins(
                type="change_request",
                title=f"Profile Change Request — {user.name or user.email}",
                body=f"{user.name or user.email} requested changes to their profile.",
                ref_id=str(cr.id),
                ref_type="change_request",
            )
        except Exception:
            logger.exception("Failed to notify admins of change request %s", cr.id)
        AuditService().log(
            actor_id=user_id, actor_type="member",
            action="change_request_created",
            entity_type="change_request", entity_id=str(cr.id),
            new_value=data.requested_fields,
        )
        return cr

    def approve_change_request(self, request_id: str, admin_id: str, admin_note: str = None, ip: str = None) -> object:
        from .audit_service import AuditService
        cr = self.q.get_change_request(request_id)
        if not cr:
            raise HTTPException(status_code=404, detail="Change request not found")
        if cr.status != "pending":
            raise HTTPException(status_code=400, detail="Change request already reviewed")

        # Apply changes based on entity type
        if cr.entity_type == "family_member" and not cr.entity_id:
            # New family member request (E8) — create it now that admin approved
            from ..schemas.member import FamilyMemberCreate
            new_fm = self.add_family_member(str(cr.user_id), FamilyMemberCreate(**cr.requested_fields))
            AuditService().log(
                actor_id=admin_id, actor_type="admin",
                action="family_member_added_via_cr",
                entity_type="family_member", entity_id=str(new_fm.id),
                new_value=cr.requested_fields,
                ip_address=ip,
            )
        elif cr.entity_type == "family_member" and cr.entity_id:
            fm = self.q.get_family_member(str(cr.entity_id))
            if fm:
                self.q.update_family_member(
                    str(cr.entity_id), str(cr.user_id),
                    **cr.requested_fields
                )
                AuditService().log(
                    actor_id=admin_id, actor_type="admin",
                    action="family_member_updated_via_cr",
                    entity_type="family_member", entity_id=str(cr.entity_id),
                    old_value={k: getattr(fm, k, None) for k in cr.requested_fields},
                    new_value=cr.requested_fields,
                    ip_address=ip,
                )
        else:
            # Profile change request — existing logic
            from ..schemas.member import AdminMemberUpdate
            update_data = AdminMemberUpdate(**{k: v for k, v in cr.requested_fields.items()})
            self.update_member_by_admin(
                member_id=str(cr.user_id),
                data=update_data,
                admin_id=admin_id,
                ip=ip,
            )
            AuditService().log(
                actor_id=admin_id, actor_type="admin",
                action="change_request_approved",
                entity_type="member", entity_id=str(cr.user_id),
                new_value=cr.requested_fields,
                ip_address=ip,
            )

        self.q.update_change_request(
            request_id, status="approved", reviewed_by=admin_id, admin_note=admin_note
        )
        try:
            from ..db.queries.activity_query import NotificationQuery
            NotificationQuery().create(
                recipient_user_id=str(cr.user_id),
                type="change_request_approved",
                title="Your profile change request was approved",
                body="Your requested changes have been applied.",
                ref_id=request_id,
                ref_type="change_request",
            )
        except Exception:
            logger.exception("Failed to notify member of change request approval %s", request_id)
        return self.q.get_change_request(request_id)

    def reject_change_request(self, request_id: str, admin_id: str, admin_note: str = None) -> object:
        from .audit_service import AuditService
        cr = self.q.get_change_request(request_id)
        if not cr:
            raise HTTPException(status_code=404, detail="Change request not found")
        if cr.status != "pending":
            raise HTTPException(status_code=400, detail="Change request already reviewed")
        updated = self.q.update_change_request(
            request_id, status="rejected", reviewed_by=admin_id, admin_note=admin_note
        )
        try:
            from ..db.queries.activity_query import NotificationQuery
            NotificationQuery().create(
                recipient_user_id=str(cr.user_id),
                type="change_request_rejected",
                title="Your profile change request was rejected",
                body=admin_note or "Your profile change request was not approved.",
                ref_id=request_id,
                ref_type="change_request",
            )
        except Exception:
            logger.exception("Failed to notify member of change request rejection %s", request_id)
        AuditService().log(
            actor_id=admin_id, actor_type="admin",
            action="change_request_rejected",
            entity_type=cr.entity_type, entity_id=str(cr.entity_id or cr.user_id),
            new_value={"admin_note": admin_note},
        )
        return updated

    def record_consent(self, user_id: str, data: ConsentCreate) -> DpdpConsent:
        return self.q.create_consent(
            user_id, consented_at=datetime.now(timezone.utc),
            version=data.version, source=data.source,
        )
