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
    additional_info: Optional[str] = None  # JSON string — parsed after extraction
    family_members: Optional[List[ExtractedFamilyMember]] = None


class DocumentExtractorAgent(BaseAgent):
    agent_name = "document_extractor"

    def extract(self, pdf_path: str, policy_id: Optional[str] = None) -> ExtractedPolicy:
        uploaded = self.client.files.upload(file=pdf_path, config={"mime_type": "application/pdf"})
        return self._run(
            prompt=DOCUMENT_EXTRACTOR,
            response_schema=ExtractedPolicy,
            files=[uploaded],
            reference_id=policy_id,
            reference_type="policy",
        )
