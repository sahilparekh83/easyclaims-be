from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class PolicyCreate(BaseModel):
    policy_type_id: UUID
    insurer: Optional[str] = None
    sum_insured: Optional[int] = None
