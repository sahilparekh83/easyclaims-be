import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    policy_type_id = Column(UUID(as_uuid=True), ForeignKey("policy_types.id"), nullable=False)
    policy_number = Column(String, nullable=True, unique=True)
    insurer = Column(String, nullable=True)
    sum_insured = Column(BigInteger, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String, nullable=False, default="pending")
    ai_confidence = Column(Integer, nullable=True)
    # storage
    storage_key = Column(String, nullable=True)   # {partner_id}/{user_id}/{policy_id}/{file_name}
    file_name = Column(String, nullable=True)
    extracted_fields = Column(JSONB, nullable=True, default=dict)
    previous_policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=True)
    renewal_confidence = Column(String, nullable=True)  # 'high' | 'low' | None
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "pending")
        kwargs.setdefault("is_deleted", False)
        kwargs.setdefault("extracted_fields", {})
        super().__init__(**kwargs)
