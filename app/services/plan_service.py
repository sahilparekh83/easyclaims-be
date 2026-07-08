import re
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


def _generate_plan_code(name: str, query: PlanQuery) -> str:
    """Auto-generate a unique plan code from the plan name, e.g.
    'EbixCash Insurance Assistance Membership' -> 'EIAM-001'."""
    words = re.findall(r"[A-Za-z0-9]+", name)
    initials = "".join(w[0] for w in words if w).upper()[:6] or "PLAN"
    n = 1
    while True:
        code = f"{initials}-{n:03d}"
        if not query.get_by_code(code):
            return code
        n += 1


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
            "name": data.name, "plan_code": _generate_plan_code(data.name, self.query),
            "tagline": data.tagline, "info_text": data.info_text,
            "price": data.price, "cycle": data.cycle, "plan_type": data.plan_type,
            "status": data.status, "color": data.color, "popular": data.popular,
            "max_claim_value": data.max_claim_value,
            "fee_slabs": [s.model_dump() for s in data.fee_slabs],
            "basic_features_note": data.basic_features_note,
            "basic_features": data.basic_features,
            "advanced_features_note": data.advanced_features_note,
            "advanced_features": data.advanced_features,
            "co_powered_by_easyclaims": data.co_powered_by_easyclaims,
            **_benefits_to_db(data.benefits),
        }
        return self.query.create(**kwargs)

    def _count_members_and_partners(self, plan_id) -> tuple[int, int]:
        from ..db.session import session_scope
        from ..db.models.member import MemberEnrollment
        from ..db.models.partner import PartnerPlan
        import uuid as _uuid
        pid = _uuid.UUID(str(plan_id))
        with session_scope() as session:
            members = session.query(MemberEnrollment).filter(
                MemberEnrollment.plan_id == pid
            ).count()
            partners = session.query(PartnerPlan).filter(
                PartnerPlan.plan_id == str(pid)
            ).count()
        return members, partners

    def update(self, plan_id: str, data: PlanUpdate) -> MembershipPlan:
        plan = self.get_by_id(plan_id)
        kwargs = data.model_dump(exclude_none=True)

        if "status" in kwargs and kwargs["status"] != plan.status:
            new_status = kwargs["status"]
            # Active → Draft or Archived is blocked when the plan has members or partners linked
            if plan.status == "Active" and new_status in ("Draft", "Archived"):
                members, partners = self._count_members_and_partners(plan.id)
                if members > 0 or partners > 0:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Cannot change status to '{new_status}' — plan has {members} enrolled member(s) "
                               f"and {partners} linked partner(s). Unlink all first.",
                    )

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
        self.get_by_id(plan_id)
        members, partners = self._count_members_and_partners(plan_id)
        if members > 0 or partners > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete — plan has {members} enrolled member(s) and "
                       f"{partners} linked partner(s). Unlink all before deleting.",
            )
        self.query.hard_delete(plan_id)

    def link_partner(self, plan_id: str, partner_id: str) -> None:
        plan = self.get_by_id(plan_id)
        if plan.plan_type != "partner":
            raise HTTPException(status_code=409, detail="Only partner-type plans can be linked")
        self.query.link_partner(plan_id, partner_id)

    def unlink_partner(self, plan_id: str, partner_id: str) -> None:
        if not self.query.unlink_partner(plan_id, partner_id):
            raise HTTPException(status_code=404, detail="Link not found")
