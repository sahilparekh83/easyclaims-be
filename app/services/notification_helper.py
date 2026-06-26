import logging
from ..db.queries.activity_query import NotificationQuery
from ..db.session import session_scope
from ..db.models.user import User
from ..constants import UserType

logger = logging.getLogger("easyclaims")


def notify_all_admins(type: str, title: str, body: str, ref_id: str, ref_type: str):
    try:
        with session_scope() as session:
            admins = session.query(User).filter(
                User.user_type == UserType.SUPERADMIN,
                User.is_active == True,
                User.is_deleted == False,
            ).all()
            for a in admins:
                session.expunge(a)
        nq = NotificationQuery()
        for admin in admins:
            nq.create(
                recipient_user_id=str(admin.id),
                type=type, title=title, body=body,
                ref_id=ref_id, ref_type=ref_type,
            )
    except Exception:
        logger.exception("Failed to send admin notification: %s", title)
