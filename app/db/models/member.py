import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class MemberEnrollment(Base):
    __tablename__ = "member_enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("membership_plans.id"), nullable=False)
    status = Column(String, nullable=False, default="Active")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "partner_id", name="uq_member_partner"),
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "Active")
        super().__init__(**kwargs)


class MemberProfile(Base):
    __tablename__ = "member_profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    gender = Column(String, nullable=True)
    dob = Column(Date, nullable=True)
    address_line = Column(String, nullable=True)
    address_city = Column(String, nullable=True)
    address_state = Column(String, nullable=True)
    address_pin = Column(String, nullable=True)
    preferred_language = Column(String, nullable=False, default="English")
    channel_email = Column(Boolean, nullable=False, default=True)
    channel_whatsapp = Column(Boolean, nullable=False, default=False)
    channel_voice = Column(Boolean, nullable=False, default=False)
    # NEW onboarding fields
    sale_date = Column(Date, nullable=True)
    sales_channel = Column(String, nullable=True)
    branch_code = Column(String, nullable=True)
    salesperson_name = Column(String, nullable=True)
    employee_code = Column(String, nullable=True)
    data1 = Column(String, nullable=True)
    data2 = Column(String, nullable=True)
    data3 = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("preferred_language", "English")
        kwargs.setdefault("channel_email", True)
        kwargs.setdefault("channel_whatsapp", False)
        kwargs.setdefault("channel_voice", False)
        super().__init__(**kwargs)


class MemberChangeRequest(Base):
    __tablename__ = "member_change_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    requested_fields = Column(JSONB, nullable=False)   # {"name": "New Name", "mobile_no": "9999999999"}
    reason = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending | approved | rejected
    reviewed_by = Column(String, nullable=True)        # admin user_id as string
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "pending")
        super().__init__(**kwargs)


class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    relation = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    dob = Column(Date, nullable=True)
    coverage_type = Column(String, nullable=True, default="Health")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("coverage_type", "Health")
        super().__init__(**kwargs)


class Nominee(Base):
    __tablename__ = "nominees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    relation = Column(String, nullable=False)
    share_percent = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class DpdpConsent(Base):
    __tablename__ = "dpdp_consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    consented_at = Column(DateTime(timezone=True), nullable=False)
    version = Column(String, nullable=False)
    source = Column(String, nullable=False, default="portal")
    created_at = Column(DateTime(timezone=True), default=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("source", "portal")
        super().__init__(**kwargs)
