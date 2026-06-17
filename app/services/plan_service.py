from typing import List
from fastapi import HTTPException
from ..db.queries.plan_query import PlanQuery
from ..db.models.plan import MembershipPlan
from ..schemas.plan import PlanCreate, PlanUpdate


def _benefits_to_db(b) -> dict:
    return {
        "benefit_family": b.family, "benefit_slots": b.slots,
        "benefit_claim": b.claim, "benefit_aiqa": b.aiqa,
        "benefit_aicalls": b.aicalls, "benefit_voice": b.voice,
        "benefit_vault": b.vault, "benefit_rm": b.rm,
        "benefit_concierge": b.concierge,
        "benefit_teleconsult_sessions": b.teleconsult_sessions,
        "benefit_hospital_cash": b.hospital_cash,
        "benefit_wellness_sessions": b.wellness_sessions,
        "benefit_emergency_assist": b.emergency_assist,
        "benefit_legal_assist": b.legal_assist,
    }


class PlanService:
    def __init__(self):
        self.query = PlanQuery()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[MembershipPlan]:
        return self.query.list_all(skip=skip, limit=limit)

    def list_active_global(self) -> List[MembershipPlan]:
        return self.query.list_active_global()

    def list_for_partner(self, partner_id: str, active_only: bool = False) -> List[MembershipPlan]:
        return self.query.list_for_partner(partner_id, active_only=active_only)

    def get_by_id(self, plan_id: str) -> MembershipPlan:
        p = self.query.get_by_id(plan_id)
        if not p:
            raise HTTPException(status_code=404, detail="Plan not found")
        return p

    def create(self, data: PlanCreate) -> MembershipPlan:
        if self.query.get_by_name(data.name):
            raise HTTPException(status_code=409, detail="Plan name already exists")
        kwargs = {
            "name": data.name, "tagline": data.tagline, "info_text": data.info_text,
            "price": data.price, "cycle": data.cycle, "plan_type": data.plan_type,
            "status": data.status, "color": data.color, "popular": data.popular,
            **_benefits_to_db(data.benefits),
        }
        return self.query.create(**kwargs)

    def update(self, plan_id: str, data: PlanUpdate) -> MembershipPlan:
        self.get_by_id(plan_id)
        kwargs = data.model_dump(exclude_none=True)
        if "benefits" in kwargs:
            benefits_obj = data.benefits
            kwargs.pop("benefits")
            kwargs.update(_benefits_to_db(benefits_obj))
        p = self.query.update(plan_id, **kwargs)
        if not p:
            raise HTTPException(status_code=404, detail="Plan not found")
        return p

    def activate(self, plan_id: str) -> MembershipPlan:
        self.get_by_id(plan_id)
        p = self.query.update(plan_id, status="Active")
        return p

    def archive(self, plan_id: str) -> MembershipPlan:
        self.get_by_id(plan_id)
        p = self.query.update(plan_id, status="Archived")
        return p

    def delete(self, plan_id: str) -> None:
        plan = self.get_by_id(plan_id)
        if plan.status != "Draft":
            raise HTTPException(status_code=409, detail="Only Draft plans can be deleted")
        self.query.soft_delete(plan_id)

    def link_partner(self, plan_id: str, partner_id: str) -> None:
        plan = self.get_by_id(plan_id)
        if plan.plan_type != "partner":
            raise HTTPException(status_code=409, detail="Only partner-type plans can be linked")
        self.query.link_partner(plan_id, partner_id)

    def unlink_partner(self, plan_id: str, partner_id: str) -> None:
        if not self.query.unlink_partner(plan_id, partner_id):
            raise HTTPException(status_code=404, detail="Link not found")
