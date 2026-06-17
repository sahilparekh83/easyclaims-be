import logging
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, UploadFile
from ..db.queries.policy_query import PolicyQuery
from ..db.queries.policy_type_query import PolicyTypeQuery
from ..db.queries.user_query import UserQuery
from ..db.queries.partner_query import PartnerQuery
from ..db.models.policy import Policy
from ..schemas.policy import PolicyCreate
from ..storage import get_storage
from .email_service import EmailService

logger = logging.getLogger(__name__)


def _dummy_extracted_fields(policy_number: str, policy_type_name: str,
                            insurer: str = None, sum_insured: int = None) -> dict:
    return {
        "Policy Number": policy_number or "N/A",
        "Policy Type": policy_type_name or "N/A",
        "Insurer Name": insurer or "Not detected",
        "Sum Insured": f"₹{int(sum_insured):,}" if sum_insured else "Not detected",
        "Coverage Type": "Individual + Family Floater",
        "Premium Amount": "Not detected",
        "Network Hospitals": "As per insurer network",
        "Claim Type": "Cashless & Reimbursement",
        "Sub-limits": "As per policy schedule",
        "Waiting Period": "30 days general, 2 years for specific conditions",
        "Co-payment": "Not applicable",
        "Room Rent Limit": "Single Private AC Room",
        "Pre-existing Diseases": "Covered after waiting period",
        "Maternity Benefit": "Not detected",
        "AI Extraction Status": "Dummy (AI not configured)",
    }


def _gen_policy_number() -> str:
    return f"POL-{datetime.now().year}-{str(uuid.uuid4().int)[:6].zfill(6)}"


def _storage_key(partner_id: str, user_id: str, policy_id: str, file_name: str) -> str:
    return f"{partner_id}/{user_id}/{policy_id}/{file_name}"


