from fastapi import APIRouter
from .plans import admin_plans_router
from .partners import admin_partners_router
from .members import admin_members_router
from .dashboard import admin_dashboard_router

admin_router = APIRouter()
admin_router.include_router(admin_plans_router, prefix="/plans", tags=["Admin - Plans"])
admin_router.include_router(admin_partners_router, prefix="/partners", tags=["Admin - Partners"])
admin_router.include_router(admin_members_router, prefix="/members", tags=["Admin - Members"])
admin_router.include_router(admin_dashboard_router, prefix="/dashboard", tags=["Admin - Dashboard"])
