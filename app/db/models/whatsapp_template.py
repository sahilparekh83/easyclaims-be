import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class WhatsAppTemplate(Base):
    __tablename__ = "whatsapp_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String, nullable=False, index=True)
    # NULL = system default template for this slug. Set = partner-specific override,
    # same pattern as EmailTemplate.partner_id.
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=True)
    # Actual Meta-approved template name — blank until an admin fills it in after
    # the template is created + approved in Meta Business Manager. send_template_from_db
    # no-ops (with a warning log) while this is blank, so nothing breaks pre-approval.
    meta_template_name = Column(String, nullable=True)
    meta_template_language = Column(String, nullable=False, default="en")
    # Informational only (admin-set): pending / approved / rejected.
    meta_template_status = Column(String, nullable=True)
    # None | "image" | "document" — only wa_membership_card needs a document header.
    header_type = Column(String, nullable=True)
    # Ordered variable names, e.g. ["member_name","partner_name","upload_url"] —
    # defines the positional {{1}}, {{2}}... mapping for the approved Meta template body.
    variable_order = Column(JSONB, nullable=False, default=list)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
