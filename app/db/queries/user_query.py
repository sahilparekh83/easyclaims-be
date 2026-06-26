import uuid as _uuid
from typing import Optional
from ..models.user import User, OTPLog, AuthSession
from ..session import session_scope
from ...constants import UserType


class UserQuery:
    def get_user_by_email(self, email: str) -> Optional[User]:
        with session_scope() as session:
            user = (
                session.query(User)
                .filter(User.email.ilike(email), User.is_deleted == False)
                .first()
            )
            if user:
                session.expunge(user)
            return user

    def get_user_by_email_any(self, email: str) -> Optional[User]:
        with session_scope() as session:
            user = session.query(User).filter(User.email.ilike(email)).first()
            if user:
                session.expunge(user)
            return user

    def get_user_by_mobile(self, mobile_no: str) -> Optional[User]:
        with session_scope() as session:
            user = (
                session.query(User)
                .filter(User.mobile_no == mobile_no, User.is_deleted == False)
                .first()
            )
            if user:
                session.expunge(user)
            return user

    def get_customer_by_mobile(self, mobile_no: str) -> Optional[User]:
        with session_scope() as session:
            user = (
                session.query(User)
                .filter(
                    User.mobile_no == mobile_no,
                    User.user_type == UserType.CUSTOMER,
                    User.is_deleted == False,
                )
                .first()
            )
            if user:
                session.expunge(user)
            return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        with session_scope() as session:
            user = (
                session.query(User)
                .filter(User.id == _uuid.UUID(str(user_id)), User.is_deleted == False)
                .first()
            )
            if user:
                session.expunge(user)
            return user

    def list_users(self, skip: int = 0, limit: int = 100):
        with session_scope() as session:
            users = (
                session.query(User)
                .filter(User.is_deleted == False)
                .offset(skip)
                .limit(limit)
                .all()
            )
            for u in users:
                session.expunge(u)
            return users

    def create_user(self, email: str, name: str, user_type: str, mobile_no: str = None) -> User:
        with session_scope() as session:
            user = User(email=email.lower(), name=name, user_type=user_type, mobile_no=mobile_no)
            session.add(user)
            session.flush()
            session.expunge(user)
            return user

    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        with session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            for key, value in kwargs.items():
                setattr(user, key, value)
            session.flush()
            session.expunge(user)
            return user

    def soft_delete_user(self, user_id: str) -> bool:
        with session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            user.is_deleted = True
            user.is_active = False
            return True

    def create_otp_log(self, user_id: str, email: str, otp_code: str, expires_at) -> OTPLog:
        with session_scope() as session:
            otp = OTPLog(
                user_id=user_id,
                email=email.lower(),
                otp_code=otp_code,
                expires_at=expires_at,
            )
            session.add(otp)
            session.flush()
            session.expunge(otp)
            return otp

    def get_latest_valid_otp(self, email: str) -> Optional[OTPLog]:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        with session_scope() as session:
            otp = (
                session.query(OTPLog)
                .filter(
                    OTPLog.email == email.lower(),
                    OTPLog.is_used == False,
                    OTPLog.expires_at > now,
                )
                .order_by(OTPLog.created_at.desc())
                .first()
            )
            if otp:
                session.expunge(otp)
            return otp

    def update_otp_log(self, otp_id: str, **kwargs) -> None:
        with session_scope() as session:
            otp = session.query(OTPLog).filter(OTPLog.id == otp_id).first()
            if otp:
                for key, value in kwargs.items():
                    setattr(otp, key, value)

    def create_auth_session(self, user_id: str, jti: str, expires_at) -> AuthSession:
        with session_scope() as session:
            auth_session = AuthSession(user_id=str(user_id), jti=jti, expires_at=expires_at)
            session.add(auth_session)
            session.flush()
            session.expunge(auth_session)
            return auth_session

    def get_auth_session_by_jti(self, jti: str) -> Optional[AuthSession]:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        with session_scope() as session:
            auth_session = (
                session.query(AuthSession)
                .filter(AuthSession.jti == jti, AuthSession.expires_at > now)
                .first()
            )
            if auth_session:
                session.expunge(auth_session)
            return auth_session

    def delete_auth_session_by_jti(self, jti: str) -> None:
        with session_scope() as session:
            session.query(AuthSession).filter(AuthSession.jti == jti).delete()

    def update_auth_session_jti(self, old_jti: str, new_jti: str, expires_at) -> None:
        with session_scope() as session:
            auth_session = session.query(AuthSession).filter(AuthSession.jti == old_jti).first()
            if auth_session:
                auth_session.jti = new_jti
                auth_session.expires_at = expires_at
