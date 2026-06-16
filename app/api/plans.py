from uuid import UUID
from fastapi import APIRouter, Depends, Request
from ..schemas.base import ResponseModel
from ..services.plan_service import PlanService
from .users import _require_authenticated

plans_router = APIRouter()


def _plan_to_dict(plan) -> dict:
    return {
        "id": str(plan.id),
        "name": plan.name,
        "tagline": plan.tagline,
        "info_text": plan.info_text,
        "price": plan.price,
        "cycle": plan.cycle,
        "plan_type": plan.plan_type,
        "status": plan.status,
        "color": plan.color,
        "popular": plan.popular,
        "benefits": {
            "family": plan.benefit_family,
            "slots": plan.benefit_slots,
            "claim": plan.benefit_claim,
            "aiqa": plan.benefit_aiqa,
            "aicalls": plan.benefit_aicalls,
            "voice": plan.benefit_voice,
            "vault": plan.benefit_vault,
            "rm": plan.benefit_rm,
            "concierge": plan.benefit_concierge,
            "teleconsult_sessions": plan.benefit_teleconsult_sessions,
            "hospital_cash": plan.benefit_hospital_cash,
            "wellness_sessions": plan.benefit_wellness_sessions,
            "emergency_assist": plan.benefit_emergency_assist,
            "legal_assist": plan.benefit_legal_assist,
        },
    }


@plans_router.get("", response_model=ResponseModel)
async def list_active_plans(request: Request, _=Depends(_require_authenticated)):
    return ResponseModel.ok(data=[_plan_to_dict(p) for p in PlanService().list_active_global()])


@plans_router.get("/{plan_id}", response_model=ResponseModel)
async def get_plan(plan_id: UUID, request: Request, _=Depends(_require_authenticated)):
    return ResponseModel.ok(data=_plan_to_dict(PlanService().get_by_id(str(plan_id))))
