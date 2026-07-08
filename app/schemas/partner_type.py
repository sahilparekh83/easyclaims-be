from typing import Optional
from pydantic import BaseModel, field_validator


class PartnerTypeCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

    @field_validator("code")
    @classmethod
    def code_lowercase(cls, v: str) -> str:
        return v.strip().lower().replace(" ", "_")

    @field_validator("name")
    @classmethod
    def name_strip(cls, v: str) -> str:
        return v.strip()


class PartnerTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
