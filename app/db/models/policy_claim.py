import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, BigInteger, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class PolicyClaim(Base):
    __tablename__ = "policy_claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_number = Column(String, nullable=False, unique=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    family_member_id = Column(UUID(as_uuid=True), ForeignKey("family_members.id"), nullable=True)
    incident_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    claimed_amount = Column(BigInteger, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending | processing | accepted | rejected
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "pending")
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)


class PolicyClaimDocument(Base):
    __tablename__ = "policy_claim_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("policy_claims.id"), nullable=False)
    doc_type = Column(String, nullable=False, default="Other")
    storage_key = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    uploaded_by = Column(String, nullable=False, default="member")  # member | agent
    created_at = Column(DateTime(timezone=True), default=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("doc_type", "Other")
        kwargs.setdefault("uploaded_by", "member")
        super().__init__(**kwargs)


class ClaimActivityLog(Base):
    __tablename__ = "claim_activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("policy_claims.id"), nullable=False)
    actor_type = Column(String, nullable=False, default="system")  # member | agent | admin | system
    actor_name = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("actor_type", "system")
        super().__init__(**kwargs)
