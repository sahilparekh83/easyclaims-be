from typing import List, Optional
from ..models.partner_type import PartnerType
from ..session import session_scope


class PartnerTypeQuery:
    def list_all(self, active_only: bool = False) -> List[PartnerType]:
        with session_scope() as session:
            q = session.query(PartnerType)
            if active_only:
                q = q.filter(PartnerType.is_active == True)
            rows = q.order_by(PartnerType.name).all()
            for r in rows:
                session.expunge(r)
            return rows

    def get_by_id(self, partner_type_id: str) -> Optional[PartnerType]:
        with session_scope() as session:
            row = session.query(PartnerType).filter(PartnerType.id == partner_type_id).first()
            if row:
                session.expunge(row)
            return row

    def get_by_code(self, code: str) -> Optional[PartnerType]:
        with session_scope() as session:
            row = session.query(PartnerType).filter(PartnerType.code == code.lower()).first()
            if row:
                session.expunge(row)
            return row

    def get_by_name_or_code(self, value: str, active_only: bool = True) -> Optional[PartnerType]:
        """Case-insensitive lookup by name or code — used to resolve free-text
        partner_type input (CRUD forms, bulk upload) to a managed PartnerType row."""
        if not value:
            return None
        needle_code = value.strip().lower().replace(" ", "_")
        needle_name = value.strip().lower()
        with session_scope() as session:
            q = session.query(PartnerType)
            if active_only:
                q = q.filter(PartnerType.is_active == True)
            rows = q.all()
            match = None
            for r in rows:
                if r.code == needle_code or r.name.strip().lower() == needle_name:
                    match = r
                    break
            if match:
                session.expunge(match)
            return match

    def create(self, name: str, code: str, description: str = None) -> PartnerType:
        with session_scope() as session:
            row = PartnerType(name=name, code=code.lower(), description=description)
            session.add(row)
            session.flush()
            session.expunge(row)
            return row

    def update(self, partner_type_id: str, **kwargs) -> Optional[PartnerType]:
        with session_scope() as session:
            row = session.query(PartnerType).filter(PartnerType.id == partner_type_id).first()
            if not row:
                return None
            for k, v in kwargs.items():
                if hasattr(row, k) and v is not None:
                    setattr(row, k, v)
            session.flush()
            session.expunge(row)
            return row

    def toggle_active(self, partner_type_id: str, is_active: bool) -> Optional[PartnerType]:
        with session_scope() as session:
            row = session.query(PartnerType).filter(PartnerType.id == partner_type_id).first()
            if not row:
                return None
            row.is_active = is_active
            session.flush()
            session.expunge(row)
            return row
