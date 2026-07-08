from fastapi import APIRouter
from .ai import admin_ai_router
from .plans import admin_plans_router
from .partners import admin_partners_router
from .members import admin_members_router
from .dashboard import admin_dashboard_router
from .policies import admin_policies_router
from .policy_types import admin_policy_types_router
from .partner_types import admin_partner_types_router
from .notifications import admin_notifications_router
from .email_templates import admin_email_templates_router
from .cron import admin_cron_router
from .settings import admin_settings_router
from .audit_logs import admin_audit_router
from .tickets import admin_tickets_router
from .finance import admin_finance_router

admin_router = APIRouter()
admin_router.include_router(admin_plans_router, prefix="/plans", tags=["Admin - Plans"])
admin_router.include_router(admin_partners_router, prefix="/partners", tags=["Admin - Partners"])
admin_router.include_router(admin_members_router, prefix="/members", tags=["Admin - Members"])
admin_router.include_router(admin_dashboard_router, prefix="/dashboard", tags=["Admin - Dashboard"])
admin_router.include_router(admin_policies_router, prefix="/policies", tags=["Admin - Policies"])
admin_router.include_router(admin_policy_types_router, prefix="/policy-types", tags=["Admin - Policy Types"])
admin_router.include_router(admin_partner_types_router, prefix="/partner-types", tags=["Admin - Partner Types"])
admin_router.include_router(admin_notifications_router, prefix="/notifications", tags=["Admin - Notifications"])
admin_router.include_router(admin_email_templates_router, prefix="/email-templates", tags=["Admin - Email Templates"])
admin_router.include_router(admin_cron_router, prefix="/cron", tags=["Admin - Cron"])
admin_router.include_router(admin_ai_router, prefix="/ai", tags=["Admin - AI"])
admin_router.include_router(admin_settings_router, prefix="/settings", tags=["Admin - Settings"])
admin_router.include_router(admin_audit_router, prefix="/audit-logs", tags=["Admin - Audit Logs"])
admin_router.include_router(admin_tickets_router, prefix="/tickets", tags=["Admin - Tickets"])
admin_router.include_router(admin_finance_router, prefix="/finance", tags=["Admin - Finance"])
