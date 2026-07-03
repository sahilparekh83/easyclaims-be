from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class PolicyCreate(BaseModel):
    policy_type_id: UUID
    insurer: Optional[str] = None
    sum_insured: Optional[int] = None
    # Motor policy fields (only relevant when policy_type is Motor)
    vehicle_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_owner_family_member_id: Optional[UUID] = None
