from fastapi import APIRouter
from .auth import auth_router
from .users import users_router
from .roles import roles_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(roles_router, prefix="/roles", tags=["Roles"])


@api_router.get("/health", tags=["Health"])
async def health():
    from ..configs.common import get_settings
    settings = get_settings()
    return {"status": "ok", "mode": "DEV" if settings.DEBUG else "PROD"}
