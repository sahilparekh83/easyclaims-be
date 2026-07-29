import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from ..session import session_scope
from ..models.ticket import Ticket
from ...utils.code_generator import generate_unique_code

DUPLICATE_WINDOW_HOURS = 48


def utcnow():
    return datetime.now(timezone.utc)


class TicketQuery:

    def get_by_ticket_number(self, ticket_number: str) -> Optional[Ticket]:
        with session_scope() as session:
            t = session.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()
            if t:
                session.expunge(t)
            return t

    def create(self, channel: str, category: str, priority: str = "medium",
               summary: str = None, user_id: str = None, partner_id: str = None,
               ref_policy_id: str = None, is_duplicate: bool = False,
               duplicate_of_ticket_id: str = None) -> Ticket:
        with session_scope() as session:
            ticket_number = generate_unique_code("TCK", lambda code: bool(self.get_by_ticket_number(code)))
            t = Ticket(
                id=uuid.uuid4(),
                ticket_number=ticket_number,
                user_id=user_id,
                partner_id=partner_id,
                channel=channel,
                category=category,
                priority=priority,
                summary=summary,
                ref_policy_id=ref_policy_id,
                is_duplicate=is_duplicate,
                duplicate_of_ticket_id=duplicate_of_ticket_id,
            )
            session.add(t)
            session.flush()
            session.expunge(t)
            return t

    def find_recent_duplicate(self, user_id: str, category: str,
                              window_hours: int = DUPLICATE_WINDOW_HOURS) -> Optional[Ticket]:
        """Most recent open/in_progress ticket for this member+category within the window —
        used to flag a new incoming ticket as a likely duplicate."""
        if not user_id:
            return None
        since = utcnow() - timedelta(hours=window_hours)
        with session_scope() as session:
            t = session.query(Ticket).filter(
                Ticket.user_id == user_id,
                Ticket.category == category,
                Ticket.is_duplicate == False,
                Ticket.status.in_(("open", "in_progress")),
                Ticket.created_at >= since,
            ).order_by(Ticket.created_at.desc()).first()
            if t:
                session.expunge(t)
            return t

    def count_open(self, partner_id: str = None) -> int:
        with session_scope() as session:
            q = session.query(Ticket).filter(Ticket.status.in_(("open", "in_progress")))
            if partner_id:
                q = q.filter(Ticket.partner_id == partner_id)
            return q.count()

    def count_by_category(self, category: str, partner_id: str = None) -> int:
        with session_scope() as session:
            q = session.query(Ticket).filter(Ticket.category == category)
            if partner_id:
                q = q.filter(Ticket.partner_id == partner_id)
            return q.count()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Ticket]:
        with session_scope() as session:
            rows = (session.query(Ticket)
                    .order_by(Ticket.created_at.desc())
                    .offset(skip).limit(limit).all())
            for r in rows:
                session.expunge(r)
            return rows

    def list_by_user(self, user_id: str, skip: int = 0, limit: int = 20) -> List[Ticket]:
        with session_scope() as session:
            rows = (session.query(Ticket)
                    .filter(Ticket.user_id == user_id)
                    .order_by(Ticket.created_at.desc())
                    .offset(skip).limit(limit).all())
            for r in rows:
                session.expunge(r)
            return rows

    def update_status(self, ticket_id: str, status: str) -> bool:
        with session_scope() as session:
            t = session.query(Ticket).filter(Ticket.id == ticket_id).first()
            if not t:
                return False
            t.status = status
            session.flush()
            return True
