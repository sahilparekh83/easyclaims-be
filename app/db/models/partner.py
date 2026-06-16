import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
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
    status = Column(String, nullable=False, default="Active")
    api_key = Column(String, unique=True, nullable=True)
    api_rate_limit = Column(Integer, nullable=False, default=600)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", foreign_keys=[user_id])

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

    partner = relationship("Partner")
    plan = relationship("MembershipPlan")

    __table_args__ = (
        UniqueConstraint("partner_id", "plan_id", name="uq_partner_plan"),
    )
