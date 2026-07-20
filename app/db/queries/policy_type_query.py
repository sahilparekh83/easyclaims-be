from typing import List, Optional
from ..models.policy_type import PolicyType
from ..session import session_scope


class PolicyTypeQuery:
    def list_all(self, active_only: bool = False) -> List[PolicyType]:
        with session_scope() as session:
            q = session.query(PolicyType)
            if active_only:
                q = q.filter(PolicyType.is_active == True)
            rows = q.order_by(PolicyType.name).all()
            for r in rows:
                session.expunge(r)
            return rows

    def get_by_id(self, policy_type_id: str) -> Optional[PolicyType]:
        with session_scope() as session:
            row = session.query(PolicyType).filter(PolicyType.id == policy_type_id).first()
            if row:
                session.expunge(row)
            return row

    def get_by_code(self, code: str) -> Optional[PolicyType]:
        with session_scope() as session:
            row = session.query(PolicyType).filter(PolicyType.code == code.lower()).first()
            if row:
                session.expunge(row)
            return row

    def create(self, name: str, code: str, description: str = None) -> PolicyType:
        with session_scope() as session:
            row = PolicyType(name=name, code=code.lower(), description=description)
            session.add(row)
            session.flush()
            session.expunge(row)
            return row

    def update(self, policy_type_id: str, **kwargs) -> Optional[PolicyType]:
        with session_scope() as session:
            row = session.query(PolicyType).filter(PolicyType.id == policy_type_id).first()
            if not row:
                return None
            for k, v in kwargs.items():
                if hasattr(row, k) and v is not None:
                    setattr(row, k, v)
            session.flush()
            session.expunge(row)
            return row

    def toggle_active(self, policy_type_id: str, is_active: bool) -> Optional[PolicyType]:
        with session_scope() as session:
            row = session.query(PolicyType).filter(PolicyType.id == policy_type_id).first()
            if not row:
                return None
            row.is_active = is_active
            session.flush()
            session.expunge(row)
            return row

    def count_linked_policies(self, policy_type_id: str) -> int:
        from ..models.policy import Policy
        with session_scope() as session:
            return session.query(Policy).filter(Policy.policy_type_id == policy_type_id).count()

    def delete(self, policy_type_id: str) -> bool:
        with session_scope() as session:
            row = session.query(PolicyType).filter(PolicyType.id == policy_type_id).first()
            if not row:
                return False
            session.delete(row)
            return True
