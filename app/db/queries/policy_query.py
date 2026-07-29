import uuid as _uuid
from typing import Optional, List, Tuple
from sqlalchemy import or_
from ..models.policy import Policy
from ..models.policy_type import PolicyType
from ..models.user import User
from ..models.member import FamilyMember
from ..models.activity import PolicyFamilyMember
from ..session import session_scope
from .list_helper import (
    apply_global_filter, apply_field_filters, apply_sort, paginate
)


# columns searchable via global_filter — includes User.name (portal account holder),
# Policy.policy_holder_name (AI-extracted insured name — distinct field, both legitimate
# search targets), and a narrowly-scoped JSONB clause (full-blob JSONB search is
# intentionally descoped — only this one hot key is searched, avoiding a full-scan).
_GLOBAL_COLS = lambda: [
    Policy.policy_number, Policy.insurer, Policy.status, Policy.file_name, PolicyType.name,
    User.name, Policy.policy_holder_name,
    Policy.extracted_fields["validation_reason"].astext,
]


def _family_member_name_filter(query, f):
    """EXISTS-style filter (not a plain join) so a policy linked to multiple
    family members doesn't get duplicated across paginated rows."""
    subq = (
        query.session.query(PolicyFamilyMember.policy_id)
        .join(FamilyMember, FamilyMember.id == PolicyFamilyMember.family_member_id)
        .filter(FamilyMember.name.ilike(f"%{f.value}%"))
    )
    return query.filter(Policy.id.in_(subq))


# columns/callables addressable by filters[].field
_FILTER_MAP = {
    "policy_number": Policy.policy_number,
    "insurer":       Policy.insurer,
    "status":        Policy.status,
    "file_name":     Policy.file_name,
    "policy_type_id": Policy.policy_type_id,
    "policy_type":   PolicyType.name,  # FE sends the type's display name, not its id
    "member_name":   User.name,
    "policy_holder_name": Policy.policy_holder_name,
    "start_date":    Policy.start_date,
    "end_date":      Policy.end_date,
    "family_member_name": _family_member_name_filter,
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

    def get_by_policy_number(self, policy_number: str) -> Optional[Policy]:
        with session_scope() as session:
            p = session.query(Policy).filter(Policy.policy_number == policy_number).first()
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
                .join(User, Policy.user_id == User.id)
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
                .join(User, Policy.user_id == User.id)
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

    def list_paginated_by_user(
        self, user_id: str, list_req
    ) -> Tuple[int, List[Policy]]:
        """For member portal: own policies across every partner enrolled with."""
        with session_scope() as session:
            q = (
                session.query(Policy)
                .join(PolicyType, Policy.policy_type_id == PolicyType.id)
                .join(User, Policy.user_id == User.id)
                .filter(
                    Policy.user_id == user_id,
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

    def list_paginated_by_user_partner(
        self, user_id: str, partner_id: str, list_req
    ) -> Tuple[int, List[Policy]]:
        """For member portal: own policies under a specific partner."""
        with session_scope() as session:
            q = (
                session.query(Policy)
                .join(PolicyType, Policy.policy_type_id == PolicyType.id)
                .join(User, Policy.user_id == User.id)
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
                         ai_confidence: int, status: str,
                         policy_type_id: Optional[str] = None,
                         policy_holder_name: Optional[str] = None) -> None:
        from datetime import date
        with session_scope() as session:
            p = session.query(Policy).filter(
                Policy.id == _uuid.UUID(policy_id), Policy.is_deleted == False
            ).first()
            if p:
                p.extracted_fields = extracted_fields
                p.ai_confidence = ai_confidence
                p.status = status
                if policy_type_id:
                    p.policy_type_id = _uuid.UUID(str(policy_type_id))
                if policy_holder_name:
                    p.policy_holder_name = policy_holder_name
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
                if extracted_fields.get("insurer_name") and not p.insurer:
                    p.insurer = extracted_fields["insurer_name"]
                if extracted_fields.get("sum_insured") and not p.sum_insured:
                    try:
                        p.sum_insured = int(float(extracted_fields["sum_insured"]))
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

    def update_vehicle_fields(self, policy_id: str, vehicle_number: Optional[str] = None,
                              vehicle_type: Optional[str] = None,
                              vehicle_owner_family_member_id: Optional[str] = None) -> None:
        with session_scope() as session:
            p = session.query(Policy).filter(
                Policy.id == _uuid.UUID(policy_id), Policy.is_deleted == False
            ).first()
            if p:
                if vehicle_number is not None:
                    p.vehicle_number = vehicle_number
                if vehicle_type is not None:
                    p.vehicle_type = vehicle_type
                if vehicle_owner_family_member_id is not None:
                    p.vehicle_owner_family_member_id = _uuid.UUID(vehicle_owner_family_member_id)
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

    def soft_delete_admin(self, policy_id: str) -> bool:
        with session_scope() as session:
            p = session.query(Policy).filter(Policy.id == policy_id).first()
            if not p:
                return False
            p.is_deleted = True
            if p.policy_number:
                p.policy_number = f"DEL-{p.id}"
            return True

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

    def find_renewal_candidate(self, user_id: str, policy_type_id: str,
                               exclude_policy_id: str) -> Optional[Policy]:
        """Return the most recent non-deleted policy for this user+type (excluding the new one)."""
        with session_scope() as session:
            p = (
                session.query(Policy)
                .filter(
                    Policy.user_id == _uuid.UUID(str(user_id)),
                    Policy.policy_type_id == _uuid.UUID(str(policy_type_id)),
                    Policy.id != _uuid.UUID(str(exclude_policy_id)),
                    Policy.is_deleted == False,
                    Policy.status != "renewed",
                )
                .order_by(Policy.end_date.desc().nullslast(), Policy.created_at.desc())
                .first()
            )
            if p:
                session.expunge(p)
            return p

    def link_renewal(self, new_policy_id: str, previous_policy_id: str,
                     confidence: str, mark_previous_renewed: bool) -> None:
        with session_scope() as session:
            new = session.query(Policy).filter(Policy.id == _uuid.UUID(new_policy_id)).first()
            if new:
                new.previous_policy_id = _uuid.UUID(previous_policy_id)
                new.renewal_confidence = confidence
                if confidence == "low":
                    new.status = "renewal_pending"
            if mark_previous_renewed:
                old = session.query(Policy).filter(Policy.id == _uuid.UUID(previous_policy_id)).first()
                if old:
                    old.status = "renewed"
            session.flush()

    def confirm_renewal(self, policy_id: str) -> bool:
        """Admin confirms a low-confidence renewal — mark old policy as renewed."""
        with session_scope() as session:
            new = session.query(Policy).filter(
                Policy.id == _uuid.UUID(policy_id), Policy.is_deleted == False
            ).first()
            if not new or not new.previous_policy_id:
                return False
            new.renewal_confidence = "high"
            new.status = "active"
            old = session.query(Policy).filter(Policy.id == new.previous_policy_id).first()
            if old:
                old.status = "renewed"
            session.flush()
            return True

    def dismiss_renewal(self, policy_id: str) -> bool:
        """Admin dismisses renewal detection — treat as a fresh policy."""
        with session_scope() as session:
            p = session.query(Policy).filter(
                Policy.id == _uuid.UUID(policy_id), Policy.is_deleted == False
            ).first()
            if not p:
                return False
            p.previous_policy_id = None
            p.renewal_confidence = None
            if p.status == "renewal_pending":
                p.status = "active"
            session.flush()
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
