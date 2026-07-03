import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String, nullable=False, index=True)
    # NULL = system default template for this slug. Set = partner-specific override
    # (E6, 4th MOM): if a partner has an active override for a slug, it takes priority
    # over the system default.
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=True)
    channel_type = Column(String, nullable=False, server_default="email")
    description = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    html_body = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
