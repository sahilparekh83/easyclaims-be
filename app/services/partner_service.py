import uuid
from typing import List
from fastapi import HTTPException
from ..db.queries.partner_query import PartnerQuery
from ..db.queries.user_query import UserQuery
from ..db.models.partner import Partner
from ..schemas.partner import PartnerCreate, PartnerUpdate
from ..constants import UserType


class PartnerService:
    def __init__(self):
        self.query = PartnerQuery()
        self.user_query = UserQuery()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Partner]:
        return self.query.list_all(skip=skip, limit=limit)

    def get_by_id(self, partner_id: str) -> Partner:
        p = self.query.get_by_id(partner_id)
        if not p:
            raise HTTPException(status_code=404, detail="Partner not found")
        return p

    def get_by_user_id(self, user_id: str) -> Partner:
        p = self.query.get_by_user_id(user_id)
        if not p:
            raise HTTPException(status_code=404, detail="Partner record not found for this user")
        return p

    def create(self, data: PartnerCreate) -> Partner:
        existing = self.user_query.get_user_by_email(str(data.email))
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
        user = self.user_query.create_user(
            email=str(data.email), name=data.name,
            user_type=UserType.PARTNER, mobile_no=data.mobile_no,
        )
        api_key = str(uuid.uuid4()).replace("-", "")
        return self.query.create(
            user_id=str(user.id), name=data.name,
            partner_type=data.partner_type, city=data.city, api_key=api_key,
        )

    def update(self, partner_id: str, data: PartnerUpdate) -> Partner:
        self.get_by_id(partner_id)
        kwargs = data.model_dump(exclude_none=True)
        p = self.query.update(partner_id, **kwargs)
        if not p:
            raise HTTPException(status_code=404, detail="Partner not found")
        return p

    def delete(self, partner_id: str) -> None:
        self.get_by_id(partner_id)
        self.query.soft_delete(partner_id)

    def regenerate_api_key(self, partner_id: str) -> Partner:
        self.get_by_id(partner_id)
        new_key = str(uuid.uuid4()).replace("-", "")
        return self.query.update(partner_id, api_key=new_key)
