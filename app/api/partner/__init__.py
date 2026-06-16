from fastapi import APIRouter
from .profile import partner_profile_router
from .plans import partner_plans_router
from .members import partner_members_router
from .dashboard import partner_dashboard_router

partner_router = APIRouter()
partner_router.include_router(partner_profile_router, prefix="/profile", tags=["Partner - Profile"])
partner_router.include_router(partner_plans_router, prefix="/plans", tags=["Partner - Plans"])
partner_router.include_router(partner_members_router, prefix="/members", tags=["Partner - Members"])
partner_router.include_router(partner_dashboard_router, prefix="/dashboard", tags=["Partner - Dashboard"])
