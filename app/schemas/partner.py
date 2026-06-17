from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re

_MOBILE_RE = re.compile(r"^\+?[\d\s\-()]{7,15}$")


class PartnerCreate(BaseModel):
    name: str
    partner_type: str = "Broker"
    city: Optional[str] = None
    email: EmailStr
    mobile_no: Optional[str] = None

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile(cls, v):
        if v and not _MOBILE_RE.match(v):
            raise ValueError("Invalid mobile number format")
        return v


class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    partner_type: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None
    api_rate_limit: Optional[int] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v and v not in ("Active", "Inactive", "Suspended"):
            raise ValueError("Status must be Active, Inactive, or Suspended")
        return v
