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


def run_ai_extraction(policy_id: str, storage_key: str, member_name: str) -> None:
    import os, tempfile, json as _json
    from ..agents import DocumentExtractorAgent, DocValidatorAgent
    from ..db.queries.policy_query import PolicyQuery as PQ
    from ..db.queries.user_query import UserQuery as UQ
    from ..storage import get_storage as _get_storage

    pq = PQ()
    tmp_path = None
    try:
        pdf_bytes = _get_storage().download(storage_key)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            tmp_path = f.name

        extracted = DocumentExtractorAgent().extract(tmp_path, policy_id=policy_id)
        policy = pq.get_by_id(policy_id)
        member = UQ().get_user_by_id(str(policy.user_id)) if policy else None

        validation = DocValidatorAgent().validate(
            extracted=extracted.model_dump(),
            member_name=member.name if member else member_name,
            policy_id=policy_id,
        )

        confidence_pct = int(extracted.confidence * 100)

        all_fields = extracted.model_dump(exclude={"additional_info", "confidence"})
        fields = {k: v for k, v in all_fields.items() if v is not None}
        fields["confidence"] = extracted.confidence
        fields["validation_status"] = validation.status
        fields["validation_reason"] = validation.reason
        fields["name_match"] = validation.name_match

        if extracted.additional_info:
            try:
                fields.update(_json.loads(extracted.additional_info))
            except (ValueError, TypeError):
                pass

        # Determine status based on validation result — need_review is skipped, policies go active directly
        if validation.status == "reject" or not validation.document_type_valid:
            final_status = "rejected"
        else:
            final_status = "active"

        pq.update_ai_result(policy_id, fields, confidence_pct, final_status)
        logger.info("AI extraction complete for policy %s — status: %s", policy_id, final_status)

        # Notify member if document rejected
        if final_status == "rejected" and member:
            pol_no = policy.policy_number or policy_id
            try:
                from .whatsapp_service import WhatsAppService
                if member.mobile_no:
                    WhatsAppService().send_from_db_template(
                        member.mobile_no, "wa_policy_rejected",
                        {
                            "member_name": member.name or "there",
                            "policy_number": pol_no,
                            "reason": validation.reason or "Document does not appear to be a valid insurance policy.",
                        },
                        partner_id=str(policy.partner_id),
                    )
            except Exception:
                logger.warning("Failed to send rejection WhatsApp for policy %s", policy_id)
            try:
                EmailService().send_policy_rejected(
                    member.email, member.name or member.email, pol_no,
                    partner_id=str(policy.partner_id),
                )
            except Exception:
                logger.warning("Failed to send rejection email for policy %s", policy_id)
            try:
                from .notification_helper import notify_all_admins, notify_partner
                member_label = member.name or member.email
                reason = validation.reason or "Document does not appear to be a valid insurance policy."
                notify_all_admins(
                    type="policy_rejected",
                    title=f"Policy Rejected — {pol_no}",
                    body=f"{member_label}'s uploaded document for policy {pol_no} was auto-rejected. Reason: {reason}",
                    ref_id=str(policy_id), ref_type="policy",
                )
                notify_partner(
                    partner_id=str(policy.partner_id),
                    type="policy_rejected",
                    title=f"Policy Rejected — {pol_no}",
                    body=f"{member_label}'s uploaded document for policy {pol_no} was auto-rejected. Reason: {reason}",
                    ref_id=str(policy_id), ref_type="policy",
                )
            except Exception:
                logger.warning("Failed to send rejection admin/partner notification for policy %s", policy_id)

        # Build family member list — prefer structured field, fallback to nominee in additional_info
        family_members = list(extracted.family_members or [])
        if not family_members and extracted.additional_info:
            try:
                extra = _json.loads(extracted.additional_info)
                nominee_name = extra.get("nominee_name") or extra.get("insured_member_2_name")
                nominee_rel = extra.get("nominee_relationship_with_policyholder") or extra.get("insured_member_2_relation")
                if nominee_name and nominee_rel and nominee_rel.upper() not in ("SELF", "PRIMARY"):
                    from ..agents.document_extractor import ExtractedFamilyMember
                    family_members.append(ExtractedFamilyMember(name=nominee_name, relation=nominee_rel))
            except (ValueError, TypeError):
                pass

        # Always include the primary insured as Self so single policies also link
        has_self = any(
            (em.relation or "").strip().lower() in ("self", "primary")
            for em in family_members
        )
        if not has_self and extracted.insured_name:
            from ..agents.document_extractor import ExtractedFamilyMember
            family_members.insert(0, ExtractedFamilyMember(
                name=extracted.insured_name, relation="Self"
            ))

        _sync_family_members(policy.user_id, policy_id, family_members)
        _detect_and_link_renewal(policy, extracted, pq)

    except Exception as exc:
        logger.error("AI extraction failed for policy %s: %s", policy_id, exc)
        try:
            failed_policy = pq.get_by_id(policy_id)
            existing_fields = dict(failed_policy.extracted_fields or {}) if failed_policy else {}
            existing_fields["AI Extraction Status"] = "Failed — could not process document"
            pq.update_ai_result(policy_id, existing_fields, 0, "rejected")
        except Exception:
            logger.error("Failed to mark policy %s as rejected after extraction error", policy_id)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


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


def _normalize_relation(relation: str) -> str:
    mapping = {
        "wife": "Spouse", "husband": "Spouse", "spouse": "Spouse",
        "son": "Son", "boy": "Son",
        "daughter": "Daughter", "girl": "Daughter",
        "father": "Father", "dad": "Father",
        "mother": "Mother", "mom": "Mother",
        "brother": "Brother", "sister": "Sister",
        "self": "Self", "primary": "Self",
    }
    return mapping.get(relation.strip().lower(), relation.title())


