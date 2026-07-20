from typing import Optional, List
from pydantic import BaseModel
from .base import BaseAgent
from .prompts import DOCUMENT_EXTRACTOR


class ExtractedFamilyMember(BaseModel):
    name: str
    relation: str
    dob: Optional[str] = None
    gender: Optional[str] = None


class ExtractedPolicy(BaseModel):
    policy_number: Optional[str] = None
    insured_name: Optional[str] = None
    insurer_name: Optional[str] = None
    sum_insured: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    confidence: float = 0.0
    policy_category: Optional[str] = None  # AI-guessed PolicyType code — resolved in policy_service
    additional_info: Optional[str] = None  # JSON string — parsed after extraction
    family_members: Optional[List[ExtractedFamilyMember]] = None


class DocumentExtractorAgent(BaseAgent):
    agent_name = "document_extractor"

    def extract(self, pdf_path: str, policy_id: Optional[str] = None,
                active_types: Optional[list] = None) -> ExtractedPolicy:
        uploaded = self.client.files.upload(file=pdf_path, config={"mime_type": "application/pdf"})
        allowed = ", ".join(f"{t.name} ({t.code})" for t in (active_types or []))
        prompt = DOCUMENT_EXTRACTOR.format(allowed_categories=allowed or "Other Insurance (other_insurance)")
        return self._run(
            prompt=prompt,
            response_schema=ExtractedPolicy,
            files=[uploaded],
            reference_id=policy_id,
            reference_type="policy",
        )
