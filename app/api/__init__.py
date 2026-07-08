from fastapi import APIRouter, Request
from .auth import auth_router
from .webhook import webhook_main_router
from .users import users_router
from .roles import roles_router
from .plans import plans_router
from .admin import admin_router
from .partner import partner_router
from .member import member_router
from ..schemas.base import ResponseModel
from ..services.policy_type_service import PolicyTypeService
from ..services.partner_type_service import PartnerTypeService

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(roles_router, prefix="/roles", tags=["Roles"])
api_router.include_router(plans_router, prefix="/plans", tags=["Plans"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
api_router.include_router(partner_router, prefix="/partner", tags=["Partner"])
api_router.include_router(member_router, prefix="/member", tags=["Member"])
api_router.include_router(webhook_main_router, prefix="/webhook", tags=["Webhook"])


@api_router.get("/policy-types", tags=["Policy Types"], response_model=ResponseModel)
async def list_policy_types(request: Request):
    svc = PolicyTypeService()
    return ResponseModel.ok(data=[svc.to_dict(pt) for pt in svc.list_all(active_only=True)])


@api_router.get("/partner-types", tags=["Partner Types"], response_model=ResponseModel)
async def list_partner_types(request: Request):
    svc = PartnerTypeService()
    return ResponseModel.ok(data=[svc.to_dict(pt) for pt in svc.list_all(active_only=True)])


@api_router.get("/health", tags=["Health"])
async def health():
    from ..configs.common import get_settings
    settings = get_settings()
    return {"status": "ok", "mode": "DEV" if settings.DEBUG else "PROD"}
