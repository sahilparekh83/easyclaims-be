from typing import Optional
from pydantic import BaseModel


class PolicyCreate(BaseModel):
    policy_type: str
    insurer: Optional[str] = None
    sum_insured: Optional[int] = None
