import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class FloatTransaction(Base):
    """Ledger entry for a partner's prepaid float balance — top-ups and per-enrollment deductions."""
    __tablename__ = "float_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    type = Column(String, nullable=False)          # "top_up" | "deduction"
    amount = Column(BigInteger, nullable=False)     # always positive; `type` gives direction
    balance_after = Column(BigInteger, nullable=False)
    note = Column(Text, nullable=True)
    ref_type = Column(String, nullable=True)        # e.g. "enrollment"
    ref_id = Column(String, nullable=True)
    is_reconciled = Column(Boolean, nullable=False, default=False)
    reconciled_by = Column(String, nullable=True)
    reconciled_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String, nullable=True)      # admin user id for top-ups; None for system deductions
    created_at = Column(DateTime(timezone=True), default=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("is_reconciled", False)
        super().__init__(**kwargs)
