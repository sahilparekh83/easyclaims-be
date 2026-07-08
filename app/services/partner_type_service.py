from typing import List
from fastapi import HTTPException
from ..db.queries.partner_type_query import PartnerTypeQuery
from ..db.models.partner_type import PartnerType
from ..schemas.partner_type import PartnerTypeCreate, PartnerTypeUpdate


class PartnerTypeService:
    def __init__(self):
        self.query = PartnerTypeQuery()

    def list_all(self, active_only: bool = False) -> List[PartnerType]:
        return self.query.list_all(active_only=active_only)

    def get(self, partner_type_id: str) -> PartnerType:
        pt = self.query.get_by_id(partner_type_id)
        if not pt:
            raise HTTPException(status_code=404, detail="Partner type not found")
        return pt

    def resolve(self, value: str) -> PartnerType:
        """Resolve free-text partner type (name or code, any case) to a managed row."""
        pt = self.query.get_by_name_or_code(value)
        if not pt:
            active = self.query.list_all(active_only=True)
            allowed = ", ".join(sorted(p.name for p in active))
            raise HTTPException(
                status_code=422,
                detail=f"Invalid partner type: '{value}'. Must be one of: {allowed}",
            )
        return pt

    def create(self, data: PartnerTypeCreate) -> PartnerType:
        if self.query.get_by_code(data.code):
            raise HTTPException(status_code=409, detail=f"Partner type code '{data.code}' already exists")
        try:
            return self.query.create(name=data.name, code=data.code, description=data.description)
        except Exception as exc:
            if "unique" in str(exc).lower() or "UniqueViolation" in str(type(exc).__name__):
                raise HTTPException(status_code=409, detail="Partner type name or code already exists")
            raise

    def update(self, partner_type_id: str, data: PartnerTypeUpdate) -> PartnerType:
        self.get(partner_type_id)
        updates = data.model_dump(exclude_none=True)
        pt = self.query.update(partner_type_id, **updates)
        return pt

    def toggle(self, partner_type_id: str, is_active: bool) -> PartnerType:
        self.get(partner_type_id)
        return self.query.toggle_active(partner_type_id, is_active)

    @staticmethod
    def to_dict(pt: PartnerType) -> dict:
        return {
            "id": str(pt.id),
            "name": pt.name,
            "code": pt.code,
            "description": pt.description,
            "is_active": pt.is_active,
            "created_at": pt.created_at.isoformat() if pt.created_at else None,
        }
