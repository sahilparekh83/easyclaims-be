import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class MembershipPlan(Base):
    __tablename__ = "membership_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    plan_code = Column(String, nullable=False, unique=True)
    tagline = Column(String, nullable=False, default="")
    info_text = Column(Text, nullable=True)
    price = Column(BigInteger, nullable=False, default=0)
    cycle = Column(String, nullable=False, default="Annual")
    plan_type = Column(String, nullable=False, default="partner")
    status = Column(String, nullable=False, default="Draft")
    color = Column(String, nullable=True, default="var(--blue-500)")
    popular = Column(Boolean, nullable=False, default=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    benefit_family = Column(Integer, nullable=False, default=2)
    benefit_slots = Column(Integer, nullable=False, default=3)
    benefit_claim = Column(String, nullable=False, default="Standard")
    benefit_aiqa = Column(Boolean, nullable=False, default=False)
    benefit_aicalls = Column(Boolean, nullable=False, default=False)
    benefit_voice = Column(String, nullable=False, default="English")
    benefit_vault = Column(Boolean, nullable=False, default=False)
    benefit_rm = Column(Boolean, nullable=False, default=False)
    benefit_concierge = Column(Boolean, nullable=False, default=False)
    benefit_teleconsult_sessions = Column(Integer, nullable=False, default=0)
    benefit_hospital_cash = Column(Boolean, nullable=False, default=False)
    benefit_wellness_sessions = Column(Integer, nullable=False, default=0)
    benefit_emergency_assist = Column(Boolean, nullable=False, default=False)
    benefit_legal_assist = Column(Boolean, nullable=False, default=False)
    max_claim_value = Column(BigInteger, nullable=True)
    # Advanced Assistance Service Fee slabs — [{ "slab": "INR 50,001 – INR 1,00,000", "fee": "INR 5000 + applicable taxes" }, ...]
    fee_slabs = Column(JSONB, nullable=False, default=list)
    # Plan Features — free-form, admin-editable, repeatable lists
    basic_features_note = Column(String, nullable=False, default="")
    basic_features = Column(JSONB, nullable=False, default=list)
    advanced_features_note = Column(String, nullable=False, default="")
    advanced_features = Column(JSONB, nullable=False, default=list)
    co_powered_by_easyclaims = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("plan_type", "partner")
        kwargs.setdefault("status", "Draft")
        kwargs.setdefault("popular", False)
        kwargs.setdefault("is_deleted", False)
        kwargs.setdefault("benefit_family", 2)
        kwargs.setdefault("benefit_slots", 3)
        kwargs.setdefault("benefit_claim", "Standard")
        kwargs.setdefault("benefit_aiqa", False)
        kwargs.setdefault("benefit_aicalls", False)
        kwargs.setdefault("benefit_voice", "English")
        kwargs.setdefault("benefit_vault", False)
        kwargs.setdefault("benefit_rm", False)
        kwargs.setdefault("benefit_concierge", False)
        kwargs.setdefault("benefit_teleconsult_sessions", 0)
        kwargs.setdefault("benefit_hospital_cash", False)
        kwargs.setdefault("benefit_wellness_sessions", 0)
        kwargs.setdefault("benefit_emergency_assist", False)
        kwargs.setdefault("benefit_legal_assist", False)
        kwargs.setdefault("fee_slabs", [])
        kwargs.setdefault("basic_features_note", "")
        kwargs.setdefault("basic_features", [])
        kwargs.setdefault("advanced_features_note", "")
        kwargs.setdefault("advanced_features", [])
        kwargs.setdefault("co_powered_by_easyclaims", True)
        super().__init__(**kwargs)
