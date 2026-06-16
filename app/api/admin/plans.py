from uuid import UUID
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from ...schemas.base import ResponseModel
from ...schemas.plan import PlanCreate, PlanUpdate
from ...services.plan_service import PlanService
from ..users import _require_superadmin
from ..plans import _plan_to_dict

admin_plans_router = APIRouter()


class LinkPartnerBody(BaseModel):
    partner_id: str


@admin_plans_router.get("", response_model=ResponseModel)
async def list_plans(request: Request, skip: int = 0, limit: int = 100,
                     _=Depends(_require_superadmin)):
    return ResponseModel.ok(data=[_plan_to_dict(p) for p in PlanService().list_all(skip=skip, limit=limit)])


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
    return ResponseModel.ok(data={"partner_ids": partner_ids})
