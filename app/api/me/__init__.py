from fastapi import APIRouter
from .partners import me_partners_router
from .plan import me_plan_router
from .profile import me_profile_router
from .family import me_family_router
from .nominees import me_nominees_router
from .consent import me_consent_router
from .policies import me_policies_router
from .dashboard import me_dashboard_router

me_router = APIRouter()
me_router.include_router(me_partners_router, prefix="/partners", tags=["Me - Partners"])
me_router.include_router(me_plan_router, prefix="/plan", tags=["Me - Plan"])
me_router.include_router(me_profile_router, prefix="/profile", tags=["Me - Profile"])
me_router.include_router(me_family_router, prefix="/family", tags=["Me - Family"])
me_router.include_router(me_nominees_router, prefix="/nominees", tags=["Me - Nominees"])
me_router.include_router(me_consent_router, prefix="/consent", tags=["Me - Consent"])
me_router.include_router(me_policies_router, prefix="/policies", tags=["Me - Policies"])
me_router.include_router(me_dashboard_router, prefix="/dashboard", tags=["Me - Dashboard"])
