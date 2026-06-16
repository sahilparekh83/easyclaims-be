import os
import uuid
from datetime import datetime
from typing import List
from fastapi import HTTPException, UploadFile
from ..db.queries.policy_query import PolicyQuery
from ..db.models.policy import Policy
from ..schemas.policy import PolicyCreate
from ..configs.common import get_settings


def _gen_policy_number() -> str:
    return f"POL-{datetime.now().year}-{str(uuid.uuid4().int)[:6].zfill(6)}"


class PolicyService:
    def __init__(self):
        self.query = PolicyQuery()

    def list_policies(self, user_id: str, partner_id: str) -> List[Policy]:
        return self.query.list_by_user_partner(user_id, partner_id)

    def get_policy(self, user_id: str, policy_id: str) -> Policy:
        p = self.query.get_by_id(policy_id, user_id=user_id)
        if not p:
            raise HTTPException(status_code=404, detail="Policy not found")
        return p

    async def upload_policy(self, user_id: str, partner_id: str,
                            data: PolicyCreate, file: UploadFile) -> Policy:
        settings = get_settings()
        if file.content_type not in ("application/pdf", "application/octet-stream"):
            raise HTTPException(status_code=422, detail="Only PDF files are accepted")
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=422, detail="File exceeds 10MB limit")
        if not contents.startswith(b"%PDF"):
            raise HTTPException(status_code=422, detail="File does not appear to be a valid PDF")
        upload_dir = os.path.join(settings.UPLOAD_DIR, "policies", user_id)
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{uuid.uuid4()}.pdf")
        with open(file_path, "wb") as f:
            f.write(contents)
        return self.query.create(
            user_id=user_id, partner_id=partner_id,
            policy_number=_gen_policy_number(),
            policy_type=data.policy_type, insurer=data.insurer,
            sum_insured=data.sum_insured, file_path=file_path,
        )

    def delete_policy(self, user_id: str, policy_id: str) -> None:
        if not self.query.soft_delete(policy_id, user_id):
            raise HTTPException(status_code=404, detail="Policy not found")