class PolicyService:
    def __init__(self):
        self.query = PolicyQuery()
        self.pt_query = PolicyTypeQuery()
        self.user_query = UserQuery()
        self.partner_query = PartnerQuery()
        self.email = EmailService()
        self.storage = get_storage()

    def list_policies(self, user_id: str, partner_id: str) -> List[Policy]:
        return self.query.list_by_user_partner(user_id, partner_id)

    def list_by_partner(self, partner_id: str, skip: int = 0, limit: int = 100) -> List[Policy]:
        return self.query.list_by_partner(partner_id, skip=skip, limit=limit)

    def list_all(self, partner_id: str = None, skip: int = 0, limit: int = 100) -> List[Policy]:
        return self.query.list_all(partner_id=partner_id, skip=skip, limit=limit)

    def get_policy_admin(self, policy_id: str) -> Policy:
        p = self.query.get_by_id(policy_id)
        if not p:
            raise HTTPException(status_code=404, detail="Policy not found")
        return p

    def get_policy(self, user_id: str, policy_id: str) -> Policy:
        p = self.query.get_by_id(policy_id, user_id=user_id)
        if not p:
            raise HTTPException(status_code=404, detail="Policy not found")
        return p

    def get_policy_type(self, policy_type_id: str) -> Optional[object]:
        return self.pt_query.get_by_id(policy_type_id)

    async def upload_policy(self, user_id: str, partner_id: str,
                            data: PolicyCreate, file: UploadFile) -> Policy:
        # Validate policy type exists and is active
        pt = self.pt_query.get_by_id(str(data.policy_type_id))
        if not pt or not pt.is_active:
            raise HTTPException(status_code=422, detail="Invalid or inactive policy type")

        # Validate file
        if file.content_type not in ("application/pdf", "application/octet-stream"):
            raise HTTPException(status_code=422, detail="Only PDF files are accepted")
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=422, detail="File exceeds 10MB limit")
        if not contents.startswith(b"%PDF"):
            raise HTTPException(status_code=422, detail="File does not appear to be a valid PDF")

        # Pre-generate policy_id so folder structure includes it
        policy_id = str(uuid.uuid4())
        safe_name = f"{uuid.uuid4()}.pdf"
        key = _storage_key(partner_id, user_id, policy_id, safe_name)

        self.storage.upload(key, contents, content_type="application/pdf")

        policy = self.query.create(
            policy_id=policy_id,
            user_id=user_id,
            partner_id=partner_id,
            policy_type_id=str(data.policy_type_id),
            policy_number=_gen_policy_number(),
            insurer=data.insurer,
            sum_insured=data.sum_insured,
            storage_key=key,
            file_name=safe_name,
        )

        # Populate dummy extracted fields until AI extraction is configured
        try:
            dummy_fields = _dummy_extracted_fields(
                policy.policy_number,
                pt.name if pt else "Unknown",
                data.insurer,
                data.sum_insured,
            )
            self.query.update_extracted_fields(str(policy.id), dummy_fields)
            policy.extracted_fields = dummy_fields
        except Exception:
            logger.warning("Failed to set dummy extracted_fields for policy %s", policy.id)

        self._send_upload_notifications(policy, user_id, partner_id, pt)
        return policy

    def _send_upload_notifications(self, policy: Policy, user_id: str,
                                   partner_id: str, pt) -> None:
        try:
            from ..db.queries.activity_query import NotificationQuery
            from ..db.session import session_scope
            from ..db.models.user import User
            from ..constants import UserType

            member = self.user_query.get_user_by_id(user_id)
            partner_record = self.partner_query.get_by_id(partner_id)
            partner_user = (self.user_query.get_user_by_id(str(partner_record.user_id))
                            if partner_record else None)
            policy_type_name = pt.name if pt else "Policy"
            member_label = (member.name or member.email) if member else "Member"
            member_email = member.email if member else ""

            nq = NotificationQuery()

            # Email + notification to member
            if member:
                self.email.send_policy_uploaded_member(
                    member.email, member_label,
                    policy.policy_number, policy_type_name,
                )

            # Email + notification to partner
            if partner_record and partner_user:
                self.email.send_policy_uploaded_partner(
                    partner_user.email, partner_record.name,
                    member_label, member_email,
                    policy.policy_number, policy_type_name,
                )
                nq.create(
                    recipient_user_id=str(partner_record.user_id),
                    type="policy_uploaded",
                    title=f"New Policy Uploaded — {policy.policy_number}",
                    body=f"{member_label} ({member_email}) uploaded a {policy_type_name} policy.",
                    ref_id=str(policy.id),
                    ref_type="policy",
                )

            # Email + notification to all SuperAdmins
            with session_scope() as session:
                admins = session.query(User).filter(
                    User.user_type == UserType.SUPERADMIN,
                    User.is_active == True, User.is_deleted == False,
                ).all()
                for a in admins:
                    session.expunge(a)

            partner_name = partner_record.name if partner_record else "Unknown"
            for admin in admins:
                self.email.send_policy_uploaded_admin(
                    admin.email, member_label, member_email,
                    partner_name, policy.policy_number, policy_type_name,
                )
                nq.create(
                    recipient_user_id=str(admin.id),
                    type="policy_uploaded",
                    title=f"[Admin] New Policy Upload — {policy.policy_number}",
                    body=f"{member_label} ({member_email}) via {partner_name} uploaded a {policy_type_name} policy.",
                    ref_id=str(policy.id),
                    ref_type="policy",
                )
        except Exception:
            logger.exception("Failed to send policy upload notifications for policy %s", policy.id)

    def delete_policy(self, user_id: str, policy_id: str) -> None:
        policy = self.query.get_by_id(policy_id, user_id=user_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        if policy.storage_key:
            try:
                self.storage.delete(policy.storage_key)
            except Exception:
                logger.warning("Failed to delete storage object %s", policy.storage_key)
        if not self.query.soft_delete(policy_id, user_id):
            raise HTTPException(status_code=404, detail="Policy not found")
