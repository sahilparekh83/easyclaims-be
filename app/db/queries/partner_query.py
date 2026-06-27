import uuid as _uuid
from typing import Optional, List, Tuple
from ..models.partner import Partner
from ..session import session_scope
from .list_helper import apply_global_filter, apply_field_filters, apply_sort, paginate

_GLOBAL_COLS = lambda: [Partner.name, Partner.partner_type, Partner.status, Partner.city]
_FILTER_MAP = {
    "name":         Partner.name,
    "partner_type": Partner.partner_type,
    "status":       Partner.status,
    "city":         Partner.city,
}


class PartnerQuery:
    def get_by_id(self, partner_id: str) -> Optional[Partner]:
        with session_scope() as session:
            p = session.query(Partner).filter(
                Partner.id == _uuid.UUID(str(partner_id)),
                Partner.is_deleted == False,
            ).first()
            if p:
                session.expunge(p)
            return p

    def get_by_user_id(self, user_id: str) -> Optional[Partner]:
        with session_scope() as session:
            p = session.query(Partner).filter(
                Partner.user_id == _uuid.UUID(str(user_id)),
                Partner.is_deleted == False,
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

    def list_paginated(self, list_req) -> Tuple[int, List[Partner]]:
        with session_scope() as session:
            q = session.query(Partner).filter(Partner.is_deleted == False)
            q = apply_global_filter(q, list_req.global_filter, _GLOBAL_COLS())
            q = apply_field_filters(q, list_req.filters, _FILTER_MAP)
            q = apply_sort(q, Partner, list_req.sort_field, list_req.sort_order)
            total, rows = paginate(q, list_req.skip, list_req.limit)
            for r in rows:
                session.expunge(r)
            return total, rows

    def create(self, user_id: str, name: str, partner_type: str,
               city: str = None, api_key: str = None,
               state: str = None, legal_company_name: str = None,
               trade_name: str = None, registered_address: str = None,
               pin_code: str = None, gstin: str = None, pan: str = None,
               authorized_signatory_name: str = None, designation: str = None,
               data_1: str = None, data_2: str = None, data_3: str = None) -> Partner:
        with session_scope() as session:
            p = Partner(
                user_id=user_id, name=name, partner_type=partner_type,
                city=city, api_key=api_key, state=state,
                legal_company_name=legal_company_name, trade_name=trade_name,
                registered_address=registered_address, pin_code=pin_code,
                gstin=gstin, pan=pan,
                authorized_signatory_name=authorized_signatory_name,
                designation=designation,
                data_1=data_1, data_2=data_2, data_3=data_3,
            )
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
