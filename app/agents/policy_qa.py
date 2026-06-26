from typing import Optional
from pydantic import BaseModel
from .base import BaseAgent
from .prompts import POLICY_QA


class QAResponse(BaseModel):
    answer: str
    language: str


class PolicyQAAgent(BaseAgent):
    agent_name = "policy_qa"

    def answer(
        self,
        question: str,
        policy_data: dict,
        membership_status: str,
        membership_end: str,
        language: str = "English",
        member_id: Optional[str] = None,
    ) -> QAResponse:
        prompt = POLICY_QA.format(
            question=question,
            language=language,
            policy_data=policy_data,
            membership_status=membership_status,
            membership_end=membership_end,
        )
        return self._run(
            prompt=prompt,
            response_schema=QAResponse,
            reference_id=member_id,
            reference_type="member",
        )
