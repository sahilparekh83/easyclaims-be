import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number = Column(String, unique=True, nullable=True)  # e.g. 'TCK-2026-000042'
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=True)
    channel = Column(String, nullable=False)          # "Portal" | "WhatsApp" | "Email"
    category = Column(String, nullable=False)         # "claim" | "query" | "correction" | "renewal"
    priority = Column(String, nullable=False, default="medium")  # "high" | "medium" | "low"
    status = Column(String, nullable=False, default="open")      # "open" | "in_progress" | "resolved"
    summary = Column(Text, nullable=True)
    ref_policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=True)
    is_duplicate = Column(Boolean, nullable=False, default=False)
    duplicate_of_ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "open")
        kwargs.setdefault("priority", "medium")
        kwargs.setdefault("is_duplicate", False)
        super().__init__(**kwargs)
