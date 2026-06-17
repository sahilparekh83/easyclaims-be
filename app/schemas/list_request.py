from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field


class FilterOption(BaseModel):
    field: str
    operator: Literal["equals", "notEquals", "contains", "startsWith", "endsWith"] = "equals"
    value: Any


class ListRequest(BaseModel):
    global_filter: str = ""
    sort_field: str = "created_at"
    sort_order: int = Field(default=-1, description="-1 desc, 1 asc")
    filters: List[FilterOption] = []
    limit: int = Field(default=10, ge=1, le=200)
    skip: int = Field(default=0, ge=0)


class PolicyListRequest(ListRequest):
    """Used by admin (optional partner_id / user_id) and partner (scoped internally)."""
    partner_id: Optional[str] = None
    user_id: Optional[str] = None


class MemberListRequest(ListRequest):
    """Used by admin (optional partner_id) and partner (scoped internally)."""
    partner_id: Optional[str] = None


class PartnerListRequest(ListRequest):
    pass
