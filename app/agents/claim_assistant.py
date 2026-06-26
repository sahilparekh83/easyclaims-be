from typing import Optional, List
from pydantic import BaseModel
from .base import BaseAgent
from .prompts import CLAIM_ASSISTANT


class ClaimResponse(BaseModel):
    incident_summary: str
    required_documents: List[str]
    next_steps: str


class ClaimAssistantAgent(BaseAgent):
    agent_name = "claim_assistant"

    def assist(
        self,
        claim_type: str,
        incident_details: str,
        policy_data: dict,
        language: str = "English",
        member_id: Optional[str] = None,
    ) -> ClaimResponse:
        prompt = CLAIM_ASSISTANT.format(
            claim_type=claim_type,
            incident_details=incident_details,
            policy_data=policy_data,
            language=language,
        )
        return self._run(
            prompt=prompt,
            response_schema=ClaimResponse,
            reference_id=member_id,
            reference_type="member",
        )
