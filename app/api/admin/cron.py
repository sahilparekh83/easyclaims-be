from fastapi import APIRouter, Depends, Request
from ...schemas.base import ResponseModel
from ..users import _require_superadmin

admin_cron_router = APIRouter()


@admin_cron_router.post("/run-expiry-check", response_model=ResponseModel)
async def trigger_expiry_check(request: Request, _=Depends(_require_superadmin)):
    """Manually trigger the daily plan expiry check cron job."""
    from ...services.cron_service import run_expiry_check
    result = run_expiry_check()
    return ResponseModel.ok(data=result)
