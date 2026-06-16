from fastapi import APIRouter
from .auth import auth_router
from .users import users_router
from .roles import roles_router
from .plans import plans_router
from .admin import admin_router
from .partner import partner_router
from .me import me_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(roles_router, prefix="/roles", tags=["Roles"])
api_router.include_router(plans_router, prefix="/plans", tags=["Plans"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
api_router.include_router(partner_router, prefix="/partner", tags=["Partner"])
api_router.include_router(me_router, prefix="/me", tags=["Me"])


@api_router.get("/health", tags=["Health"])
async def health():
    from ..configs.common import get_settings
    settings = get_settings()
    return {"status": "ok", "mode": "DEV" if settings.DEBUG else "PROD"}
