import uuid as _uuid
from datetime import date, datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import and_
from ..models.member import MemberProfile, MemberEnrollment, FamilyMember, Nominee, DpdpConsent, MemberChangeRequest
from ..models.user import User
from ..session import session_scope
from .list_helper import apply_global_filter, apply_field_filters, apply_sort, paginate
from ...constants import UserType

_MEMBER_GLOBAL_COLS = lambda: [User.name, User.email, User.mobile_no]
_MEMBER_FILTER_MAP = {
    "name":      User.name,
    "email":     User.email,
    "mobile_no": User.mobile_no,
    "is_active": User.is_active,
}


class MemberQuery:
    # ── Paginated member list (POST /list pattern) ────────────────────────────

    def list_members_paginated(
        self, list_req, partner_id: str = None
    ) -> Tuple[int, List[User]]:
        """
        Return (total, [User]) applying list_req filters.
        If partner_id is given, only return users enrolled under that partner.
        """
        with session_scope() as session:
            q = session.query(User).filter(
                User.user_type == UserType.CUSTOMER,
                User.is_deleted == False,
            )
            if partner_id:
                q = q.join(
                    MemberEnrollment,
                    and_(
                        User.id == MemberEnrollment.user_id,
                        MemberEnrollment.partner_id == _uuid.UUID(str(partner_id)),
                    ),
                )
            q = apply_global_filter(q, list_req.global_filter, _MEMBER_GLOBAL_COLS())
            q = apply_field_filters(q, list_req.filters, _MEMBER_FILTER_MAP)
            q = apply_sort(q, User, list_req.sort_field, list_req.sort_order)
            total, rows = paginate(q, list_req.skip, list_req.limit)
            for r in rows:
                session.expunge(r)
            return total, rows

    # ── Enrollments ──────────────────────────────────────────────────────────
    def get_enrollment(self, user_id: str, partner_id: str) -> Optional[MemberEnrollment]:
        with session_scope() as session:
            e = session.query(MemberEnrollment).filter(
                MemberEnrollment.user_id == _uuid.UUID(str(user_id)),
                MemberEnrollment.partner_id == _uuid.UUID(str(partner_id)),
            ).first()
            if e:
                session.expunge(e)
            return e

    def count_by_partner(self, partner_id: str) -> int:
        with session_scope() as session:
            return session.query(MemberEnrollment).filter(
                MemberEnrollment.partner_id == _uuid.UUID(str(partner_id)),
            ).count()

    def list_enrollments(self, user_id: str) -> List[MemberEnrollment]:
        with session_scope() as session:
            rows = session.query(MemberEnrollment).filter(
                MemberEnrollment.user_id == user_id
            ).order_by(MemberEnrollment.created_at).all()
            for r in rows:
                session.expunge(r)
            return rows

    def list_by_partner(self, partner_id: str, skip: int = 0, limit: int = 100) -> List[MemberEnrollment]:
        with session_scope() as session:
            rows = session.query(MemberEnrollment).filter(
                MemberEnrollment.partner_id == partner_id
            ).offset(skip).limit(limit).all()
            for r in rows:
                session.expunge(r)
            return rows

    def create_enrollment(self, user_id: str, partner_id: str, plan_id: str) -> MemberEnrollment:
        today = date.today()
        end = today.replace(year=today.year + 1)
        with session_scope() as session:
            existing = session.query(MemberEnrollment).filter(
                MemberEnrollment.user_id == _uuid.UUID(str(user_id)),
                MemberEnrollment.partner_id == _uuid.UUID(str(partner_id)),
            ).first()
            if existing:
                existing.plan_id = plan_id
                existing.start_date = today
                existing.end_date = end
                existing.status = "Active"
                session.flush()
                session.expunge(existing)
                return existing
            e = MemberEnrollment(
                user_id=user_id, partner_id=partner_id, plan_id=plan_id,
                start_date=today, end_date=end,
            )
            session.add(e)
            session.flush()
            session.expunge(e)
            return e

    def update_enrollment(self, user_id: str, partner_id: str, **kwargs) -> Optional[MemberEnrollment]:
        with session_scope() as session:
            e = session.query(MemberEnrollment).filter(
                MemberEnrollment.user_id == _uuid.UUID(str(user_id)),
                MemberEnrollment.partner_id == _uuid.UUID(str(partner_id)),
            ).first()
            if not e:
                return None
            for k, v in kwargs.items():
                setattr(e, k, v)
            session.flush()
            session.expunge(e)
            return e

    def list_enrollments_by_plan_partner(self, plan_id: str, partner_id: str) -> List[MemberEnrollment]:
        with session_scope() as session:
            rows = session.query(MemberEnrollment).filter(
                MemberEnrollment.plan_id == _uuid.UUID(str(plan_id)),
                MemberEnrollment.partner_id == _uuid.UUID(str(partner_id)),
            ).all()
            for r in rows:
                session.expunge(r)
            return rows

    def get_first_active_enrollment(self, user_id: str) -> Optional[MemberEnrollment]:
        with session_scope() as session:
            e = session.query(MemberEnrollment).filter(
                MemberEnrollment.user_id == _uuid.UUID(str(user_id)),
                MemberEnrollment.status == "Active",
            ).order_by(MemberEnrollment.created_at).first()
            if e:
                session.expunge(e)
            return e

    # ── Profile ──────────────────────────────────────────────────────────────
    def get_profile(self, user_id: str) -> Optional[MemberProfile]:
        with session_scope() as session:
            p = session.query(MemberProfile).filter(MemberProfile.user_id == user_id).first()
            if p:
                session.expunge(p)
            return p

    def upsert_profile(self, user_id: str, **kwargs) -> MemberProfile:
        with session_scope() as session:
            p = session.query(MemberProfile).filter(MemberProfile.user_id == user_id).first()
            if p:
                for k, v in kwargs.items():
                    setattr(p, k, v)
            else:
                p = MemberProfile(user_id=user_id, **kwargs)
                session.add(p)
            session.flush()
            session.expunge(p)
            return p

    # ── Family ───────────────────────────────────────────────────────────────
    def list_family(self, user_id: str) -> List[FamilyMember]:
        with session_scope() as session:
            rows = session.query(FamilyMember).filter(FamilyMember.user_id == user_id).all()
            for r in rows:
                session.expunge(r)
            return rows

    def get_family_member(self, member_id: str, user_id: str = None) -> Optional[FamilyMember]:
        with session_scope() as session:
            q = session.query(FamilyMember).filter(FamilyMember.id == member_id)
            if user_id:
                q = q.filter(FamilyMember.user_id == user_id)
            m = q.first()
            if m:
                session.expunge(m)
            return m

    def create_family_member(self, user_id: str, **kwargs) -> FamilyMember:
        with session_scope() as session:
            m = FamilyMember(user_id=user_id, **kwargs)
            session.add(m)
            session.flush()
            session.expunge(m)
            return m

    def update_family_member(self, member_id: str, user_id: str, **kwargs) -> Optional[FamilyMember]:
        with session_scope() as session:
            m = session.query(FamilyMember).filter(
                FamilyMember.id == member_id, FamilyMember.user_id == user_id
            ).first()
            if not m:
                return None
            for k, v in kwargs.items():
                setattr(m, k, v)
            session.flush()
            session.expunge(m)
            return m

    def delete_family_member(self, member_id: str, user_id: str) -> bool:
        with session_scope() as session:
            m = session.query(FamilyMember).filter(
                FamilyMember.id == member_id, FamilyMember.user_id == user_id
            ).first()
            if not m:
                return False
            session.delete(m)
            return True

    # ── Nominees ─────────────────────────────────────────────────────────────
    def list_nominees(self, user_id: str) -> List[Nominee]:
        with session_scope() as session:
            rows = session.query(Nominee).filter(Nominee.user_id == user_id).all()
            for r in rows:
                session.expunge(r)
            return rows

    def get_nominee(self, nominee_id: str, user_id: str) -> Optional[Nominee]:
        with session_scope() as session:
            n = session.query(Nominee).filter(
                Nominee.id == nominee_id, Nominee.user_id == user_id
            ).first()
            if n:
                session.expunge(n)
            return n

    def total_share(self, user_id: str, exclude_id: str = None) -> int:
        with session_scope() as session:
            q = session.query(Nominee).filter(Nominee.user_id == user_id)
            if exclude_id:
                q = q.filter(Nominee.id != exclude_id)
            return sum(n.share_percent for n in q.all())

    def create_nominee(self, user_id: str, **kwargs) -> Nominee:
        with session_scope() as session:
            n = Nominee(user_id=user_id, **kwargs)
            session.add(n)
            session.flush()
            session.expunge(n)
            return n

    def update_nominee(self, nominee_id: str, user_id: str, **kwargs) -> Optional[Nominee]:
        with session_scope() as session:
            n = session.query(Nominee).filter(
                Nominee.id == nominee_id, Nominee.user_id == user_id
            ).first()
            if not n:
                return None
            for k, v in kwargs.items():
                setattr(n, k, v)
            session.flush()
            session.expunge(n)
            return n

    def delete_nominee(self, nominee_id: str, user_id: str) -> bool:
        with session_scope() as session:
            n = session.query(Nominee).filter(
                Nominee.id == nominee_id, Nominee.user_id == user_id
            ).first()
            if not n:
                return False
            session.delete(n)
            return True

    # ── Consent ──────────────────────────────────────────────────────────────
    def list_consents(self, user_id: str) -> list:
        with session_scope() as session:
            items = session.query(DpdpConsent).filter(
                DpdpConsent.user_id == user_id
            ).order_by(DpdpConsent.created_at.desc()).all()
            for item in items:
                session.expunge(item)
            return items

    def get_latest_consent(self, user_id: str) -> Optional[DpdpConsent]:
        with session_scope() as session:
            c = session.query(DpdpConsent).filter(
                DpdpConsent.user_id == user_id
            ).order_by(DpdpConsent.created_at.desc()).first()
            if c:
                session.expunge(c)
            return c

    def create_consent(self, user_id: str, consented_at, version: str, source: str) -> DpdpConsent:
        with session_scope() as session:
            c = DpdpConsent(user_id=user_id, consented_at=consented_at,
                            version=version, source=source)
            session.add(c)
            session.flush()
            session.expunge(c)
            return c

    # ── Change Requests ──────────────────────────────────────────────────────
    def create_change_request(self, user_id: str, requested_fields: dict, reason: str = None) -> MemberChangeRequest:
        with session_scope() as session:
            cr = MemberChangeRequest(
                user_id=user_id,
                requested_fields=requested_fields,
                reason=reason,
            )
            session.add(cr)
            session.flush()
            session.expunge(cr)
            return cr

    def get_change_request(self, request_id: str):
        with session_scope() as session:
            cr = session.query(MemberChangeRequest).filter(MemberChangeRequest.id == request_id).first()
            if cr:
                session.expunge(cr)
            return cr

    def list_change_requests(self, user_id=None, status=None, skip=0, limit=50):
        with session_scope() as session:
            q = session.query(MemberChangeRequest)
            if user_id:
                q = q.filter(MemberChangeRequest.user_id == user_id)
            if status:
                q = q.filter(MemberChangeRequest.status == status)
            total = q.count()
            rows = q.order_by(MemberChangeRequest.created_at.desc()).offset(skip).limit(limit).all()
            for r in rows:
                session.expunge(r)
            return total, rows

    def update_change_request(self, request_id: str, status: str,
                               reviewed_by: str = None, admin_note: str = None):
        with session_scope() as session:
            cr = session.query(MemberChangeRequest).filter(MemberChangeRequest.id == request_id).first()
            if not cr:
                return None
            cr.status = status
            cr.reviewed_by = reviewed_by
            cr.reviewed_at = datetime.now(timezone.utc)
            if admin_note is not None:
                cr.admin_note = admin_note
            session.flush()
            session.expunge(cr)
            return cr
