from typing import Optional
from datetime import date
from pydantic import BaseModel, EmailStr


class MemberCreate(BaseModel):
    email: EmailStr
    name: str
    mobile_no: Optional[str] = None
    partner_id: str
    plan_id: Optional[str] = None


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


class FamilyMemberCreate(BaseModel):
    name: str
    relation: str
    gender: Optional[str] = None
    dob: Optional[date] = None
    coverage_type: Optional[str] = "Health"


class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    relation: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    coverage_type: Optional[str] = None


class NomineeCreate(BaseModel):
    name: str
    relation: str
    share_percent: int


class NomineeUpdate(BaseModel):
    name: Optional[str] = None
    relation: Optional[str] = None
    share_percent: Optional[int] = None


class ConsentCreate(BaseModel):
    version: str
    source: str = "portal"


class PlanSwitchRequest(BaseModel):
    plan_id: str
