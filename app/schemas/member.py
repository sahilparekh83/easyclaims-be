from typing import Optional
from datetime import date
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

_MOBILE_RE = re.compile(r"^\+?[\d\s\-()]{7,15}$")


class MemberCreate(BaseModel):
    email: EmailStr
    name: str
    mobile_no: Optional[str] = None
    partner_id: Optional[str] = None
    plan_id: Optional[str] = None

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile(cls, v):
        if v and not _MOBILE_RE.match(v):
            raise ValueError("Invalid mobile number format")
        return v


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    mobile_no: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    address_line: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_pin: Optional[str] = None
    preferred_language: Optional[str] = None
    channel_email: Optional[bool] = None
    channel_whatsapp: Optional[bool] = None
    channel_voice: Optional[bool] = None

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile(cls, v):
        if v and not _MOBILE_RE.match(v):
            raise ValueError("Invalid mobile number format")
        return v

    @field_validator("address_pin")
    @classmethod
    def validate_pin(cls, v):
        if v and not re.match(r"^\d{6}$", v):
            raise ValueError("PIN code must be 6 digits")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v and v not in ("Male", "Female", "Other"):
            raise ValueError("Gender must be Male, Female, or Other")
        return v


class FamilyMemberCreate(BaseModel):
    name: str
    relation: str
    gender: Optional[str] = None
    dob: Optional[date] = None
    coverage_type: Optional[str] = "Health"

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v and v not in ("Male", "Female", "Other"):
            raise ValueError("Gender must be Male, Female, or Other")
        return v

    @field_validator("coverage_type")
    @classmethod
    def default_coverage(cls, v):
        return v or "Health"


class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    relation: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    coverage_type: Optional[str] = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v and v not in ("Male", "Female", "Other"):
            raise ValueError("Gender must be Male, Female, or Other")
        return v

    @field_validator("coverage_type")
    @classmethod
    def default_coverage(cls, v):
        return v or "Health"


class NomineeCreate(BaseModel):
    name: str
    relation: str
    share_percent: int = Field(..., ge=0, le=100)


class NomineeUpdate(BaseModel):
    name: Optional[str] = None
    relation: Optional[str] = None
    share_percent: Optional[int] = Field(default=None, ge=0, le=100)


class ConsentCreate(BaseModel):
    version: str
    source: str = "portal"


class PlanSwitchRequest(BaseModel):
    plan_id: str
