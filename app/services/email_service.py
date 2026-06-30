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

    def send_from_template(self, to_email: str, slug: str, context: dict) -> bool:
        """Render a template from DB by slug and send it."""
        tpl = self._tq.get_by_slug(slug)
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

    def _send(self, to_email: str, subject: str, html_body: str,
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
            logger.info("Email sent to %s (subject: %s)", to_email, subject)
            return True
        except Exception as exc:
            logger.exception("Failed to send email to %s: %s", to_email, exc)
            return False

    # ── Named methods (delegate to DB templates) ────────────────────────────────

    def send_otp_email(self, to_email: str, otp: str) -> bool:
        return self.send_from_template(to_email, "otp_login", {
            "otp": otp,
            "otp_expire_minutes": self.settings.OTP_EXPIRE_MINUTES,
        })

    def send_welcome_member(self, to_email: str, member_name: str,
                            partner_name: str, login_url: str) -> bool:
        return self.send_from_template(to_email, "welcome_member", {
            "member_name": member_name or to_email,
            "partner_name": partner_name,
            "login_url": login_url,
            "email": to_email,
        })

    def send_policy_uploaded_member(self, to_email: str, member_name: str,
                                    policy_number: str, policy_type: str) -> bool:
        return self.send_from_template(to_email, "policy_uploaded_member", {
            "member_name": member_name,
            "policy_number": policy_number,
            "policy_type": policy_type,
        })

    def send_policy_uploaded_partner(self, to_email: str, partner_name: str,
                                     member_name: str, member_email: str,
                                     policy_number: str, policy_type: str) -> bool:
        return self.send_from_template(to_email, "policy_uploaded_partner", {
            "partner_name": partner_name,
            "member_name": member_name,
            "member_email": member_email,
            "policy_number": policy_number,
            "policy_type": policy_type,
        })

    def send_policy_uploaded_admin(self, to_email: str, member_name: str,
                                   member_email: str, partner_name: str,
                                   policy_number: str, policy_type: str) -> bool:
        return self.send_from_template(to_email, "policy_uploaded_admin", {
            "member_name": member_name,
            "member_email": member_email,
            "partner_name": partner_name,
            "policy_number": policy_number,
            "policy_type": policy_type,
        })

    def send_plan_expiry_warning(self, to_email: str, member_name: str,
                                 plan_name: str, end_date: str, days_left: int) -> bool:
        return self.send_from_template(to_email, "plan_expiry_warning", {
            "member_name": member_name,
            "plan_name": plan_name,
            "end_date": end_date,
            "days_left": days_left,
        })

    def send_plan_expired(self, to_email: str, member_name: str,
                          plan_name: str, end_date: str) -> bool:
        return self.send_from_template(to_email, "plan_expired_member", {
            "member_name": member_name,
            "plan_name": plan_name,
            "end_date": end_date,
        })

    def send_plan_expired_partner(self, to_email: str, partner_name: str,
                                  member_name: str, member_email: str,
                                  plan_name: str, end_date: str) -> bool:
        return self.send_from_template(to_email, "plan_expired_partner", {
            "partner_name": partner_name,
            "member_name": member_name,
            "member_email": member_email,
            "plan_name": plan_name,
            "end_date": end_date,
        })

    def send_policy_expiry_warning(self, to_email: str, member_name: str,
                                    policy_number: str, policy_type: str,
                                    end_date: str, days_left: int) -> bool:
        return self.send_from_template(to_email, "policy_expiry_warning", {
            "member_name": member_name,
            "policy_number": policy_number,
            "policy_type": policy_type,
            "end_date": end_date,
            "days_left": days_left,
        })

    def send_policy_active(self, to_email: str, member_name: str, policy_number: str) -> bool:
        return self.send_from_template(to_email, "policy_active_member", {
            "member_name": member_name,
            "policy_number": policy_number,
        })

    def send_policy_rejected(self, to_email: str, member_name: str, policy_number: str) -> bool:
        return self.send_from_template(to_email, "policy_rejected_member", {
            "member_name": member_name,
            "policy_number": policy_number,
        })

    def send_plan_changed(self, to_email: str, member_name: str,
                          old_plan: str, new_plan: str, changed_by: str) -> bool:
        return self.send_from_template(to_email, "plan_changed", {
            "member_name": member_name,
            "old_plan": old_plan,
            "new_plan": new_plan,
            "changed_by": changed_by,
        })

    def send_from_template_with_attachment(self, to_email: str, slug: str, context: dict,
                                            attachment_bytes: bytes, attachment_filename: str) -> bool:
        tpl = self._tq.get_by_slug(slug)
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

    def send_new_partner_welcome(self, to_email: str, member_name: str,
                                  partner_name: str, login_url: str) -> bool:
        return self.send_from_template(to_email, "welcome_member_new_partner", {
            "member_name": member_name or to_email,
            "partner_name": partner_name,
            "login_url": login_url,
        })

    def send_membership_card(self, to_email: str, member_name: str, member_email: str,
                              partner_name: str, partner_type: str, plan_name: str,
                              plan, login_url: str) -> bool:
        try:
            from .pdf_service import PdfService
            pdf_bytes = PdfService().generate_membership_card_pdf(
                member_name=member_name or to_email,
                member_email=member_email,
                partner_name=partner_name,
                partner_type=partner_type,
                plan_name=plan_name,
                plan=plan,
            )
        except Exception:
            logger.exception("Failed to generate membership card PDF for %s", to_email)
            pdf_bytes = None

        context = {
            "member_name": member_name or to_email,
            "member_email": member_email,
            "partner_name": partner_name,
            "partner_type": partner_type,
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
            )
        return self.send_from_template(to_email, "membership_card", context)
