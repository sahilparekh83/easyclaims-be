import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base


def utcnow():
    return datetime.now(timezone.utc)


class LLMUsage(Base):
    __tablename__ = "llm_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Float, nullable=False, default=0.0)
    reference_id = Column(String, nullable=True)   # policy_id / member_id / ticket_id etc.
    reference_type = Column(String, nullable=True)  # "policy" | "ticket" | "claim" etc.
    created_at = Column(DateTime(timezone=True), default=utcnow)

    def __init__(self, **kwargs):
        kwargs.setdefault("input_tokens", 0)
        kwargs.setdefault("output_tokens", 0)
        kwargs.setdefault("total_tokens", 0)
        kwargs.setdefault("cost_usd", 0.0)
        super().__init__(**kwargs)
