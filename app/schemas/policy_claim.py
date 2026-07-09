from datetime import date
from typing import List, Optional
from pydantic import BaseModel, field_validator


class ClaimCreate(BaseModel):
    policy_id: str
    family_member_id: Optional[str] = None  # None = claim is for the member themself
    incident_date: Optional[date] = None
    description: Optional[str] = None
    claimed_amount: Optional[int] = None

    @field_validator("claimed_amount")
    @classmethod
    def amount_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("claimed_amount must be greater than 0")
        return v


class ClaimStatusUpdate(BaseModel):
    status: str
    remark: Optional[str] = None

    @field_validator("status")
    @classmethod
    def status_valid(cls, v):
        if v not in ("pending", "processing", "accepted", "rejected"):
            raise ValueError("status must be one of: pending, processing, accepted, rejected")
        return v


class ClaimReassign(BaseModel):
    agent_id: str


class ClaimBulkAssign(BaseModel):
    claim_ids: List[str]
    agent_id: str


class ClaimRemark(BaseModel):
    message: str
