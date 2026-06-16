from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ...services.plan_service import PlanService
from ..deps import _require_partner
from ..plans import _plan_to_dict

partner_plans_router = APIRouter()


@partner_plans_router.get("", response_model=ResponseModel)
async def list_partner_plans(request: Request, partner=Depends(_require_partner)):
    plans = PlanService().list_for_partner(str(partner.id))
    return ResponseModel.ok(data=[_plan_to_dict(p) for p in plans])
