from typing import Optional
from pydantic import BaseModel, field_validator


class BenefitsSchema(BaseModel):
    family: int = 2
    slots: int = 3
    claim: str = "Standard"
    aiqa: bool = True
    aicalls: bool = False
    voice: str = "English"
    vault: bool = True
    rm: bool = False
    concierge: bool = False
    teleconsult_sessions: int = 0
    hospital_cash: bool = False
    wellness_sessions: int = 0
    emergency_assist: bool = False
    legal_assist: bool = False

    @field_validator("family")
    @classmethod
    def family_range(cls, v):
        if not 1 <= v <= 10:
            raise ValueError("family must be 1-10")
        return v

    @field_validator("slots")
    @classmethod
    def slots_range(cls, v):
        if not 1 <= v <= 20:
            raise ValueError("slots must be 1-20")
        return v

    @field_validator("claim")
    @classmethod
    def claim_valid(cls, v):
        if v not in ("Standard", "Priority", "24x7 Priority"):
            raise ValueError("invalid claim value")
        return v

    @field_validator("voice")
    @classmethod
    def voice_valid(cls, v):
        if v not in ("English", "English + Hindi"):
            raise ValueError("invalid voice value")
        return v


class PlanCreate(BaseModel):
    name: str
    tagline: str = ""
    info_text: Optional[str] = None
    price: int
    cycle: str = "Annual"
    plan_type: str = "global"
    status: str = "Draft"
    color: Optional[str] = "var(--blue-500)"
    popular: bool = False
    max_claim_value: Optional[int] = None
    benefits: BenefitsSchema = BenefitsSchema()

    @field_validator("max_claim_value")
    @classmethod
    def max_claim_value_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("max_claim_value must be greater than 0")
        return v

    @field_validator("cycle")
    @classmethod
    def cycle_valid(cls, v):
        if v not in ("Annual", "Half-yearly", "Quarterly"):
            raise ValueError("invalid cycle")
        return v

    @field_validator("status")
    @classmethod
    def status_valid(cls, v):
        if v not in ("Draft", "Active", "Archived"):
            raise ValueError("invalid status")
        return v

    @field_validator("plan_type")
    @classmethod
    def plan_type_valid(cls, v):
        if v not in ("global", "partner"):
            raise ValueError("plan_type must be 'global' or 'partner'")
        return v


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    tagline: Optional[str] = None
    info_text: Optional[str] = None
    price: Optional[int] = None
    cycle: Optional[str] = None
    plan_type: Optional[str] = None
    status: Optional[str] = None
    color: Optional[str] = None
    popular: Optional[bool] = None
    max_claim_value: Optional[int] = None
    benefits: Optional[BenefitsSchema] = None

    @field_validator("status")
    @classmethod
    def status_valid(cls, v):
        if v is not None and v not in ("Draft", "Active", "Archived"):
            raise ValueError("invalid status")
        return v

    @field_validator("max_claim_value")
    @classmethod
    def max_claim_value_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("max_claim_value must be greater than 0")
        return v
