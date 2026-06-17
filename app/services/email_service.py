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

    def _send(self, to_email: str, subject: str, html_body: str) -> bool:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.settings.SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))
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

    def send_plan_changed(self, to_email: str, member_name: str,
                          old_plan: str, new_plan: str, changed_by: str) -> bool:
        return self.send_from_template(to_email, "plan_changed", {
            "member_name": member_name,
            "old_plan": old_plan,
            "new_plan": new_plan,
            "changed_by": changed_by,
        })
