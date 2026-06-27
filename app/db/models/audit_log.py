import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(String, nullable=True)       # user_id performing the action (None = system)
    actor_type = Column(String, nullable=True)     # "admin" | "member" | "partner" | "system"
    action = Column(String, nullable=False)        # "member_created" | "member_updated" | "bulk_upload" | "change_request_approved" etc.
    entity_type = Column(String, nullable=True)    # "member" | "policy" | "change_request"
    entity_id = Column(String, nullable=True)      # UUID of the affected entity
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    ip_address = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
