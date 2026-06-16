from typing import Optional
from pydantic import BaseModel, EmailStr


class PartnerCreate(BaseModel):
    name: str
    partner_type: str = "Broker"
    city: Optional[str] = None
    email: EmailStr
    mobile_no: Optional[str] = None


class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    partner_type: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None
    api_rate_limit: Optional[int] = None
