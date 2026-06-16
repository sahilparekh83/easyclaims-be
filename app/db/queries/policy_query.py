from typing import Optional, List
from ..models.policy import Policy
from ..session import session_scope


class PolicyQuery:
    def list_by_user_partner(self, user_id: str, partner_id: str) -> List[Policy]:
        with session_scope() as session:
            rows = session.query(Policy).filter(
                Policy.user_id == user_id,
                Policy.partner_id == partner_id,
                Policy.is_deleted == False,
            ).all()
            for r in rows:
                session.expunge(r)
            return rows

    def list_by_user(self, user_id: str) -> List[Policy]:
        with session_scope() as session:
            rows = session.query(Policy).filter(
                Policy.user_id == user_id, Policy.is_deleted == False
            ).all()
            for r in rows:
                session.expunge(r)
            return rows

    def get_by_id(self, policy_id: str, user_id: str = None) -> Optional[Policy]:
        with session_scope() as session:
            q = session.query(Policy).filter(
                Policy.id == policy_id, Policy.is_deleted == False
            )
            if user_id:
                q = q.filter(Policy.user_id == user_id)
            p = q.first()
            if p:
                session.expunge(p)
            return p

    def create(self, user_id: str, partner_id: str, policy_number: str, **kwargs) -> Policy:
        with session_scope() as session:
            p = Policy(user_id=user_id, partner_id=partner_id,
                       policy_number=policy_number, **kwargs)
            session.add(p)
            session.flush()
            session.expunge(p)
            return p

    def soft_delete(self, policy_id: str, user_id: str) -> bool:
        with session_scope() as session:
            p = session.query(Policy).filter(
                Policy.id == policy_id, Policy.user_id == user_id
            ).first()
            if not p:
                return False
            p.is_deleted = True
            return True
