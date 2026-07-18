from typing import List
from fastapi import HTTPException
from ..db.queries.policy_type_query import PolicyTypeQuery
from ..db.models.policy_type import PolicyType
from ..schemas.policy_type import PolicyTypeCreate, PolicyTypeUpdate


class PolicyTypeService:
    def __init__(self):
        self.query = PolicyTypeQuery()

    def list_all(self, active_only: bool = False) -> List[PolicyType]:
        return self.query.list_all(active_only=active_only)

    def get(self, policy_type_id: str) -> PolicyType:
        pt = self.query.get_by_id(policy_type_id)
        if not pt:
            raise HTTPException(status_code=404, detail="Policy type not found")
        return pt

    def create(self, data: PolicyTypeCreate) -> PolicyType:
        if self.query.get_by_code(data.code):
            raise HTTPException(status_code=409, detail=f"Policy type code '{data.code}' already exists")
        try:
            return self.query.create(name=data.name, code=data.code, description=data.description)
        except Exception as exc:
            if "unique" in str(exc).lower() or "UniqueViolation" in str(type(exc).__name__):
                raise HTTPException(status_code=409, detail="Policy type name or code already exists")
            raise

    def update(self, policy_type_id: str, data: PolicyTypeUpdate) -> PolicyType:
        self.get(policy_type_id)
        updates = data.model_dump(exclude_none=True)
        pt = self.query.update(policy_type_id, **updates)
        return pt

    def toggle(self, policy_type_id: str, is_active: bool) -> PolicyType:
        self.get(policy_type_id)
        return self.query.toggle_active(policy_type_id, is_active)

    def linked_count(self, policy_type_id: str) -> int:
        return self.query.count_linked_policies(policy_type_id)

    def delete(self, policy_type_id: str) -> None:
        self.get(policy_type_id)
        count = self.linked_count(policy_type_id)
        if count > 0:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cannot delete: {count} polic{'y is' if count == 1 else 'ies are'} "
                    "linked to this policy type. Deactivate it instead."
                ),
            )
        self.query.delete(policy_type_id)

    @staticmethod
    def to_dict(pt: PolicyType, linked_count: int = None) -> dict:
        return {
            "id": str(pt.id),
            "name": pt.name,
            "code": pt.code,
            "description": pt.description,
            "is_active": pt.is_active,
            "created_at": pt.created_at.isoformat() if pt.created_at else None,
            "linked_count": linked_count,
            "can_delete": (linked_count == 0) if linked_count is not None else None,
        }
