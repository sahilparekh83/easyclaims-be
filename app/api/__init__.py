from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/health", tags=["Health"])
async def health():
    from ..configs.common import get_settings
    settings = get_settings()
    return {"status": "ok", "mode": "DEV" if settings.DEBUG else "PROD"}
