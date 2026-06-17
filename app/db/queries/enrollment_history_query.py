import uuid as _uuid
from typing import List
from ..models.enrollment_history import EnrollmentHistory
from ..session import session_scope


class EnrollmentHistoryQuery:
    def create(
        self,
        enrollment_id: str,
        user_id: str,
        partner_id: str,
        to_plan_id: str,
        action: str,
        from_plan_id: str = None,
        changed_by: str = "system",
        note: str = None,
    ) -> EnrollmentHistory:
        with session_scope() as session:
            h = EnrollmentHistory(
                enrollment_id=_uuid.UUID(enrollment_id),
                user_id=_uuid.UUID(user_id),
                partner_id=_uuid.UUID(partner_id),
                from_plan_id=_uuid.UUID(from_plan_id) if from_plan_id else None,
                to_plan_id=_uuid.UUID(to_plan_id),
                action=action,
                changed_by=changed_by,
                note=note,
            )
            session.add(h)
            session.flush()
            session.expunge(h)
            return h

    def list_for_enrollment(self, enrollment_id: str) -> List[EnrollmentHistory]:
        with session_scope() as session:
            rows = (
                session.query(EnrollmentHistory)
                .filter(EnrollmentHistory.enrollment_id == _uuid.UUID(enrollment_id))
                .order_by(EnrollmentHistory.changed_at.desc())
                .all()
            )
            for r in rows:
                session.expunge(r)
            return rows

    def list_for_user(self, user_id: str) -> List[EnrollmentHistory]:
        with session_scope() as session:
            rows = (
                session.query(EnrollmentHistory)
                .filter(EnrollmentHistory.user_id == _uuid.UUID(user_id))
                .order_by(EnrollmentHistory.changed_at.desc())
                .all()
            )
            for r in rows:
                session.expunge(r)
            return rows
