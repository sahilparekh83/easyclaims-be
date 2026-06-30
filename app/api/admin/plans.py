from uuid import UUID
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from ...schemas.base import ResponseModel
from ...schemas.plan import PlanCreate, PlanUpdate
from ...services.plan_service import PlanService
from ...db.queries.partner_query import PartnerQuery
from ...db.queries.member_query import MemberQuery
from ...db.queries.user_query import UserQuery
from ..users import _require_superadmin
from ..plans import _plan_to_dict

admin_plans_router = APIRouter()


class LinkPartnerBody(BaseModel):
    partner_id: str


@admin_plans_router.get("", response_model=ResponseModel)
async def list_plans(request: Request, skip: int = 0, limit: int = 100,
                     _=Depends(_require_superadmin)):
    from ...db.session import session_scope
    from ...db.models.member import MemberEnrollment
    from sqlalchemy import func

    from ...db.models.partner import PartnerPlan

    plans = PlanService().list_all(skip=skip, limit=limit)

    with session_scope() as session:
        member_counts = dict(
            session.query(MemberEnrollment.plan_id, func.count(MemberEnrollment.id))
            .group_by(MemberEnrollment.plan_id)
            .all()
        )
        partner_counts = dict(
            session.query(PartnerPlan.plan_id, func.count(PartnerPlan.partner_id))
            .group_by(PartnerPlan.plan_id)
            .all()
        )

    result = []
    for p in plans:
        d = _plan_to_dict(p)
        d["member_count"] = member_counts.get(p.id, 0)
        d["partner_count"] = partner_counts.get(str(p.id), 0)
        result.append(d)

    return ResponseModel.ok(data=result)


@admin_plans_router.post("", response_model=ResponseModel, status_code=201)
async def create_plan(body: PlanCreate, request: Request, _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_plan_to_dict(PlanService().create(body)))


@admin_plans_router.get("/{plan_id}", response_model=ResponseModel)
async def get_plan(plan_id: UUID, request: Request, _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_plan_to_dict(PlanService().get_by_id(str(plan_id))))


@admin_plans_router.patch("/{plan_id}", response_model=ResponseModel)
async def update_plan(plan_id: UUID, body: PlanUpdate, request: Request,
                      _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_plan_to_dict(PlanService().update(str(plan_id), body)))


@admin_plans_router.post("/{plan_id}/activate", response_model=ResponseModel)
async def activate_plan(plan_id: UUID, request: Request, _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_plan_to_dict(PlanService().activate(str(plan_id))))


@admin_plans_router.post("/{plan_id}/archive", response_model=ResponseModel)
async def archive_plan(plan_id: UUID, request: Request, _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=_plan_to_dict(PlanService().archive(str(plan_id))))


@admin_plans_router.delete("/{plan_id}", response_model=ResponseModel)
async def delete_plan(plan_id: UUID, request: Request, _=Depends(_require_superadmin)):
    PlanService().delete(str(plan_id))
    return ResponseModel.ok(data={"message": "Plan deleted"})


@admin_plans_router.post("/{plan_id}/partners", response_model=ResponseModel, status_code=201)
async def link_partner(plan_id: UUID, body: LinkPartnerBody, request: Request,
                       _=Depends(_require_superadmin)):
    PlanService().link_partner(str(plan_id), body.partner_id)
    return ResponseModel.ok(data={"message": "Partner linked to plan"})


@admin_plans_router.delete("/{plan_id}/partners/{partner_id}", response_model=ResponseModel)
async def unlink_partner(plan_id: UUID, partner_id: UUID, request: Request,
                         _=Depends(_require_superadmin)):
    PlanService().unlink_partner(str(plan_id), str(partner_id))
    return ResponseModel.ok(data={"message": "Partner unlinked from plan"})


@admin_plans_router.get("/{plan_id}/partners", response_model=ResponseModel)
async def list_linked_partners(plan_id: UUID, request: Request, _=Depends(_require_superadmin)):
    partner_ids = PlanService().query.list_linked_partners(str(plan_id))
    pq = PartnerQuery()
    mq = MemberQuery()
    partners = []
    for pid in partner_ids:
        partner = pq.get_by_id(pid)
        if partner:
            # Count members enrolled on this plan under this partner
            enrollments = mq.list_enrollments_by_plan_partner(str(plan_id), pid)
            partners.append({
                "id": str(partner.id),
                "name": partner.name,
                "partner_type": partner.partner_type,
                "status": partner.status,
                "member_count": len(enrollments),
            })
    return ResponseModel.ok(data=partners)


@admin_plans_router.get("/{plan_id}/members", response_model=ResponseModel)
async def list_members_on_plan(
    plan_id: UUID, partner_id: str, request: Request, _=Depends(_require_superadmin)
):
    """Return members enrolled on this plan under a specific partner."""
    mq = MemberQuery()
    uq = UserQuery()
    enrollments = mq.list_enrollments_by_plan_partner(str(plan_id), partner_id)
    members = []
    for e in enrollments:
        user = uq.get_user_by_id(str(e.user_id))
        if user:
            members.append({"id": str(user.id), "name": user.name, "email": user.email})
    return ResponseModel.ok(data=members)
