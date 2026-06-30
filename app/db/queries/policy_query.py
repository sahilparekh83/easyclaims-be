import uuid as _uuid
from typing import Optional, List, Tuple
from sqlalchemy import or_
from ..models.policy import Policy
from ..models.policy_type import PolicyType
from ..session import session_scope
from .list_helper import (
    apply_global_filter, apply_field_filters, apply_sort, paginate
)


# columns searchable via global_filter
_GLOBAL_COLS = lambda: [
    Policy.policy_number, Policy.insurer, Policy.status, Policy.file_name, PolicyType.name
]

# columns addressable by filters[].field
_FILTER_MAP = {
    "policy_number": Policy.policy_number,
    "insurer":       Policy.insurer,
    "status":        Policy.status,
    "file_name":     Policy.file_name,
    "policy_type_id": Policy.policy_type_id,
}


class PolicyQuery:
    # ── simple lookups (unchanged) ────────────────────────────────────────────

    def list_by_user_partner(self, user_id: str, partner_id: str) -> List[Policy]:
        with session_scope() as session:
            rows = session.query(Policy).filter(
                Policy.user_id == _uuid.UUID(str(user_id)),
                Policy.partner_id == _uuid.UUID(str(partner_id)),
                Policy.is_deleted == False,
            ).all()
            for r in rows:
                session.expunge(r)
            return rows

    def list_by_user(self, user_id: str) -> List[Policy]:
        with session_scope() as session:
            rows = session.query(Policy).filter(
                Policy.user_id == _uuid.UUID(str(user_id)), Policy.is_deleted == False
            ).all()
            for r in rows:
                session.expunge(r)
            return rows

    def get_by_id(self, policy_id: str, user_id: str = None) -> Optional[Policy]:
        with session_scope() as session:
            q = session.query(Policy).filter(
                Policy.id == _uuid.UUID(str(policy_id)), Policy.is_deleted == False
            )
            if user_id:
                q = q.filter(Policy.user_id == _uuid.UUID(str(user_id)))
            p = q.first()
            if p:
                session.expunge(p)
            return p

    # ── paginated list (POST /list pattern) ───────────────────────────────────

    def list_paginated_by_partner(
        self, partner_id: str, list_req
    ) -> Tuple[int, List[Policy]]:
        """For partner portal: all policies under this partner, with filters."""
        with session_scope() as session:
            q = (
                session.query(Policy)
                .join(PolicyType, Policy.policy_type_id == PolicyType.id)
                .filter(Policy.partner_id == partner_id, Policy.is_deleted == False)
            )
            q = apply_global_filter(q, list_req.global_filter, _GLOBAL_COLS())
            q = apply_field_filters(q, list_req.filters, _FILTER_MAP)
            q = apply_sort(q, Policy, list_req.sort_field, list_req.sort_order)
            total, rows = paginate(q, list_req.skip, list_req.limit)
            for r in rows:
                session.expunge(r)
            return total, rows

    def list_paginated_all(
        self, list_req, partner_id: str = None, user_id: str = None
    ) -> Tuple[int, List[Policy]]:
        """For admin portal: all policies, optional partner_id / user_id scoping."""
        with session_scope() as session:
            q = (
                session.query(Policy)
                .join(PolicyType, Policy.policy_type_id == PolicyType.id)
                .filter(Policy.is_deleted == False)
            )
            if partner_id:
                q = q.filter(Policy.partner_id == partner_id)
            if user_id:
                q = q.filter(Policy.user_id == user_id)
            q = apply_global_filter(q, list_req.global_filter, _GLOBAL_COLS())
            q = apply_field_filters(q, list_req.filters, _FILTER_MAP)
            q = apply_sort(q, Policy, list_req.sort_field, list_req.sort_order)
            total, rows = paginate(q, list_req.skip, list_req.limit)
            for r in rows:
                session.expunge(r)
            return total, rows

    def list_paginated_by_user_partner(
        self, user_id: str, partner_id: str, list_req
    ) -> Tuple[int, List[Policy]]:
        """For member portal: own policies under a specific partner."""
        with session_scope() as session:
            q = (
                session.query(Policy)
                .join(PolicyType, Policy.policy_type_id == PolicyType.id)
                .filter(
                    Policy.user_id == user_id,
                    Policy.partner_id == partner_id,
                    Policy.is_deleted == False,
                )
            )
            q = apply_global_filter(q, list_req.global_filter, _GLOBAL_COLS())
            q = apply_field_filters(q, list_req.filters, _FILTER_MAP)
            q = apply_sort(q, Policy, list_req.sort_field, list_req.sort_order)
            total, rows = paginate(q, list_req.skip, list_req.limit)
            for r in rows:
                session.expunge(r)
            return total, rows

    # ── write ops ─────────────────────────────────────────────────────────────

    def create(self, user_id: str, partner_id: str, policy_number: str,
               policy_id: str = None, **kwargs) -> Policy:
        with session_scope() as session:
            init = dict(user_id=user_id, partner_id=partner_id, policy_number=policy_number)
            if policy_id:
                init["id"] = policy_id
            init.update(kwargs)
            p = Policy(**init)
            session.add(p)
            session.flush()
            session.expunge(p)
            return p

    def update_extracted_fields(self, policy_id: str, fields: dict) -> None:
        with session_scope() as session:
            p = session.query(Policy).filter(
                Policy.id == _uuid.UUID(policy_id), Policy.is_deleted == False
            ).first()
            if p:
                p.extracted_fields = fields
                session.flush()

    def update_ai_result(self, policy_id: str, extracted_fields: dict,
                         ai_confidence: int, status: str) -> None:
        from datetime import date
        with session_scope() as session:
            p = session.query(Policy).filter(
                Policy.id == _uuid.UUID(policy_id), Policy.is_deleted == False
            ).first()
            if p:
                p.extracted_fields = extracted_fields
                p.ai_confidence = ai_confidence
                p.status = status
                if extracted_fields.get("start_date"):
                    try:
                        p.start_date = date.fromisoformat(str(extracted_fields["start_date"]))
                    except (ValueError, TypeError):
                        pass
                if extracted_fields.get("end_date"):
                    try:
                        p.end_date = date.fromisoformat(str(extracted_fields["end_date"]))
                    except (ValueError, TypeError):
                        pass
                if extracted_fields.get("policy_number"):
                    extracted_num = extracted_fields["policy_number"]
                    conflict = session.query(Policy).filter(
                        Policy.policy_number == extracted_num,
                        Policy.id != p.id,
                    ).first()
                    if not conflict:
                        p.policy_number = extracted_num
                    elif conflict.is_deleted:
                        # Soft-deleted policy is squatting the number — free it up
                        conflict.policy_number = f"DEL-{conflict.id}"
                        p.policy_number = extracted_num
                session.flush()

    def update_status(self, policy_id: str, status: str) -> bool:
        with session_scope() as session:
            p = session.query(Policy).filter(
                Policy.id == _uuid.UUID(policy_id), Policy.is_deleted == False
            ).first()
            if p:
                p.status = status
                session.flush()
                return True
            return False

    def soft_delete(self, policy_id: str, user_id: str) -> bool:
        with session_scope() as session:
            p = session.query(Policy).filter(
                Policy.id == policy_id, Policy.user_id == user_id
            ).first()
            if not p:
                return False
            p.is_deleted = True
            # Free up the policy number so re-uploads of the same doc don't conflict
            if p.policy_number:
                p.policy_number = f"DEL-{p.id}"
            return True

    # ── kept for backward compat (services still call these) ─────────────────

    def list_by_partner(self, partner_id: str, skip: int = 0, limit: int = 100) -> List[Policy]:
        with session_scope() as session:
            rows = session.query(Policy).filter(
                Policy.partner_id == partner_id, Policy.is_deleted == False,
            ).order_by(Policy.created_at.desc()).offset(skip).limit(limit).all()
            for r in rows:
                session.expunge(r)
            return rows

    def list_all(self, partner_id: str = None, skip: int = 0, limit: int = 100) -> List[Policy]:
        with session_scope() as session:
            q = session.query(Policy).filter(Policy.is_deleted == False)
            if partner_id:
                q = q.filter(Policy.partner_id == partner_id)
            rows = q.order_by(Policy.created_at.desc()).offset(skip).limit(limit).all()
            for r in rows:
                session.expunge(r)
            return rows
