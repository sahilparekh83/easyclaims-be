from typing import Optional
from pydantic import BaseModel
from .base import BaseAgent
from .prompts import OUTBOUND_CALLER


class CallScript(BaseModel):
    greeting: str
    body: str
    closing: str
    language: str


class OutboundCallerAgent(BaseAgent):
    agent_name = "outbound_caller"

    def generate_script(
        self,
        call_type: str,
        member_name: str,
        plan_name: str,
        end_date: str,
        language: str = "English",
        member_id: Optional[str] = None,
    ) -> CallScript:
        prompt = OUTBOUND_CALLER.format(
            call_type=call_type,
            member_name=member_name,
            language=language,
            plan_name=plan_name,
            end_date=end_date,
        )
        return self._run(
            prompt=prompt,
            response_schema=CallScript,
            reference_id=member_id,
            reference_type="member",
        )
