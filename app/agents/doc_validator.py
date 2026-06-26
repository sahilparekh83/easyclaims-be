from datetime import date
from typing import Optional
from pydantic import BaseModel
from .base import BaseAgent
from .prompts import DOC_VALIDATOR


class ValidationResult(BaseModel):
    status: str
    reason: Optional[str] = None
    name_match: bool = False
    document_type_valid: bool = False
    not_expired: bool = False


class DocValidatorAgent(BaseAgent):
    agent_name = "doc_validator"

    def validate(
        self,
        extracted: dict,
        member_name: str,
        policy_id: Optional[str] = None,
    ) -> ValidationResult:
        prompt = DOC_VALIDATOR.format(
            extracted=extracted,
            member_name=member_name,
            today=str(date.today()),
        )
        return self._run(
            prompt=prompt,
            response_schema=ValidationResult,
            reference_id=policy_id,
            reference_type="policy",
        )
