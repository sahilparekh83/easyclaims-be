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


def notify_partner(partner_id: str, type: str, title: str,
                   body: str = None, ref_id: str = None, ref_type: str = None):
    """Send a notification to the user account of a partner by partner_id."""
    try:
        from ..db.queries.partner_query import PartnerQuery
        partner = PartnerQuery().get_by_id(partner_id)
        if not partner:
            return
        NotificationQuery().create(
            recipient_user_id=str(partner.user_id),
            type=type, title=title, body=body,
            ref_id=ref_id, ref_type=ref_type,
        )
    except Exception:
        logger.exception("Failed to send partner notification: %s", title)
