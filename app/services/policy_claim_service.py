import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException
from ..db.queries.policy_claim_query import PolicyClaimQuery
from ..db.queries.policy_query import PolicyQuery
from ..db.queries.member_query import MemberQuery
from ..db.queries.user_query import UserQuery
from ..db.queries.role_query import RoleQuery
from ..db.queries.system_setting_query import SystemSettingQuery
from ..schemas.policy_claim import ClaimCreate, ClaimStatusUpdate
from ..storage import get_storage
from .email_service import EmailService
from .whatsapp_service import WhatsAppService  # noqa: F401 — kept dormant, see MetaWhatsAppService below
from .meta_whatsapp_service import MetaWhatsAppService
from .notification_helper import notify_all_admins
from ..db.queries.activity_query import NotificationQuery
from ..utils.code_generator import generate_unique_code

logger = logging.getLogger("easyclaims")

_ROUND_ROBIN_KEY = "claim_round_robin_last_agent_id"


class PolicyClaimService:
    def __init__(self):
        self.query = PolicyClaimQuery()
        self.policy_query = PolicyQuery()
        self.member_query = MemberQuery()
        self.user_query = UserQuery()
        self.role_query = RoleQuery()
        self.setting_query = SystemSettingQuery()

    # ── Claim number ─────────────────────────────────────────────────────────

    def _generate_claim_number(self) -> str:
        """Auto-generate a unique claim number, e.g. 'CLM-2026-000042'."""
        return generate_unique_code("CLM", lambda code: bool(self.query.get_by_claim_number(code)))

    # ── Round robin ──────────────────────────────────────────────────────────

    def _next_claims_agent_id(self) -> Optional[str]:
        agent_ids = self.role_query.list_user_ids_with_role_name("CLAIMS_AGENT")
        if not agent_ids:
            return None
        last_id = self.setting_query.get(_ROUND_ROBIN_KEY)
        if last_id in agent_ids:
            idx = agent_ids.index(last_id)
            next_id = agent_ids[(idx + 1) % len(agent_ids)]
        else:
            next_id = agent_ids[0]
        self.setting_query.set(_ROUND_ROBIN_KEY, next_id, description="Round-robin cursor for claim auto-assignment")
        return next_id

    # ── Notifications ────────────────────────────────────────────────────────

    def _notify_agent_assigned(self, claim, agent, member_name: str, policy_number: str) -> None:
        try:
            NotificationQuery().create(
                recipient_user_id=str(agent.id), type="claim_assigned",
                title=f"Claim assigned: {claim.claim_number}",
                body=f"{member_name}'s claim on policy {policy_number} has been assigned to you.",
                ref_id=str(claim.id), ref_type="policy_claim",
            )
        except Exception:
            logger.exception("Failed to create in-app notification for claim agent %s", agent.id)
        context = {
            "agent_name": agent.name or agent.email, "claim_number": claim.claim_number,
            "member_name": member_name, "policy_number": policy_number,
        }
        try:
            EmailService().send_from_template(str(agent.email), "claim_assigned_agent", context)
        except Exception:
            logger.exception("Failed to email claim agent %s", agent.email)
        if agent.mobile_no:
            try:
                # WhatsAppService().send_from_db_template(agent.mobile_no, "wa_claim_assigned_agent", context)  # Twilio — replaced by Meta template send below
                MetaWhatsAppService().send_template_from_db(agent.mobile_no, "wa_claim_assigned_agent", context)
            except Exception:
                logger.exception("Failed to WhatsApp claim agent %s", agent.mobile_no)

    def _notify_member_claim_submitted(self, claim, member, policy_number: str, agent_name: Optional[str]) -> None:
        """Confirms receipt to the member who filed the claim — sent regardless of
        whether an agent could be auto-assigned yet."""
        try:
            NotificationQuery().create(
                recipient_user_id=str(member.id), type="claim_submitted",
                title=f"Claim received: {claim.claim_number}",
                body="We've received your claim and it's now being reviewed.",
                ref_id=str(claim.id), ref_type="policy_claim",
            )
        except Exception:
            logger.exception("Failed to create in-app notification for member %s", member.id)
        context = {
            "member_name": member.name or member.email, "claim_number": claim.claim_number,
            "policy_number": policy_number, "agent_name": agent_name or "",
        }
        try:
            EmailService().send_from_template(str(member.email), "claim_submitted_member", context)
        except Exception:
            logger.exception("Failed to email member %s about claim submission", member.email)

    def _notify_admins_claim_submitted(self, claim, member_name: str, policy_number: str, agent_name: str) -> None:
        notify_all_admins(
            type="claim_submitted",
            title=f"New claim: {claim.claim_number}",
            body=f"{member_name} submitted a claim on policy {policy_number}. Assigned to {agent_name}.",
            ref_id=str(claim.id), ref_type="policy_claim",
        )
        context = {
            "claim_number": claim.claim_number, "member_name": member_name,
            "policy_number": policy_number, "agent_name": agent_name,
        }
        try:
            from ..db.session import session_scope
            from ..db.models.user import User
            from ..constants import UserType
            with session_scope() as session:
                admins = session.query(User).filter(
                    User.user_type == UserType.SUPERADMIN, User.is_active == True, User.is_deleted == False,
                ).all()
                admin_data = [(str(a.email), a.mobile_no, a.name) for a in admins]
            for email, mobile, name in admin_data:
                try:
                    EmailService().send_from_template(email, "claim_submitted_admin", context)
                except Exception:
                    logger.exception("Failed to email admin %s about claim %s", email, claim.claim_number)
                if mobile:
                    try:
                        # WhatsAppService().send_from_db_template(mobile, "wa_claim_submitted_admin", context)  # Twilio — replaced by Meta template send below
                        MetaWhatsAppService().send_template_from_db(mobile, "wa_claim_submitted_admin", context)
                    except Exception:
                        logger.exception("Failed to WhatsApp admin %s about claim %s", mobile, claim.claim_number)
        except Exception:
            logger.exception("Failed to notify admins about claim %s", claim.claim_number)

    def _notify_member_status_changed(self, claim, member, new_status: str, remark: Optional[str]) -> None:
        try:
            NotificationQuery().create(
                recipient_user_id=str(member.id), type="claim_status_changed",
                title=f"Claim {claim.claim_number} — {new_status.title()}",
                body=remark or f"Your claim status is now {new_status}.",
                ref_id=str(claim.id), ref_type="policy_claim",
            )
        except Exception:
            logger.exception("Failed to create in-app notification for member %s", member.id)
        context = {
            "member_name": member.name or member.email, "claim_number": claim.claim_number,
            "new_status": new_status.title(), "remark": remark or "",
        }
        try:
            EmailService().send_from_template(str(member.email), "claim_status_update_member", context)
        except Exception:
            logger.exception("Failed to email member %s about claim status", member.email)
        if member.mobile_no:
            try:
                # WhatsAppService().send_from_db_template(member.mobile_no, "wa_claim_status_update_member", context)  # Twilio — replaced by Meta template send below
                # Meta rejects blank template parameters, so fall back to non-empty text
                # for the WhatsApp send only (email/in-app can stay blank when no remark).
                MetaWhatsAppService().send_template_from_db(
                    member.mobile_no, "wa_claim_status_update_member",
                    {**context, "remark": remark or "No additional remarks."},
                )
            except Exception:
                logger.exception("Failed to WhatsApp member %s about claim status", member.mobile_no)

    # ── Create ───────────────────────────────────────────────────────────────

    def create_claim(self, user_id: str, data: ClaimCreate):
        policy = self.policy_query.get_by_id(data.policy_id, user_id=user_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")

        if data.family_member_id:
            fm = self.member_query.get_family_member(data.family_member_id, user_id=user_id)
            if not fm:
                raise HTTPException(status_code=404, detail="Family member not found")

        member = self.user_query.get_user_by_id(user_id)
        claim_number = self._generate_claim_number()

        claim = self.query.create(
            claim_number=claim_number,
            policy_id=str(policy.id),
            user_id=user_id,
            partner_id=str(policy.partner_id),
            family_member_id=data.family_member_id,
            incident_date=data.incident_date,
            description=data.description,
            claimed_amount=data.claimed_amount,
        )
        self.query.add_log(
            str(claim.id), f"Claim submitted by {member.name or member.email}.",
            actor_type="member", actor_name=member.name or member.email,
            new_status="pending",
        )

        agent_id = self._next_claims_agent_id()
        if agent_id:
            agent = self.user_query.get_user_by_id(agent_id)
            claim = self.query.update(
                str(claim.id), assigned_agent_id=agent_id,
                assigned_at=datetime.now(timezone.utc), status="processing",
            )
            self.query.add_log(
                str(claim.id), f"Auto-assigned to {agent.name or agent.email}. Status changed to Processing.",
                actor_type="system", old_status="pending", new_status="processing",
            )
            self._notify_agent_assigned(claim, agent, member.name or member.email, policy.policy_number or "—")
            self._notify_admins_claim_submitted(claim, member.name or member.email, policy.policy_number or "—",
                                                agent.name or agent.email)
            self._notify_member_claim_submitted(claim, member, policy.policy_number or "—", agent.name or agent.email)
        else:
            self.query.add_log(
                str(claim.id), "No claim agent is configured yet — awaiting manual assignment.",
                actor_type="system",
            )
            notify_all_admins(
                type="claim_needs_assignment",
                title=f"Claim {claim.claim_number} needs an agent",
                body="No CLAIMS_AGENT is configured — please assign this claim manually.",
                ref_id=str(claim.id), ref_type="policy_claim",
            )
            self._notify_member_claim_submitted(claim, member, policy.policy_number or "—", None)
        return claim

    # ── Reads ────────────────────────────────────────────────────────────────

    def list_my_claims(self, user_id: str):
        return self.query.list_for_user(user_id)

    def get_for_member(self, claim_id: str, user_id: str):
        claim = self.query.get_by_id(claim_id)
        if not claim or str(claim.user_id) != str(user_id):
            raise HTTPException(status_code=404, detail="Claim not found")
        return claim

    def get_for_admin(self, claim_id: str, payload: dict):
        claim = self.query.get_by_id(claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        self._assert_agent_can_access(claim, payload)
        return claim

    def _assert_agent_can_access(self, claim, payload: dict) -> None:
        # Any user reaching here already holds claims:view/edit permission (route-gated) —
        # both SUPERADMIN and CLAIMS_AGENT may view/comment/change status on any claim, not
        # just their own assigned queue. Reassignment is separately gated to superadmin only,
        # at the route level (see admin/claims.py::reassign_claim / bulk_assign_claims).
        return

    def list_paginated(self, payload: dict, skip=0, limit=50, status=None, statuses=None, partner_id=None,
                       assigned_agent_id=None, user_id=None, search=None, date_from=None, date_to=None):
        is_superadmin = payload.get("user_type") == "SUPERADMIN" or "SUPERADMIN" in payload.get("roles", [])
        if not is_superadmin:
            assigned_agent_id = payload.get("sub")  # agents only ever see their own queue
        return self.query.list_paginated(
            skip=skip, limit=limit, status=status, statuses=statuses, assigned_agent_id=assigned_agent_id,
            partner_id=partner_id, user_id=user_id, search=search, date_from=date_from, date_to=date_to,
        )

    def search_all_claims(self, search: str, skip: int = 0, limit: int = 50):
        """Cross-agent claim lookup by claim number, member name/email, or member code —
        unlike list_paginated, never scoped to the caller's own assigned queue. Used by the
        "Search Claims" menu, open to both SUPERADMIN and CLAIMS_AGENT."""
        return self.query.list_paginated(skip=skip, limit=limit, search=search)

    def get_agents_overview(self, skip: int = 0, limit: int = 50, active_only: bool = False):
        """CLAIMS_AGENT-role users (active or deactivated account) with their total
        claim count and per-status breakdown — for the claim-agents admin listing."""
        agent_ids = self.role_query.list_user_ids_with_role_name("CLAIMS_AGENT")
        agents = self.user_query.get_users_by_ids(agent_ids)
        if active_only:
            agents = [a for a in agents if a.is_active]
        agents.sort(key=lambda a: (a.name or a.email or "").lower())

        total = len(agents)
        page = agents[skip:skip + limit]
        page_ids = [str(a.id) for a in page]
        counts = self.query.count_by_agent_and_status(page_ids)

        result = []
        for a in page:
            status_counts = counts.get(str(a.id), {})
            result.append({
                "id": str(a.id),
                "name": a.name or a.email,
                "email": a.email,
                "is_active": a.is_active,
                "total_claims": sum(status_counts.values()),
                "status_counts": status_counts,
            })
        return total, result

    def get_agent_overview(self, agent_id: str):
        """Single agent's workload summary — for the Claim Agents detail page header.
        Returns None if the user doesn't exist or doesn't hold the CLAIMS_AGENT role."""
        agent_ids = self.role_query.list_user_ids_with_role_name("CLAIMS_AGENT")
        if str(agent_id) not in [str(a) for a in agent_ids]:
            return None
        user = self.user_query.get_user_by_id(agent_id)
        if not user:
            return None
        status_counts = self.query.count_by_agent_and_status([agent_id]).get(str(agent_id), {})
        return {
            "id": str(user.id),
            "name": user.name or user.email,
            "email": user.email,
            "is_active": user.is_active,
            "total_claims": sum(status_counts.values()),
            "status_counts": status_counts,
        }

    # ── Mutations ────────────────────────────────────────────────────────────

    def update_status(self, claim_id: str, data: ClaimStatusUpdate, payload: dict):
        claim = self.query.get_by_id(claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        self._assert_agent_can_access(claim, payload)

        actor = self.user_query.get_user_by_id(payload.get("sub"))
        old_status = claim.status
        claim = self.query.update(claim_id, status=data.status)
        self.query.add_log(
            claim_id, data.remark or f"Status changed to {data.status.title()}.",
            actor_type="agent", actor_name=actor.name or actor.email if actor else None,
            old_status=old_status, new_status=data.status,
        )
        member = self.user_query.get_user_by_id(str(claim.user_id))
        if member:
            self._notify_member_status_changed(claim, member, data.status, data.remark)
        return claim

    def reassign_agent(self, claim_id: str, new_agent_id: str, payload: dict):
        claim = self.query.get_by_id(claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        new_agent = self.user_query.get_user_by_id(new_agent_id)
        if not new_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        actor = self.user_query.get_user_by_id(payload.get("sub"))
        old_agent = self.user_query.get_user_by_id(str(claim.assigned_agent_id)) if claim.assigned_agent_id else None

        claim = self.query.update(
            claim_id, assigned_agent_id=new_agent_id, assigned_at=datetime.now(timezone.utc),
        )
        self.query.add_log(
            claim_id,
            f"Reassigned from {old_agent.name or old_agent.email if old_agent else 'unassigned'} "
            f"to {new_agent.name or new_agent.email} by {actor.name or actor.email if actor else 'admin'}.",
            actor_type="admin", actor_name=actor.name or actor.email if actor else None,
        )
        member = self.user_query.get_user_by_id(str(claim.user_id))
        policy = self.policy_query.get_by_id(str(claim.policy_id))
        self._notify_agent_assigned(
            claim, new_agent, member.name or member.email if member else "—",
            policy.policy_number if policy else "—",
        )
        return claim

    def bulk_reassign(self, claim_ids: list, new_agent_id: str, payload: dict) -> list:
        """Assign every listed claim to one agent — each gets its own timeline entry
        and its own assignment notification (in-app + email + WhatsApp)."""
        claims = []
        for claim_id in claim_ids:
            try:
                claims.append(self.reassign_agent(claim_id, new_agent_id, payload))
            except HTTPException:
                raise
            except Exception:
                logger.exception("Bulk reassign failed for claim %s", claim_id)
        return claims

    def add_remark(self, claim_id: str, message: str, payload: dict):
        claim = self.query.get_by_id(claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        self._assert_agent_can_access(claim, payload)
        actor = self.user_query.get_user_by_id(payload.get("sub"))
        self.query.add_log(
            claim_id, message, actor_type="agent",
            actor_name=actor.name or actor.email if actor else None,
        )
        return claim

    # ── Documents ────────────────────────────────────────────────────────────

    def add_document(self, claim_id: str, doc_type: str, file_bytes: bytes, file_name: str,
                     uploaded_by: str, actor_label: str):
        claim = self.query.get_by_id(claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        key = f"claims/{claim.partner_id}/{claim.user_id}/{claim.id}/{file_name}"
        get_storage().upload(key, file_bytes, content_type="application/octet-stream")
        doc = self.query.add_document(claim_id, doc_type, key, file_name, uploaded_by)
        self.query.add_log(
            claim_id, f"{actor_label} uploaded a document: {doc_type} ({file_name}).",
            actor_type=uploaded_by,
        )
        return doc

    def get_timeline(self, claim_id: str):
        return self.query.list_logs(claim_id)

    def get_documents(self, claim_id: str):
        return self.query.list_documents(claim_id)
