import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class Partner(Base):
    __tablename__ = "partners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    partner_type = Column(String, nullable=False, default="Broker")
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    # New onboarding fields
    legal_company_name = Column(String, nullable=True)
    trade_name = Column(String, nullable=True)
    registered_address = Column(Text, nullable=True)
    pin_code = Column(String(10), nullable=True)
    gstin = Column(String(15), nullable=True)
    pan = Column(String(10), nullable=True)
    authorized_signatory_name = Column(String, nullable=True)
    designation = Column(String, nullable=True)
    data_1 = Column(String, nullable=True)
    data_2 = Column(String, nullable=True)
    data_3 = Column(String, nullable=True)
    # Existing fields
    status = Column(String, nullable=False, default="Active")
    api_key = Column(String, unique=True, nullable=True)
    api_rate_limit = Column(Integer, nullable=False, default=600)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "Active")
        kwargs.setdefault("api_rate_limit", 600)
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)


class PartnerPlan(Base):
    __tablename__ = "partner_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("membership_plans.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        UniqueConstraint("partner_id", "plan_id", name="uq_partner_plan"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class PartnerChangeRequest(Base):
    __tablename__ = "partner_change_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    requested_fields = Column(JSONB, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending | approved | rejected
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "pending")
        super().__init__(**kwargs)
