from fastapi import APIRouter
from .ai import member_ai_router
from .partners import member_partners_router
from .change_requests import member_change_requests_router
from .plan import member_plan_router
from .profile import member_profile_router
from .family import member_family_router
from .nominees import member_nominees_router
from .consent import member_consent_router
from .policies import member_policies_router
from .dashboard import member_dashboard_router
from .notifications import member_notifications_router

member_router = APIRouter()
member_router.include_router(member_partners_router, prefix="/partners", tags=["Member - Partners"])
member_router.include_router(member_plan_router, prefix="/plan", tags=["Member - Plan"])
member_router.include_router(member_profile_router, prefix="/profile", tags=["Member - Profile"])
member_router.include_router(member_family_router, prefix="/family", tags=["Member - Family"])
member_router.include_router(member_nominees_router, prefix="/nominees", tags=["Member - Nominees"])
member_router.include_router(member_consent_router, prefix="/consent", tags=["Member - Consent"])
member_router.include_router(member_policies_router, prefix="/policies", tags=["Member - Policies"])
member_router.include_router(member_dashboard_router, prefix="/dashboard", tags=["Member - Dashboard"])
member_router.include_router(member_notifications_router, prefix="/notifications", tags=["Member - Notifications"])
member_router.include_router(member_ai_router, prefix="/ai", tags=["Member - AI"])
member_router.include_router(member_change_requests_router, prefix="/change-requests", tags=["Member - Change Requests"])
