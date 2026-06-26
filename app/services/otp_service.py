import secrets
import logging
import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Optional
from ..configs.common import get_settings
from ..db.queries.user_query import UserQuery
from ..db.models.user import OTPLog

logger = logging.getLogger(__name__)


class OTPService:
    def __init__(self):
        self.settings = get_settings()
        self.user_query = UserQuery()

    def generate_otp(self) -> str:
        if self.settings.DEBUG:
            return "12345"
        return str(secrets.randbelow(900000) + 100000)

    def hash_otp(self, otp: str) -> str:
        return bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()

    def verify_otp(self, otp: str, hashed: str) -> bool:
        return bcrypt.checkpw(otp.encode(), hashed.encode())

    def create_otp_for_user(self, user_id: str, email: str) -> str:
        raw_otp = self.generate_otp()
        hashed = self.hash_otp(raw_otp)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.settings.OTP_EXPIRE_MINUTES)
        self.user_query.create_otp_log(
            user_id=str(user_id),
            email=email,
            otp_code=hashed,
            expires_at=expires_at,
        )
        return raw_otp

    def validate_otp(self, email: str, otp: str) -> Optional[OTPLog]:
        otp_log = self.user_query.get_latest_valid_otp(email)
        if not otp_log:
            return None

        new_attempts = otp_log.attempts + 1
        if new_attempts >= self.settings.OTP_MAX_ATTEMPTS:
            self.user_query.update_otp_log(str(otp_log.id), is_used=True, attempts=new_attempts)
            return None

        if not self.verify_otp(otp, otp_log.otp_code):
            self.user_query.update_otp_log(str(otp_log.id), attempts=new_attempts)
            return None

        self.user_query.update_otp_log(str(otp_log.id), is_used=True, attempts=new_attempts)
        return otp_log
