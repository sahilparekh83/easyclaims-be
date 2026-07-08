import base64
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, Undefined
from ..configs.common import get_settings
from ..db.queries.email_template_query import EmailTemplateQuery

logger = logging.getLogger(__name__)

_jinja_env = Environment(undefined=Undefined)


class EmailService:
    def __init__(self):
        self.settings = get_settings()
        self._tq = EmailTemplateQuery()

    # ── Core rendering + send ───────────────────────────────────────────────────

    def send_from_template(self, to_email: str, slug: str, context: dict, partner_id: str = None) -> bool:
        """Render a template from DB by slug and send it. If partner_id is given and that
        partner has an active override for this slug, it's used instead of the system
        default (E6, 4th MOM: partner-specific template > system default)."""
        tpl = self._tq.get_for_partner(slug, partner_id)
        if not tpl:
            logger.error("Email template '%s' not found in DB — skipping send", slug)
            return False
        try:
            subject = _jinja_env.from_string(tpl.subject).render(**context)
            body = _jinja_env.from_string(tpl.html_body).render(**context)
        except Exception as exc:
            logger.exception("Failed to render email template '%s': %s", slug, exc)
            return False
        return self._send(to_email, subject, body)

    def send_from_template_with_attachment(self, to_email: str, slug: str, context: dict,
                                            attachment_bytes: bytes, attachment_filename: str,
                                            partner_id: str = None) -> bool:
        tpl = self._tq.get_for_partner(slug, partner_id)
        if not tpl:
            logger.error("Email template '%s' not found — skipping send", slug)
            return False
        try:
            subject = _jinja_env.from_string(tpl.subject).render(**context)
            body = _jinja_env.from_string(tpl.html_body).render(**context)
        except Exception as exc:
            logger.exception("Failed to render template '%s': %s", slug, exc)
            return False
        return self._send(to_email, subject, body,
                          attachment_bytes=attachment_bytes,
                          attachment_filename=attachment_filename)

    def _send(self, to_email: str, subject: str, html_body: str,
              attachment_bytes: bytes = None, attachment_filename: str = None) -> bool:
        if self.settings.EMAIL_PROVIDER == "gmail":
            return self._send_via_smtp(to_email, subject, html_body,
                                       attachment_bytes, attachment_filename)
        return self._send_via_resend(to_email, subject, html_body,
                                     attachment_bytes, attachment_filename)

    def _send_via_resend(self, to_email: str, subject: str, html_body: str,
                         attachment_bytes: bytes = None, attachment_filename: str = None) -> bool:
        import resend
        resend.api_key = self.settings.RESEND_API_KEY
        params: dict = {
            "from": self.settings.RESEND_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }
        if attachment_bytes and attachment_filename:
            params["attachments"] = [{
                "filename": attachment_filename,
                "content": list(attachment_bytes),
            }]
        try:
            resend.Emails.send(params)
            logger.info("Email sent via Resend to %s (subject: %s)", to_email, subject)
            return True
        except Exception as exc:
            logger.exception("Failed to send email via Resend to %s: %s", to_email, exc)
            return False

    def _send_via_smtp(self, to_email: str, subject: str, html_body: str,
                       attachment_bytes: bytes = None, attachment_filename: str = None) -> bool:
        from email.mime.application import MIMEApplication
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = self.settings.SMTP_FROM_EMAIL
        msg["To"] = to_email
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(html_body, "html"))
        msg.attach(alt)
        if attachment_bytes and attachment_filename:
            part = MIMEApplication(attachment_bytes, _subtype="pdf")
            part.add_header("Content-Disposition", "attachment", filename=attachment_filename)
            msg.attach(part)
        try:
            with smtplib.SMTP(self.settings.SMTP_HOST, self.settings.SMTP_PORT) as server:
                if self.settings.SMTP_TLS:
                    server.starttls()
                server.login(self.settings.SMTP_USER, self.settings.SMTP_PASSWORD)
                server.sendmail(self.settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
            logger.info("Email sent via SMTP to %s (subject: %s)", to_email, subject)
            return True
        except Exception as exc:
            logger.exception("Failed to send email to %s: %s", to_email, exc)
            return False

    # ── Named methods (delegate to DB templates) ────────────────────────────────
    # All accept an optional partner_id so a partner's own template override (E6)
    # is used automatically when one exists; falls back to the system default otherwise.

    def send_otp_email(self, to_email: str, otp: str, partner_id: str = None) -> bool:
        return self.send_from_template(to_email, "otp_login", {
            "otp": otp,
            "otp_expire_minutes": self.settings.OTP_EXPIRE_MINUTES,
        }, partner_id=partner_id)

    def send_welcome_member(self, to_email: str, member_name: str,
                            partner_name: str, login_url: str, partner_id: str = None) -> bool:
        return self.send_from_template(to_email, "welcome_member", {
            "member_name": member_name or to_email,
            "partner_name": partner_name,
            "login_url": login_url,
            "email": to_email,
        }, partner_id=partner_id)

    def send_policy_uploaded_member(self, to_email: str, member_name: str,
                                    policy_number: str, policy_type: str, partner_id: str = None) -> bool:
        return self.send_from_template(to_email, "policy_uploaded_member", {
            "member_name": member_name,
            "policy_number": policy_number,
            "policy_type": policy_type,
        }, partner_id=partner_id)

    def send_policy_uploaded_partner(self, to_email: str, partner_name: str,
                                     member_name: str, member_email: str,
                                     policy_number: str, policy_type: str) -> bool:
        # Partner-facing internal notification — no template override (E6 is for member-facing branding).
        return self.send_from_template(to_email, "policy_uploaded_partner", {
            "partner_name": partner_name,
            "member_name": member_name,
            "member_email": member_email,
            "policy_number": policy_number,
            "policy_type": policy_type,
        }, partner_id=partner_id)

    def send_policy_uploaded_admin(self, to_email: str, member_name: str,
                                   member_email: str, partner_name: str,
                                   policy_number: str, policy_type: str) -> bool:
        # Admin-facing — always the system default, no partner override applies.
        return self.send_from_template(to_email, "policy_uploaded_admin", {
            "member_name": member_name,
            "member_email": member_email,
            "partner_name": partner_name,
            "policy_number": policy_number,
            "policy_type": policy_type,
        })

    def send_plan_expiry_warning(self, to_email: str, member_name: str,
                                 plan_name: str, end_date: str, days_left: int, partner_id: str = None) -> bool:
        return self.send_from_template(to_email, "plan_expiry_warning", {
            "member_name": member_name,
            "plan_name": plan_name,
            "end_date": end_date,
            "days_left": days_left,
        }, partner_id=partner_id)

    def send_plan_expired(self, to_email: str, member_name: str,
                          plan_name: str, end_date: str, partner_id: str = None) -> bool:
        return self.send_from_template(to_email, "plan_expired_member", {
            "member_name": member_name,
            "plan_name": plan_name,
            "end_date": end_date,
        }, partner_id=partner_id)

    def send_plan_expired_partner(self, to_email: str, partner_name: str,
                                  member_name: str, member_email: str,
                                  plan_name: str, end_date: str, partner_id: str = None) -> bool:
        return self.send_from_template(to_email, "plan_expired_partner", {
            "partner_name": partner_name,
            "member_name": member_name,
            "member_email": member_email,
            "plan_name": plan_name,
            "end_date": end_date,
        }, partner_id=partner_id)

    def send_policy_expiry_warning(self, to_email: str, member_name: str,
                                    policy_number: str, policy_type: str,
                                    end_date: str, days_left: int, partner_id: str = None) -> bool:
        return self.send_from_template(to_email, "policy_expiry_warning", {
            "member_name": member_name,
            "policy_number": policy_number,
            "policy_type": policy_type,
            "end_date": end_date,
            "days_left": days_left,
        }, partner_id=partner_id)

    def send_policy_active(self, to_email: str, member_name: str, policy_number: str, partner_id: str = None) -> bool:
        return self.send_from_template(to_email, "policy_active_member", {
            "member_name": member_name,
            "policy_number": policy_number,
        }, partner_id=partner_id)

    def send_policy_rejected(self, to_email: str, member_name: str, policy_number: str, partner_id: str = None) -> bool:
        return self.send_from_template(to_email, "policy_rejected_member", {
            "member_name": member_name,
            "policy_number": policy_number,
        }, partner_id=partner_id)

    def send_plan_changed(self, to_email: str, member_name: str,
                          old_plan: str, new_plan: str, changed_by: str, partner_id: str = None) -> bool:
        return self.send_from_template(to_email, "plan_changed", {
            "member_name": member_name,
            "old_plan": old_plan,
            "new_plan": new_plan,
            "changed_by": changed_by,
        }, partner_id=partner_id)

    def send_membership_cancelled(self, to_email: str, member_name: str,
                                  plan_name: str, reason: str = None, partner_id: str = None) -> bool:
        return self.send_from_template(to_email, "membership_cancelled", {
            "member_name": member_name,
            "plan_name": plan_name,
            "reason": reason or "Not specified",
        }, partner_id=partner_id)

    def send_new_partner_welcome(self, to_email: str, member_name: str,
                                  partner_name: str, login_url: str, partner_id: str = None) -> bool:
        return self.send_from_template(to_email, "welcome_member_new_partner", {
            "member_name": member_name or to_email,
            "partner_name": partner_name,
            "login_url": login_url,
        }, partner_id=partner_id)

    def send_ticket_raised(self, to_email: str, member_name: str,
                           ticket_id: str, summary: str, channel: str,
                           partner_id: str = None) -> bool:
        return self.send_from_template(to_email, "ticket_raised", {
            "member_name": member_name or to_email,
            "ticket_id": ticket_id,
            "summary": summary,
            "channel": channel,
        }, partner_id=partner_id)

    def send_membership_card(self, to_email: str, member_name: str, member_email: str,
                              partner_name: str, partner_type: str, plan_name: str,
                              plan, login_url: str,
                              membership_number: str = None, start_date: str = None,
                              end_date: str = None, partner_address: str = None,
                              card_logo_key: str = None, card_color: str = None,
                              partner_id: str = None) -> bool:
        try:
            from .pdf_service import PdfService
            logo_bytes = None
            if card_logo_key:
                try:
                    from ..storage import get_storage
                    logo_bytes = get_storage().download(card_logo_key)
                except Exception:
                    logger.warning("Failed to fetch partner card logo '%s' — using default branding", card_logo_key)
            pdf_bytes = PdfService().generate_membership_card_pdf(
                member_name=member_name or to_email,
                member_email=member_email,
                partner_name=partner_name,
                partner_type=partner_type,
                plan_name=plan_name,
                plan=plan,
                membership_number=membership_number,
                start_date=start_date,
                end_date=end_date,
                partner_address=partner_address,
                partner_logo_bytes=logo_bytes,
                partner_color=card_color,
            )
        except Exception:
            logger.exception("Failed to generate membership card PDF for %s", to_email)
            pdf_bytes = None

        context = {
            "member_name": member_name or to_email,
            "member_email": member_email,
            "partner_name": partner_name,
            "partner_type": partner_type,
            "partner_address": partner_address,
            "membership_number": membership_number,
            "start_date": start_date,
            "end_date": end_date,
            "plan_name": plan_name,
            "benefit_family": plan.benefit_family,
            "benefit_slots": plan.benefit_slots,
            "benefit_claim": plan.benefit_claim,
            "benefit_aiqa": plan.benefit_aiqa,
            "benefit_teleconsult": plan.benefit_teleconsult_sessions,
            "benefit_hospital_cash": plan.benefit_hospital_cash,
            "benefit_wellness": plan.benefit_wellness_sessions,
            "benefit_emergency_assist": plan.benefit_emergency_assist,
            "login_url": login_url,
        }

        if pdf_bytes:
            return self.send_from_template_with_attachment(
                to_email, "membership_card", context,
                attachment_bytes=pdf_bytes,
                attachment_filename="easyclaims_membership_card.pdf",
                partner_id=partner_id,
            )
        return self.send_from_template(to_email, "membership_card", context, partner_id=partner_id)
