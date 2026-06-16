from typing import Optional, List
from ..models.partner import Partner
from ..session import session_scope


class PartnerQuery:
    def get_by_id(self, partner_id: str) -> Optional[Partner]:
        with session_scope() as session:
            p = session.query(Partner).filter(
                Partner.id == partner_id, Partner.is_deleted == False
            ).first()
            if p:
                session.expunge(p)
            return p

    def get_by_user_id(self, user_id: str) -> Optional[Partner]:
        with session_scope() as session:
            p = session.query(Partner).filter(
                Partner.user_id == user_id, Partner.is_deleted == False
            ).first()
            if p:
                session.expunge(p)
            return p

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Partner]:
        with session_scope() as session:
            partners = session.query(Partner).filter(
                Partner.is_deleted == False
            ).offset(skip).limit(limit).all()
            for p in partners:
                session.expunge(p)
            return partners

    def create(self, user_id: str, name: str, partner_type: str,
               city: str = None, api_key: str = None) -> Partner:
        with session_scope() as session:
            p = Partner(user_id=user_id, name=name, partner_type=partner_type,
                        city=city, api_key=api_key)
            session.add(p)
            session.flush()
            session.expunge(p)
            return p

    def update(self, partner_id: str, **kwargs) -> Optional[Partner]:
        with session_scope() as session:
            p = session.query(Partner).filter(Partner.id == partner_id).first()
            if not p:
                return None
            for k, v in kwargs.items():
                setattr(p, k, v)
            session.flush()
            session.expunge(p)
            return p

    def soft_delete(self, partner_id: str) -> bool:
        with session_scope() as session:
            p = session.query(Partner).filter(Partner.id == partner_id).first()
            if not p:
                return False
            p.is_deleted = True
            p.status = "Inactive"
            return True
