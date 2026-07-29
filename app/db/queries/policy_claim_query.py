import uuid as _uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func, or_
from ..models.policy_claim import PolicyClaim, PolicyClaimDocument, ClaimActivityLog
from ..models.user import User
from ..session import session_scope


class PolicyClaimQuery:
    def create(self, **kwargs) -> PolicyClaim:
        with session_scope() as session:
            claim = PolicyClaim(**kwargs)
            session.add(claim)
            session.flush()
            session.expunge(claim)
            return claim

    def get_by_id(self, claim_id: str) -> Optional[PolicyClaim]:
        with session_scope() as session:
            c = session.query(PolicyClaim).filter(
                PolicyClaim.id == _uuid.UUID(str(claim_id)), PolicyClaim.is_deleted == False
            ).first()
            if c:
                session.expunge(c)
            return c

    def get_by_claim_number(self, claim_number: str) -> Optional[PolicyClaim]:
        with session_scope() as session:
            c = session.query(PolicyClaim).filter(PolicyClaim.claim_number == claim_number).first()
            if c:
                session.expunge(c)
            return c

    def count_all(self) -> int:
        with session_scope() as session:
            return session.query(PolicyClaim).filter(PolicyClaim.is_deleted == False).count()

    def count_by_agent_and_status(self, agent_ids: List[str]) -> Dict[str, Dict[str, int]]:
        """Returns {agent_id: {status: count, ...}, ...} for the given agent ids in a
        single grouped query — used for the claim-agents overview/workload page."""
        if not agent_ids:
            return {}
        ids = [_uuid.UUID(str(a)) for a in agent_ids]
        with session_scope() as session:
            rows = (
                session.query(
                    PolicyClaim.assigned_agent_id, PolicyClaim.status, func.count(PolicyClaim.id)
                )
                .filter(PolicyClaim.assigned_agent_id.in_(ids), PolicyClaim.is_deleted == False)
                .group_by(PolicyClaim.assigned_agent_id, PolicyClaim.status)
                .all()
            )
        result: Dict[str, Dict[str, int]] = {str(a): {} for a in agent_ids}
        for agent_id, status, count in rows:
            result.setdefault(str(agent_id), {})[status] = count
        return result

    def list_for_user(self, user_id: str) -> List[PolicyClaim]:
        with session_scope() as session:
            rows = (
                session.query(PolicyClaim)
                .filter(PolicyClaim.user_id == _uuid.UUID(str(user_id)), PolicyClaim.is_deleted == False)
                .order_by(PolicyClaim.created_at.desc())
                .all()
            )
            for r in rows:
                session.expunge(r)
            return rows

    def list_paginated(self, skip: int = 0, limit: int = 50, status: Optional[str] = None,
                       statuses: Optional[List[str]] = None,
                       assigned_agent_id: Optional[str] = None, partner_id: Optional[str] = None,
                       user_id: Optional[str] = None, search: Optional[str] = None,
                       date_from=None, date_to=None) -> Tuple[int, List[PolicyClaim]]:
        with session_scope() as session:
            q = session.query(PolicyClaim).filter(PolicyClaim.is_deleted == False)
            if statuses:
                q = q.filter(PolicyClaim.status.in_(statuses))
            elif status:
                q = q.filter(PolicyClaim.status == status)
            if assigned_agent_id:
                q = q.filter(PolicyClaim.assigned_agent_id == _uuid.UUID(str(assigned_agent_id)))
            if partner_id:
                q = q.filter(PolicyClaim.partner_id == _uuid.UUID(str(partner_id)))
            if user_id:
                q = q.filter(PolicyClaim.user_id == _uuid.UUID(str(user_id)))
            if search:
                q = q.join(User, User.id == PolicyClaim.user_id).filter(or_(
                    PolicyClaim.claim_number.ilike(f"%{search}%"),
                    User.name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.member_code.ilike(f"%{search}%"),
                ))
            if date_from:
                q = q.filter(PolicyClaim.created_at >= date_from)
            if date_to:
                q = q.filter(PolicyClaim.created_at <= date_to)
            total = q.count()
            rows = q.order_by(PolicyClaim.created_at.desc()).offset(skip).limit(limit).all()
            for r in rows:
                session.expunge(r)
            return total, rows

    def update(self, claim_id: str, **kwargs) -> Optional[PolicyClaim]:
        with session_scope() as session:
            c = session.query(PolicyClaim).filter(PolicyClaim.id == claim_id).first()
            if not c:
                return None
            for k, v in kwargs.items():
                setattr(c, k, v)
            session.flush()
            session.expunge(c)
            return c

    # ── Documents ─────────────────────────────────────────────────────────────

    def add_document(self, claim_id: str, doc_type: str, storage_key: str,
                     file_name: str, uploaded_by: str) -> PolicyClaimDocument:
        with session_scope() as session:
            doc = PolicyClaimDocument(
                claim_id=claim_id, doc_type=doc_type, storage_key=storage_key,
                file_name=file_name, uploaded_by=uploaded_by,
            )
            session.add(doc)
            session.flush()
            session.expunge(doc)
            return doc

    def list_documents(self, claim_id: str) -> List[PolicyClaimDocument]:
        with session_scope() as session:
            rows = (
                session.query(PolicyClaimDocument)
                .filter(PolicyClaimDocument.claim_id == claim_id)
                .order_by(PolicyClaimDocument.created_at)
                .all()
            )
            for r in rows:
                session.expunge(r)
            return rows

    def get_document(self, document_id: str) -> Optional[PolicyClaimDocument]:
        with session_scope() as session:
            doc = session.query(PolicyClaimDocument).filter(PolicyClaimDocument.id == document_id).first()
            if doc:
                session.expunge(doc)
            return doc

    # ── Activity log ─────────────────────────────────────────────────────────

    def add_log(self, claim_id: str, message: str, actor_type: str = "system",
               actor_name: str = None, old_status: str = None, new_status: str = None) -> ClaimActivityLog:
        with session_scope() as session:
            log = ClaimActivityLog(
                claim_id=claim_id, message=message, actor_type=actor_type,
                actor_name=actor_name, old_status=old_status, new_status=new_status,
            )
            session.add(log)
            session.flush()
            session.expunge(log)
            return log

    def list_logs(self, claim_id: str) -> List[ClaimActivityLog]:
        with session_scope() as session:
            rows = (
                session.query(ClaimActivityLog)
                .filter(ClaimActivityLog.claim_id == claim_id)
                .order_by(ClaimActivityLog.created_at)
                .all()
            )
            for r in rows:
                session.expunge(r)
            return rows
