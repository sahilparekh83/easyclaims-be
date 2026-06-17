import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class EnrollmentHistory(Base):
    """Audit log for all enrollment plan changes, renewals, and expirations."""
    __tablename__ = "enrollment_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("member_enrollments.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    from_plan_id = Column(UUID(as_uuid=True), ForeignKey("membership_plans.id"), nullable=True)
    to_plan_id = Column(UUID(as_uuid=True), ForeignKey("membership_plans.id"), nullable=False)
    # action: created | plan_changed | renewed | expired
    action = Column(String, nullable=False)
    # changed_by: member | partner | admin | system
    changed_by = Column(String, nullable=False, default="system")
    note = Column(String, nullable=True)
    changed_at = Column(DateTime(timezone=True), default=utcnow)
