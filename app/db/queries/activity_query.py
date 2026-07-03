import uuid
from datetime import datetime, timezone
from typing import List, Optional
from ..session import session_scope
from ..models.activity import UserActivity, PolicyFamilyMember, PolicyNominee, Notification


def utcnow():
    return datetime.now(timezone.utc)


class ActivityQuery:

    def record_login(self, user_id: str) -> UserActivity:
        """Upsert user_activity on every successful login."""
        now = utcnow()
        with session_scope() as session:
            activity = session.query(UserActivity).filter(
                UserActivity.user_id == user_id
            ).first()
            if activity:
                activity.last_login_at = now
                activity.login_count = (activity.login_count or 0) + 1
                if not activity.has_logged_in:
                    activity.first_login_at = now
                    activity.has_logged_in = True
                session.flush()
                session.expunge(activity)
            else:
                activity = UserActivity(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    first_login_at=now,
                    last_login_at=now,
                    login_count=1,
                    has_logged_in=True,
                )
                session.add(activity)
                session.flush()
                session.expunge(activity)
        return activity

    def get_activity(self, user_id: str) -> Optional[UserActivity]:
        with session_scope() as session:
            a = session.query(UserActivity).filter(
                UserActivity.user_id == user_id
            ).first()
            if a:
                session.expunge(a)
            return a


class PolicyFamilyQuery:

    def link(self, policy_id: str, family_member_id: str) -> PolicyFamilyMember:
        """Link a family member to a policy. Raises ValueError if duplicate."""
        with session_scope() as session:
            existing = session.query(PolicyFamilyMember).filter(
                PolicyFamilyMember.policy_id == policy_id,
                PolicyFamilyMember.family_member_id == family_member_id,
            ).first()
            if existing:
                raise ValueError("Family member already linked to this policy")
            link = PolicyFamilyMember(
                id=uuid.uuid4(),
                policy_id=policy_id,
                family_member_id=family_member_id,
            )
            session.add(link)
            session.flush()
            session.expunge(link)
        return link

    def unlink(self, policy_id: str, family_member_id: str) -> bool:
        with session_scope() as session:
            rows = session.query(PolicyFamilyMember).filter(
                PolicyFamilyMember.policy_id == policy_id,
                PolicyFamilyMember.family_member_id == family_member_id,
            ).delete()
        return rows > 0

    def delete_by_policy(self, policy_id: str) -> int:
        with session_scope() as session:
            return session.query(PolicyFamilyMember).filter(
                PolicyFamilyMember.policy_id == policy_id,
            ).delete()

    def list_by_policy(self, policy_id: str) -> List[PolicyFamilyMember]:
        with session_scope() as session:
            rows = session.query(PolicyFamilyMember).filter(
                PolicyFamilyMember.policy_id == policy_id,
            ).all()
            for r in rows:
                session.expunge(r)
        return rows

    def list_by_family_member(self, family_member_id: str) -> List[PolicyFamilyMember]:
        with session_scope() as session:
            rows = session.query(PolicyFamilyMember).filter(
                PolicyFamilyMember.family_member_id == family_member_id,
            ).all()
            for r in rows:
                session.expunge(r)
        return rows


class PolicyNomineeQuery:

    def link(self, policy_id: str, nominee_id: str) -> PolicyNominee:
        """Link a nominee to a policy. Raises ValueError if duplicate."""
        with session_scope() as session:
            existing = session.query(PolicyNominee).filter(
                PolicyNominee.policy_id == policy_id,
                PolicyNominee.nominee_id == nominee_id,
            ).first()
            if existing:
                raise ValueError("Nominee already linked to this policy")
            link = PolicyNominee(
                id=uuid.uuid4(),
                policy_id=policy_id,
                nominee_id=nominee_id,
            )
            session.add(link)
            session.flush()
            session.expunge(link)
        return link

    def unlink(self, policy_id: str, nominee_id: str) -> bool:
        with session_scope() as session:
            rows = session.query(PolicyNominee).filter(
                PolicyNominee.policy_id == policy_id,
                PolicyNominee.nominee_id == nominee_id,
            ).delete()
        return rows > 0

    def delete_by_policy(self, policy_id: str) -> int:
        with session_scope() as session:
            return session.query(PolicyNominee).filter(
                PolicyNominee.policy_id == policy_id,
            ).delete()

    def list_by_policy(self, policy_id: str) -> List[PolicyNominee]:
        with session_scope() as session:
            rows = session.query(PolicyNominee).filter(
                PolicyNominee.policy_id == policy_id,
            ).all()
            for r in rows:
                session.expunge(r)
        return rows

    def list_by_nominee(self, nominee_id: str) -> List[PolicyNominee]:
        with session_scope() as session:
            rows = session.query(PolicyNominee).filter(
                PolicyNominee.nominee_id == nominee_id,
            ).all()
            for r in rows:
                session.expunge(r)
        return rows


class NotificationQuery:

    def create(self, recipient_user_id: str, type: str, title: str,
               body: str = None, ref_id: str = None, ref_type: str = None) -> Notification:
        with session_scope() as session:
            n = Notification(
                id=uuid.uuid4(),
                recipient_user_id=recipient_user_id,
                type=type,
                title=title,
                body=body,
                ref_id=ref_id,
                ref_type=ref_type,
                is_read=False,
            )
            session.add(n)
            session.flush()
            session.expunge(n)
        return n

    def list_for_user(self, user_id: str, unread_only: bool = False,
                      skip: int = 0, limit: int = 50) -> tuple:
        with session_scope() as session:
            q = session.query(Notification).filter(
                Notification.recipient_user_id == user_id
            )
            if unread_only:
                q = q.filter(Notification.is_read == False)
            total = q.count()
            rows = (q.order_by(Notification.is_read.asc(), Notification.created_at.desc())
                    .offset(skip).limit(limit).all())
            for r in rows:
                session.expunge(r)
        return total, rows

    def mark_read(self, notification_id: str, user_id: str) -> bool:
        with session_scope() as session:
            n = session.query(Notification).filter(
                Notification.id == notification_id,
                Notification.recipient_user_id == user_id,
            ).first()
            if not n:
                return False
            n.is_read = True
            session.flush()
        return True

    def mark_all_read(self, user_id: str) -> int:
        with session_scope() as session:
            count = session.query(Notification).filter(
                Notification.recipient_user_id == user_id,
                Notification.is_read == False,
            ).update({"is_read": True})
        return count

    def delete(self, notification_id: str, user_id: str) -> bool:
        with session_scope() as session:
            rows = session.query(Notification).filter(
                Notification.id == notification_id,
                Notification.recipient_user_id == user_id,
            ).delete()
        return rows > 0

    def unread_count(self, user_id: str) -> int:
        with session_scope() as session:
            return session.query(Notification).filter(
                Notification.recipient_user_id == user_id,
                Notification.is_read == False,
            ).count()

    def count_by_type(self, user_id: str, types: list) -> int:
        with session_scope() as session:
            return session.query(Notification).filter(
                Notification.recipient_user_id == user_id,
                Notification.is_read == False,
                Notification.type.in_(types),
            ).count()

    def mark_read_by_type(self, user_id: str, type: str) -> int:
        with session_scope() as session:
            count = session.query(Notification).filter(
                Notification.recipient_user_id == user_id,
                Notification.is_read == False,
                Notification.type == type,
            ).update({"is_read": True})
        return count
