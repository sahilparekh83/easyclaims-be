from datetime import date
from typing import Optional, List
from ..models.member import MemberProfile, MemberEnrollment, FamilyMember, Nominee, DpdpConsent
from ..session import session_scope


class MemberQuery:
    # ── Enrollments ──────────────────────────────────────────────────────────
    def get_enrollment(self, user_id: str, partner_id: str) -> Optional[MemberEnrollment]:
        with session_scope() as session:
            e = session.query(MemberEnrollment).filter(
                MemberEnrollment.user_id == user_id,
                MemberEnrollment.partner_id == partner_id,
            ).first()
            if e:
                session.expunge(e)
            return e

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
                MemberEnrollment.user_id == user_id,
                MemberEnrollment.partner_id == partner_id,
            ).first()
            if existing:
                existing.plan_id = plan_id
                existing.start_date = today
                existing.end_date = end
                existing.status = "active"
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
                MemberEnrollment.user_id == user_id,
                MemberEnrollment.partner_id == partner_id,
            ).first()
            if not e:
                return None
            for k, v in kwargs.items():
                setattr(e, k, v)
            session.flush()
            session.expunge(e)
            return e

    def get_first_active_enrollment(self, user_id: str) -> Optional[MemberEnrollment]:
        with session_scope() as session:
            e = session.query(MemberEnrollment).filter(
                MemberEnrollment.user_id == user_id,
                MemberEnrollment.status == "active",
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

    def get_family_member(self, member_id: str, user_id: str) -> Optional[FamilyMember]:
        with session_scope() as session:
            m = session.query(FamilyMember).filter(
                FamilyMember.id == member_id, FamilyMember.user_id == user_id
            ).first()
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