def _sync_family_members(user_id, policy_id: str, extracted_members: list) -> None:
    from ..db.queries.member_query import MemberQuery
    from ..db.queries.activity_query import PolicyFamilyQuery
    from datetime import date
    mq = MemberQuery()
    pfq = PolicyFamilyQuery()
    try:
        existing = mq.list_family(str(user_id))
        existing_by_name = {fm.name.strip().lower(): fm for fm in existing}
        existing_self = next((fm for fm in existing if fm.relation == "Self"), None)

        for em in extracted_members:
            name = (em.name or "").strip()
            relation = _normalize_relation(em.relation or "")
            if not name:
                continue

            if relation == "Self":
                # Find or create a Self record for this user
                fm = existing_self or existing_by_name.get(name.lower())
                if not fm:
                    fm = mq.create_family_member(
                        user_id=str(user_id),
                        name=name,
                        relation="Self",
                        gender=em.gender,
                    )
                    existing_self = fm
                    existing_by_name[name.lower()] = fm
                    logger.info("Auto-added Self family member '%s' for user %s", name, user_id)
            else:
                fm = existing_by_name.get(name.lower())
                if not fm:
                    dob = None
                    if em.dob:
                        try:
                            dob = date.fromisoformat(em.dob)
                        except (ValueError, TypeError):
                            pass
                    fm = mq.create_family_member(
                        user_id=str(user_id),
                        name=name,
                        relation=relation,
                        gender=em.gender,
                        dob=dob,
                    )
                    existing_by_name[name.lower()] = fm
                    logger.info("Auto-added family member '%s' (%s) for user %s", name, relation, user_id)

            try:
                pfq.link(policy_id, str(fm.id))
            except ValueError:
                pass  # already linked
    except Exception as exc:
        logger.warning("Failed to sync family members for user %s: %s", user_id, exc)


def _detect_and_link_renewal(policy, extracted, pq) -> None:
    from datetime import date
    try:
        candidate = pq.find_renewal_candidate(
            str(policy.user_id), str(policy.policy_type_id), str(policy.id)
        )
        if not candidate:
            return

        new_start = extracted.start_date
        old_end = candidate.end_date

        confidence = None
        if new_start and old_end:
            try:
                ns = date.fromisoformat(str(new_start)) if isinstance(new_start, str) else new_start
                delta = abs((ns - old_end).days)
                if delta <= 7:
                    confidence = "high"
                elif delta <= 30:
                    confidence = "low"
            except (ValueError, TypeError):
                pass

        if confidence is None:
            return

        mark_renewed = confidence == "high"
        pq.link_renewal(str(policy.id), str(candidate.id), confidence, mark_renewed)
        logger.info(
            "Renewal detected for policy %s — previous: %s, confidence: %s",
            policy.id, candidate.id, confidence,
        )
    except Exception as exc:
        logger.warning("Renewal detection failed for policy %s: %s", policy.id, exc)


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

        # Enforce plan's max policy cap (benefit_slots), scoped to this member+partner enrollment
        from ..db.queries.member_query import MemberQuery
        from ..db.queries.plan_query import PlanQuery
        enrollment = MemberQuery().get_enrollment(user_id, partner_id)
        if enrollment:
            plan = PlanQuery().get_by_id(str(enrollment.plan_id))
            if plan and plan.benefit_slots is not None:
                current_count = len(self.query.list_by_user_partner(user_id, partner_id))
                if current_count >= plan.benefit_slots:
                    unit = "policy" if plan.benefit_slots == 1 else "policies"
                    raise HTTPException(
                        status_code=400,
                        detail=f"Your plan allows a maximum of {plan.benefit_slots} {unit}. "
                               f"You have already added {current_count}."
                    )

        # Validate vehicle owner belongs to this member's own family members
        if data.vehicle_owner_family_member_id:
            owner = MemberQuery().get_family_member(str(data.vehicle_owner_family_member_id), user_id)
            if not owner:
                raise HTTPException(status_code=422, detail="Vehicle owner must be one of this member's family members")

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
            vehicle_number=data.vehicle_number,
            vehicle_type=data.vehicle_type,
            vehicle_owner_family_member_id=str(data.vehicle_owner_family_member_id) if data.vehicle_owner_family_member_id else None,
            storage_key=key,
            file_name=safe_name,
            status="processing",
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

            # Email + WhatsApp notification to member
            if member:
                self.email.send_policy_uploaded_member(
                    member.email, member_label,
                    policy.policy_number, policy_type_name,
                    partner_id=partner_id,
                )
                if member.mobile_no:
                    try:
                        from .whatsapp_service import WhatsAppService
                        WhatsAppService().send_from_db_template(
                            member.mobile_no, "wa_policy_uploaded",
                            {
                                "member_name": member_label,
                                "policy_type": policy_type_name,
                            },
                            partner_id=partner_id,
                        )
                    except Exception:
                        logger.warning("Failed to send WhatsApp upload confirmation to %s", member.mobile_no)

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
                    body=f"{member_label} uploaded a {policy_type_name} policy.",
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
                    title=f"New Policy Upload — {policy.policy_number}",
                    body=f"{member_label} via {partner_name} uploaded a {policy_type_name} policy.",
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
        from ..db.queries.activity_query import PolicyFamilyQuery, PolicyNomineeQuery
        PolicyFamilyQuery().delete_by_policy(policy_id)
        PolicyNomineeQuery().delete_by_policy(policy_id)
        if not self.query.soft_delete(policy_id, user_id):
            raise HTTPException(status_code=404, detail="Policy not found")
