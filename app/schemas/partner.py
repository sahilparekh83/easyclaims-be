from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator
import re

_MOBILE_RE = re.compile(r"^\+?[\d\s\-()]{7,15}$")
_GSTIN_RE  = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
_PAN_RE    = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
_PIN_RE    = re.compile(r"^\d{6}$")


class PartnerCreate(BaseModel):
    # Identity / contact (email+mobile go into User table)
    name: str
    email: EmailStr
    mobile_no: str
    partner_type: str = "Broker"

    # Mandatory onboarding fields
    legal_company_name: str
    trade_name: str
    registered_address: str
    city: str
    state: str
    pin_code: str
    gstin: str
    pan: str
    authorized_signatory_name: str
    designation: str

    # Optional extras
    data_1: Optional[str] = None
    data_2: Optional[str] = None
    data_3: Optional[str] = None
    plan_ids: List[str] = []

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile(cls, v):
        if not v or not _MOBILE_RE.match(v.strip()):
            raise ValueError("Invalid mobile number — must be 7–15 digits, may include +, spaces, hyphens")
        return v.strip()

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v):
        v = v.strip().upper()
        if not _GSTIN_RE.match(v):
            raise ValueError("Invalid GSTIN format — must be 15 characters, e.g. 27AAPFU0939F1ZV")
        return v

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v):
        v = v.strip().upper()
        if not _PAN_RE.match(v):
            raise ValueError("Invalid PAN format — must be 10 characters, e.g. AAPFU0939F")
        return v

    @field_validator("pin_code")
    @classmethod
    def validate_pin_code(cls, v):
        v = str(v).strip()
        if not _PIN_RE.match(v):
            raise ValueError("Invalid pin code — must be exactly 6 digits")
        return v

    @field_validator("partner_type")
    @classmethod
    def validate_partner_type(cls, v):
        allowed = {"Broker", "Corporate", "NGO", "Other"}
        if v not in allowed:
            raise ValueError(f"Partner type must be one of: {', '.join(sorted(allowed))}")
        return v


class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    partner_type: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    status: Optional[str] = None
    allow_member_upload: Optional[bool] = None
    card_color: Optional[str] = None
    api_rate_limit: Optional[int] = None
    legal_company_name: Optional[str] = None
    trade_name: Optional[str] = None
    registered_address: Optional[str] = None
    pin_code: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    authorized_signatory_name: Optional[str] = None
    designation: Optional[str] = None
    mobile_no: Optional[str] = None
    data_1: Optional[str] = None
    data_2: Optional[str] = None
    data_3: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v and v not in ("Active", "Inactive", "Suspended"):
            raise ValueError("Status must be Active, Inactive, or Suspended")
        return v

    @field_validator("card_color")
    @classmethod
    def validate_card_color(cls, v):
        import re
        if v and not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("card_color must be a hex color like #0050b0")
        return v

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v):
        if v is None:
            return v
        v = v.strip().upper()
        if not _GSTIN_RE.match(v):
            raise ValueError("Invalid GSTIN format — must be 15 characters, e.g. 27AAPFU0939F1ZV")
        return v

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v):
        if v is None:
            return v
        v = v.strip().upper()
        if not _PAN_RE.match(v):
            raise ValueError("Invalid PAN format — must be 10 characters, e.g. AAPFU0939F")
        return v

    @field_validator("pin_code")
    @classmethod
    def validate_pin_code(cls, v):
        if v is None:
            return v
        v = str(v).strip()
        if not _PIN_RE.match(v):
            raise ValueError("Invalid pin code — must be exactly 6 digits")
        return v

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile(cls, v):
        if v is None:
            return v
        if not _MOBILE_RE.match(v.strip()):
            raise ValueError("Invalid mobile number — must be 7–15 digits, may include +, spaces, hyphens")
        return v.strip()
