import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..configs.common import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.settings = get_settings()

    def send_otp_email(self, to_email: str, otp: str) -> bool:
        subject = "Your EasyClaims Login OTP"
        body = f"""
        <html>
        <body>
            <p>Hello,</p>
            <p>Your one-time password (OTP) for EasyClaims login is:</p>
            <h2 style="letter-spacing: 4px;">{otp}</h2>
            <p>This OTP is valid for {self.settings.OTP_EXPIRE_MINUTES} minutes.</p>
            <p>If you did not request this, please ignore this email.</p>
        </body>
        </html>
        """
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
            logger.info("Email sent to %s", to_email)
            return True
        except Exception as exc:
            logger.exception("Failed to send email to %s: %s", to_email, exc)
            return False
