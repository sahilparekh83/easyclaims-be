import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, Enum as SAEnum, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..base import Base
from ...constants import UserType


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    mobile_no = Column(String, nullable=True)
    user_type = Column(SAEnum(UserType), nullable=False)
    member_code = Column(String, unique=True, nullable=True)  # set for CUSTOMER-type users, e.g. 'MEM-2026-000042'
    agent_code = Column(String, unique=True, nullable=True)   # set when the CLAIMS_AGENT role is granted, e.g. 'AGT-2026-000042'
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)

    roles = relationship("UserRole", foreign_keys="UserRole.user_id", back_populates="user", lazy="joined")
    otp_logs = relationship("OTPLog", back_populates="user")


class OTPLog(Base):
    __tablename__ = "otp_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email = Column(String, nullable=False, index=True)
    otp_code = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="otp_logs")

    def __init__(self, **kwargs):
        kwargs.setdefault("is_used", False)
        kwargs.setdefault("attempts", 0)
        super().__init__(**kwargs)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    jti = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
