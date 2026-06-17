import uuid as _uuid
from typing import Optional, List
from ..models.plan import MembershipPlan
from ..models.partner import PartnerPlan
from ..session import session_scope


class PlanQuery:
    def get_by_id(self, plan_id: str) -> Optional[MembershipPlan]:
        with session_scope() as session:
            p = session.query(MembershipPlan).filter(
                MembershipPlan.id == _uuid.UUID(str(plan_id)),
                MembershipPlan.is_deleted == False,
            ).first()
            if p:
                session.expunge(p)
            return p

    def get_by_name(self, name: str) -> Optional[MembershipPlan]:
        with session_scope() as session:
            p = session.query(MembershipPlan).filter(
                MembershipPlan.name == name, MembershipPlan.is_deleted == False
            ).first()
            if p:
                session.expunge(p)
            return p

    def list_all(self, skip: int = 0, limit: int = 100) -> List[MembershipPlan]:
        with session_scope() as session:
            plans = session.query(MembershipPlan).filter(
                MembershipPlan.is_deleted == False
            ).offset(skip).limit(limit).all()
            for p in plans:
                session.expunge(p)
            return plans

    def list_active_global(self) -> List[MembershipPlan]:
        with session_scope() as session:
            plans = session.query(MembershipPlan).filter(
                MembershipPlan.status == "Active",
                MembershipPlan.plan_type == "global",
                MembershipPlan.is_deleted == False,
            ).all()
            for p in plans:
                session.expunge(p)
            return plans

    def list_for_partner(self, partner_id: str, active_only: bool = False) -> List[MembershipPlan]:
        """Returns global active plans + partner-type plans explicitly linked to this partner.

        Linked partner plans are shown regardless of Draft/Active status — the admin
        linking act is sufficient authorization. Pass active_only=True to restrict to
        Active plans only (e.g. for member-facing enrollment selection).
        """
        with session_scope() as session:
            global_plans = session.query(MembershipPlan).filter(
                MembershipPlan.status == "Active",
                MembershipPlan.plan_type == "global",
                MembershipPlan.is_deleted == False,
            ).all()
            linked_ids = [
                row.plan_id for row in
                session.query(PartnerPlan).filter(
                    PartnerPlan.partner_id == _uuid.UUID(str(partner_id))
                ).all()
            ]
            partner_plans = []
            if linked_ids:
                q = session.query(MembershipPlan).filter(
                    MembershipPlan.id.in_(linked_ids),
                    MembershipPlan.is_deleted == False,
                )
                if active_only:
                    q = q.filter(MembershipPlan.status == "Active")
                partner_plans = q.all()
            all_plans = global_plans + partner_plans
            for p in all_plans:
                session.expunge(p)
            return all_plans

    def create(self, **kwargs) -> MembershipPlan:
        with session_scope() as session:
            p = MembershipPlan(**kwargs)
            session.add(p)
            session.flush()
            session.expunge(p)
            return p

    def update(self, plan_id: str, **kwargs) -> Optional[MembershipPlan]:
        with session_scope() as session:
            p = session.query(MembershipPlan).filter(
                MembershipPlan.id == _uuid.UUID(str(plan_id)),
                MembershipPlan.is_deleted == False,
            ).first()
            if not p:
                return None
            for k, v in kwargs.items():
                setattr(p, k, v)
            session.flush()
            session.expunge(p)
            return p

    def soft_delete(self, plan_id: str) -> bool:
        with session_scope() as session:
            p = session.query(MembershipPlan).filter(
                MembershipPlan.id == _uuid.UUID(str(plan_id)),
                MembershipPlan.is_deleted == False,
            ).first()
            if not p:
                return False
            p.is_deleted = True
            return True

    def link_partner(self, plan_id: str, partner_id: str) -> bool:
        with session_scope() as session:
            exists = session.query(PartnerPlan).filter_by(
                plan_id=plan_id, partner_id=partner_id
            ).first()
            if exists:
                return False
            session.add(PartnerPlan(plan_id=plan_id, partner_id=partner_id))
            return True

    def unlink_partner(self, plan_id: str, partner_id: str) -> bool:
        with session_scope() as session:
            row = session.query(PartnerPlan).filter_by(
                plan_id=plan_id, partner_id=partner_id
            ).first()
            if not row:
                return False
            session.delete(row)
            return True

    def list_linked_partners(self, plan_id: str) -> List[str]:
        with session_scope() as session:
            rows = session.query(PartnerPlan).filter(PartnerPlan.plan_id == plan_id).all()
            return [str(r.partner_id) for r in rows]
